from typing import List, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from app.core.config import settings
from app.models.agent import Agent
from app.models.message import Message


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
    """
    # Limit history to last 8 messages for performance
    recent_history = history[-8:] if len(history) > 8 else history
    
    messages: List[Any] = []
    
    # Process history messages
    for m in recent_history:
      current_role = m.role.value
      
      # Add new message or merge with last if same role
      if messages and messages[-1].__class__.__name__ == ("HumanMessage" if current_role == "user" else "AIMessage"):
        # Merge with last message of same type
        messages[-1].content += f"\n\n{m.content}"
      else:
        # Add new message
        if current_role == "user":
          messages.append(HumanMessage(content=m.content))
        elif current_role == "assistant":
          messages.append(AIMessage(content=m.content))
    
    # If latest_input is provided, merge with last user message or add as new
    if latest_input:
      if messages and isinstance(messages[-1], HumanMessage):
        # Merge with last user message
        messages[-1].content += f"\n\n{latest_input}"
      else:
        # Add as new user message
        messages.append(HumanMessage(content=latest_input))
    
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
    """
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
      
      # Clean quiz output if present
      if "**Question 1:**" in output or "Question 1:" in output:
        quiz_start = output.find("**Question 1:**")
        if quiz_start == -1:
          quiz_start = output.find("Question 1:")
        if quiz_start > 0:
          output = output[quiz_start:].strip()
      
      return output
      
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
    except Exception as e:
      yield f"Error: {str(e)}"
