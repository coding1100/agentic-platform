import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.gemini import GeminiClient
from app.models.message import MessageRole


@patch('app.services.gemini.genai')
def test_gemini_client_initialization(mock_genai):
    """Test Gemini client initialization."""
    with patch('app.core.config.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "test-key"
        client = GeminiClient()
        mock_genai.configure.assert_called_once_with(api_key="test-key")


@patch('app.services.gemini.genai')
def test_gemini_client_missing_api_key(mock_genai):
    """Test Gemini client raises error when API key is missing."""
    with patch('app.core.config.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = ""
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            GeminiClient()


@patch('app.services.gemini.genai')
def test_generate_response_simple(mock_genai):
    """Test generating a simple response."""
    with patch('app.core.config.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "test-key"
        
        # Mock the model and response
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        client = GeminiClient()
        messages = [{"role": "user", "content": "Hello"}]
        
        result = client.generate_response(
            system_prompt="You are helpful.",
            messages=messages,
            model="gemini-2.5-pro",
            temperature=0.7
        )
        
        assert result == "Test response"


@patch('app.services.gemini.genai')
def test_generate_response_with_history(mock_genai):
    """Test generating response with conversation history."""
    with patch('app.core.config.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "test-key"
        
        # Mock the chat model
        mock_model = MagicMock()
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Response with history"
        mock_chat.send_message.return_value = mock_response
        mock_model.start_chat.return_value = mock_chat
        mock_genai.GenerativeModel.return_value = mock_model
        
        client = GeminiClient()
        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "First response"},
            {"role": "user", "content": "Second message"}
        ]
        
        result = client.generate_response(
            system_prompt="You are helpful.",
            messages=messages,
            model="gemini-2.5-pro",
            temperature=0.7
        )
        
        assert result == "Response with history"
        mock_chat.send_message.assert_called_once()

