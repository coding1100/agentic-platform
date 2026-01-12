import google.generativeai as genai
from typing import List, Dict, Optional
from app.core.config import settings
from app.models.message import MessageRole


class GeminiClient:
    """Client for interacting with Google Gemini API."""
    
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY must be set in environment variables")
        genai.configure(api_key=settings.GEMINI_API_KEY)
    
    def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        model: str = "gemini-2.5-pro",
        temperature: float = 0.7
    ) -> str:
        """
        Generate a response from Gemini.
        
        Args:
            system_prompt: System prompt/instructions for the agent
            messages: List of message dicts with 'role' and 'content' keys
            model: Gemini model name
            temperature: Temperature for generation
        
        Returns:
            Generated response text
        """
        try:
            # Configure the model
            generation_config = {
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
            
            # Build the conversation history
            # Gemini uses a different format - we need to combine system prompt with history
            conversation_parts = []
            
            # Add system prompt as the first user message with instruction
            # Note: Gemini doesn't have a separate system role, so we prepend it
            full_system_context = f"{system_prompt}\n\n"
            
            # Convert messages to Gemini format
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content", "")
                
                # Handle both enum and string values
                role_str = role.value if hasattr(role, 'value') else str(role)
                
                if role_str == MessageRole.USER.value or role_str == "user":
                    conversation_parts.append({"role": "user", "parts": [content]})
                elif role_str == MessageRole.ASSISTANT.value or role_str == "assistant":
                    conversation_parts.append({"role": "model", "parts": [content]})
                elif role_str == MessageRole.SYSTEM.value or role_str == "system":
                    # System messages are incorporated into context
                    full_system_context += f"{content}\n\n"
            
            # Initialize model
            model_instance = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config
            )
            
            # If we have conversation history, use chat
            if len(conversation_parts) > 0:
                # Prepend system context to first user message if exists
                if full_system_context.strip() and conversation_parts[0]["role"] == "user":
                    conversation_parts[0]["parts"][0] = full_system_context.strip() + "\n\n" + conversation_parts[0]["parts"][0]
                
                # Start chat with history
                chat = model_instance.start_chat(history=conversation_parts[:-1] if len(conversation_parts) > 1 else [])
                # Send the last message (current user message)
                response = chat.send_message(conversation_parts[-1]["parts"][0] if conversation_parts[-1]["role"] == "user" else "")
            else:
                # No history, just send system prompt + first message
                prompt = full_system_context.strip()
                if conversation_parts and conversation_parts[0]["role"] == "user":
                    prompt += "\n\n" + conversation_parts[0]["parts"][0]
                response = model_instance.generate_content(prompt)
            
            return response.text
        
        except Exception as e:
            raise Exception(f"Error generating response from Gemini: {str(e)}")

