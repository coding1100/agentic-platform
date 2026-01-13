from typing import List, Any
import warnings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from app.core.config import settings
from app.models.agent import Agent
from app.models.message import Message

# Suppress specific warnings from langchain/google libraries
warnings.filterwarnings('ignore', message='.*Unrecognized FinishReason enum value.*')
warnings.filterwarnings('ignore', message='.*Unrecognized role.*')
warnings.filterwarnings('ignore', message='.*Gemini produced an empty response.*')


class LangchainAgentService:
  """Simplified LangChain wrapper around Gemini - uses simple chain for all agents."""

  def __init__(self) -> None:
    if not settings.GEMINI_API_KEY:
      raise ValueError("GEMINI_API_KEY must be set in environment variables")
    self._api_key = settings.GEMINI_API_KEY

  def _build_llm(self, agent: Agent) -> ChatGoogleGenerativeAI:
    """Build the ChatGoogleGenerativeAI LLM instance."""
    return ChatGoogleGenerativeAI(
      model=agent.model,
      temperature=agent.temperature,
      google_api_key=self._api_key,
    )

  def _build_chain(self, agent: Agent) -> Any:
    """Build a simple chain for all agents."""
    llm = self._build_llm(agent)
    system_instructions = agent.system_prompt or ""

    # Simple prompt with chat history support
    prompt = ChatPromptTemplate.from_messages(
      [
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
      ]
    )
    
    # Add system instructions to first message if available
    from langchain_core.runnables import RunnableLambda
    
    def add_system_context(inputs: dict) -> dict:
      """Add system instructions to the input if this is the first message."""
      user_input = inputs.get("input", "")
      chat_history = inputs.get("chat_history", [])
      
      # If no history and we have system instructions, prepend them to input
      if not chat_history and system_instructions:
        enhanced_input = f"{system_instructions}\n\n{user_input}"
        return {"input": enhanced_input, "chat_history": []}
      
      return {"input": user_input, "chat_history": chat_history}
    
    chain = RunnableLambda(add_system_context) | prompt | llm
    return chain

  def _history_to_messages(self, history: List[Message], latest_input: str = None) -> List[Any]:
    """Convert database Message objects to LangChain message objects.
    
    Merges consecutive messages from the same role (Gemini requirement).
    If latest_input is provided, it's merged with the last user message if present.
    Filters out invalid messages (empty content or invalid roles).
    """
    # Limit history to last 8 messages for performance
    recent_history = history[-8:] if len(history) > 8 else history
    
    messages: List[Any] = []
    
    # Process history messages - filter out invalid ones
    for m in recent_history:
      # Skip messages with empty or invalid content
      if not m.content or not m.content.strip():
        continue
      
      # Validate role
      try:
        current_role = m.role.value if hasattr(m.role, 'value') else str(m.role)
        if not current_role or current_role not in ['user', 'assistant', 'system']:
          continue
      except (AttributeError, ValueError):
        # Skip messages with invalid roles
        continue
      
      # Skip system messages (they're handled separately)
      if current_role == "system":
        continue
      
      # Add new message or merge with last if same role
      if messages and messages[-1].__class__.__name__ == ("HumanMessage" if current_role == "user" else "AIMessage"):
        # Merge with last message of same type
        messages[-1].content += f"\n\n{m.content}"
      else:
        # Add new message
        if current_role == "user":
          messages.append(HumanMessage(content=m.content.strip()))
        elif current_role == "assistant":
          messages.append(AIMessage(content=m.content.strip()))
    
    # If latest_input is provided, merge with last user message or add as new
    if latest_input and latest_input.strip():
      if messages and isinstance(messages[-1], HumanMessage):
        # Merge with last user message
        messages[-1].content += f"\n\n{latest_input.strip()}"
      else:
        # Add as new user message
        messages.append(HumanMessage(content=latest_input.strip()))
    
    return messages

  def generate_response(
    self,
    agent: Agent,
    history: List[Message],
    latest_input: str,
  ) -> str:
    """
    Simplified LangChain agent - uses simple chain for all agents.
    Merges history properly to avoid consecutive same-role messages.
    
    For quiz requests, intercepts and generates quiz directly in a single call.
    """
    # Check if this is a quiz request - intercept and generate directly
    latest_lower = latest_input.lower() if latest_input else ""
    is_quiz_request = (
      "quiz" in latest_lower or 
      "generate" in latest_lower and ("question" in latest_lower or "mcq" in latest_lower) or
      "multiple choice" in latest_lower
    )
    
    # If it's a quiz request for prebuilt agents, generate directly
    if is_quiz_request and agent.is_prebuilt:
      from app.tools.prebuilt_agents import PREBUILT_AGENT_SLUGS
      if agent.slug in [PREBUILT_AGENT_SLUGS["personal_tutor"], 
                        PREBUILT_AGENT_SLUGS["course_creation_agent"],
                        PREBUILT_AGENT_SLUGS["language_practice_agent"]]:
        # Extract quiz parameters from the request
        import re
        topic_match = re.search(r'(?:about|on|for)\s+([^,\.\?]+?)(?:\s+with|\s+at|\s+of|$)', latest_input, re.IGNORECASE)
        topic = topic_match.group(1).strip() if topic_match else "general knowledge"
        
        difficulty_match = re.search(r'(easy|medium|hard|beginner|intermediate|advanced)', latest_input, re.IGNORECASE)
        difficulty = difficulty_match.group(1).lower() if difficulty_match else "medium"
        if difficulty in ["beginner"]:
          difficulty = "easy"
        elif difficulty in ["intermediate"]:
          difficulty = "medium"
        elif difficulty in ["advanced"]:
          difficulty = "hard"
        
        num_match = re.search(r'(\d+)\s*(?:questions?|mcqs?)', latest_input, re.IGNORECASE)
        num_questions = int(num_match.group(1)) if num_match else 5
        
        # Generate quiz directly using the tool (single API call)
        from app.tools.prebuilt_agents import _generate_quiz
        try:
          quiz_output = _generate_quiz(topic=topic, difficulty=difficulty, num_questions=num_questions)
          # Keep answers in the response - they're needed for validation
          # Answers will be hidden in the UI but available for validation
          return quiz_output
        except Exception as e:
          # Fallback to normal generation if tool fails
          print(f"Quiz generation tool failed, falling back to normal generation: {str(e)}")
    
    # Build messages with latest_input merged properly
    chat_history = self._history_to_messages(history, latest_input)
    
    # Use simple chain for all agents
    chain = self._build_chain(agent)
    
    try:
      # Extract the latest input from merged messages
      if chat_history and isinstance(chat_history[-1], HumanMessage):
        current_input = chat_history[-1].content
        # Remove it from history for the chain
        history_for_chain = chat_history[:-1]
      else:
        current_input = latest_input
        history_for_chain = chat_history
      
      result = chain.invoke(
        {
          "input": current_input,
          "chat_history": history_for_chain,
        }
      )
      output = result.content if hasattr(result, 'content') else str(result)
      
      # Clean quiz output if present - only remove preamble, keep answers for validation
      if "**Question 1:**" in output or "Question 1:" in output:
        quiz_start = output.find("**Question 1:**")
        if quiz_start == -1:
          quiz_start = output.find("Question 1:")
        if quiz_start > 0:
          output = output[quiz_start:].strip()
      
      return output
      
    except AttributeError as e:
      # Handle finish_reason AttributeError (unrecognized enum value from Gemini)
      error_str = str(e).lower()
      if "'int' object has no attribute 'name'" in str(e) or "finish_reason" in error_str:
        print(f"Warning: Unrecognized finish_reason from Gemini, attempting fallback...")
        # Try using the LLM directly without the chain to bypass the finish_reason processing
        try:
          llm = self._build_llm(agent)
          # Build a simple prompt from history and current input
          prompt_parts = []
          for msg in history_for_chain:
            if isinstance(msg, HumanMessage):
              prompt_parts.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
              prompt_parts.append(f"Assistant: {msg.content}")
          
          prompt_parts.append(f"User: {current_input}")
          prompt_parts.append("Assistant:")
          
          full_prompt = "\n".join(prompt_parts)
          if agent.system_prompt:
            full_prompt = f"{agent.system_prompt}\n\n{full_prompt}"
          
          # Use invoke directly on LLM
          result = llm.invoke(full_prompt)
          output = result.content if hasattr(result, 'content') else str(result)
          
          # Clean quiz output if present
          if "**Question 1:**" in output or "Question 1:" in output:
            quiz_start = output.find("**Question 1:**")
            if quiz_start == -1:
              quiz_start = output.find("Question 1:")
            if quiz_start > 0:
              output = output[quiz_start:].strip()
          
          return output
        except Exception as fallback_error:
          print(f"Fallback also failed: {str(fallback_error)}")
          # Final fallback: Use raw Google Generative AI SDK to bypass LangChain entirely
          try:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            
            # Build conversation history in Gemini format
            conversation_parts = []
            
            # Add system prompt to first message if available
            system_context = agent.system_prompt or ""
            
            # Convert history to Gemini format
            for msg in history_for_chain:
              if isinstance(msg, HumanMessage):
                conversation_parts.append({"role": "user", "parts": [msg.content]})
              elif isinstance(msg, AIMessage):
                conversation_parts.append({"role": "model", "parts": [msg.content]})
            
            # Add current input
            conversation_parts.append({"role": "user", "parts": [current_input]})
            
            # Initialize model
            model_instance = genai.GenerativeModel(
              model_name=agent.model,
              generation_config={
                "temperature": agent.temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
              }
            )
            
            # Prepend system context to first user message if exists
            if system_context.strip() and conversation_parts and conversation_parts[0]["role"] == "user":
              conversation_parts[0]["parts"][0] = f"{system_context.strip()}\n\n{conversation_parts[0]['parts'][0]}"
            
            # Start chat with history (all but last message)
            if len(conversation_parts) > 1:
              chat = model_instance.start_chat(history=conversation_parts[:-1])
              # Send the last message (current user message)
              response = chat.send_message(conversation_parts[-1]["parts"][0])
            else:
              # No history, just send the message
              prompt = system_context.strip() + "\n\n" + conversation_parts[0]["parts"][0] if system_context.strip() else conversation_parts[0]["parts"][0]
              response = model_instance.generate_content(prompt)
            
            output = response.text
            
            # Clean quiz output if present
            if "**Question 1:**" in output or "Question 1:" in output:
              quiz_start = output.find("**Question 1:**")
              if quiz_start == -1:
                quiz_start = output.find("Question 1:")
              if quiz_start > 0:
                output = output[quiz_start:].strip()
            
            return output
          except Exception as final_error:
            print(f"Final fallback also failed: {str(final_error)}")
            # Last resort: return a simple error message
            raise Exception(f"Error generating response (finish_reason issue): {str(e)}. All fallback attempts failed. Please try again.") from e
      else:
        raise Exception(f"Error generating response: {str(e)}") from e
      
    except Exception as e:
      error_str = str(e).lower()
      
      # If we get consecutive messages error, retry with minimal history
      if "multiple messages" in error_str:
        # Retry with just the latest input, no history
        try:
          result = chain.invoke(
            {
              "input": latest_input,
              "chat_history": [],
            }
          )
          return result.content if hasattr(result, 'content') else str(result)
        except:
          pass
      
      raise Exception(f"Error generating response: {str(e)}") from e

  async def stream_response(
    self,
    agent: Agent,
    history: List[Message],
    latest_input: str,
  ):
    """Generate streaming response - simplified version."""
    chat_history = self._history_to_messages(history, latest_input)
    chain = self._build_chain(agent)
    
    try:
      if chat_history and isinstance(chat_history[-1], HumanMessage):
        current_input = chat_history[-1].content
        history_for_chain = chat_history[:-1]
      else:
        current_input = latest_input
        history_for_chain = chat_history
      
      async for chunk in chain.astream({
        "input": current_input,
        "chat_history": history_for_chain,
      }):
        content = chunk.content if hasattr(chunk, 'content') else str(chunk)
        if content:
          yield content
    except AttributeError as e:
      # Handle finish_reason AttributeError (unrecognized enum value from Gemini)
      if "'int' object has no attribute 'name'" in str(e) or "finish_reason" in str(e).lower():
        print(f"Warning: Unrecognized finish_reason in streaming, attempting fallback...")
        # Fallback: use LLM directly for streaming
        try:
          llm = self._build_llm(agent)
          # Build a simple prompt from history and current input
          prompt_parts = []
          for msg in history_for_chain:
            if isinstance(msg, HumanMessage):
              prompt_parts.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
              prompt_parts.append(f"Assistant: {msg.content}")
          
          prompt_parts.append(f"User: {current_input}")
          prompt_parts.append("Assistant:")
          
          full_prompt = "\n".join(prompt_parts)
          if agent.system_prompt:
            full_prompt = f"{agent.system_prompt}\n\n{full_prompt}"
          
          # Stream from LLM directly
          async for chunk in llm.astream(full_prompt):
            content = chunk.content if hasattr(chunk, 'content') else str(chunk)
            if content:
              yield content
        except Exception as fallback_error:
          yield f"Error: Failed to generate response due to finish_reason issue. Please try again."
    except Exception as e:
      yield f"Error: {str(e)}"
