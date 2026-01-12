import pytest
from unittest.mock import Mock, patch
from app.models.agent import Agent
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole


@pytest.fixture
def test_agent(db_session, test_user):
    """Create a test agent."""
    agent = Agent(
        user_id=test_user.id,
        name="Test Agent",
        system_prompt="You are a helpful assistant.",
        model="gemini-2.5-pro",
        temperature=0.7
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


@patch('app.api.v1.chat.GeminiClient')
def test_send_message_new_conversation(mock_gemini_client, client, auth_headers, test_agent):
    """Test sending a message creates a new conversation."""
    # Mock Gemini response
    mock_instance = Mock()
    mock_instance.generate_response.return_value = "This is a test response."
    mock_gemini_client.return_value = mock_instance
    
    response = client.post(
        f"/api/v1/chat/{test_agent.id}",
        json={
            "message": "Hello, how are you?"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert data["message"] == "This is a test response."
    assert data["agent_id"] == str(test_agent.id)
    
    # Verify Gemini was called
    mock_instance.generate_response.assert_called_once()


@patch('app.api.v1.chat.GeminiClient')
def test_send_message_existing_conversation(mock_gemini_client, client, auth_headers, db_session, test_user, test_agent):
    """Test sending a message to an existing conversation."""
    # Create conversation
    conv = Conversation(
        agent_id=test_agent.id,
        user_id=test_user.id,
        title="Test"
    )
    db_session.add(conv)
    db_session.commit()
    
    # Mock Gemini response
    mock_instance = Mock()
    mock_instance.generate_response.return_value = "Response to existing conversation."
    mock_gemini_client.return_value = mock_instance
    
    response = client.post(
        f"/api/v1/chat/{test_agent.id}",
        json={
            "conversation_id": str(conv.id),
            "message": "Hello again!"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == str(conv.id)
    assert data["message"] == "Response to existing conversation."


@patch('app.api.v1.chat.GeminiClient')
def test_send_message_with_history(mock_gemini_client, client, auth_headers, db_session, test_user, test_agent):
    """Test that conversation history is included in Gemini call."""
    # Create conversation with messages
    conv = Conversation(
        agent_id=test_agent.id,
        user_id=test_user.id,
        title="Test"
    )
    db_session.add(conv)
    db_session.commit()
    
    msg1 = Message(
        conversation_id=conv.id,
        role=MessageRole.USER,
        content="First message"
    )
    msg2 = Message(
        conversation_id=conv.id,
        role=MessageRole.ASSISTANT,
        content="First response"
    )
    db_session.add_all([msg1, msg2])
    db_session.commit()
    
    # Mock Gemini response
    mock_instance = Mock()
    mock_instance.generate_response.return_value = "Second response."
    mock_gemini_client.return_value = mock_instance
    
    response = client.post(
        f"/api/v1/chat/{test_agent.id}",
        json={
            "conversation_id": str(conv.id),
            "message": "Second message"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    
    # Verify Gemini was called with history
    call_args = mock_instance.generate_response.call_args
    assert call_args is not None
    messages = call_args[1]["messages"]
    assert len(messages) >= 2  # Should include previous messages


def test_send_message_agent_not_found(client, auth_headers):
    """Test sending message to non-existent agent."""
    import uuid
    fake_id = uuid.uuid4()
    
    response = client.post(
        f"/api/v1/chat/{fake_id}",
        json={"message": "Hello"},
        headers=auth_headers
    )
    
    assert response.status_code == 404


def test_send_message_unauthorized_agent(client, auth_headers, db_session):
    """Test sending message to agent owned by another user."""
    from app.models.user import User
    from app.core.security import get_password_hash
    from app.models.agent import Agent
    
    other_user = User(
        email="other@example.com",
        password_hash=get_password_hash("password123")
    )
    db_session.add(other_user)
    db_session.commit()
    
    other_agent = Agent(
        user_id=other_user.id,
        name="Other Agent",
        system_prompt="Prompt"
    )
    db_session.add(other_agent)
    db_session.commit()
    
    response = client.post(
        f"/api/v1/chat/{other_agent.id}",
        json={"message": "Hello"},
        headers=auth_headers
    )
    
    assert response.status_code == 404

