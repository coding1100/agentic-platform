import pytest
from app.models.conversation import Conversation
from app.models.agent import Agent


@pytest.fixture
def test_agent(db_session, test_user):
    """Create a test agent."""
    agent = Agent(
        user_id=test_user.id,
        name="Test Agent",
        system_prompt="Test prompt"
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


def test_create_conversation(client, auth_headers, test_agent):
    """Test creating a new conversation."""
    response = client.post(
        "/api/v1/conversations",
        json={
            "agent_id": str(test_agent.id),
            "title": "Test Conversation"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["agent_id"] == str(test_agent.id)
    assert data["title"] == "Test Conversation"
    assert "id" in data


def test_list_conversations(client, auth_headers, db_session, test_user, test_agent):
    """Test listing conversations for an agent."""
    conv1 = Conversation(
        agent_id=test_agent.id,
        user_id=test_user.id,
        title="Conv 1"
    )
    conv2 = Conversation(
        agent_id=test_agent.id,
        user_id=test_user.id,
        title="Conv 2"
    )
    db_session.add_all([conv1, conv2])
    db_session.commit()
    
    response = client.get(
        f"/api/v1/conversations/agent/{test_agent.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_conversation(client, auth_headers, db_session, test_user, test_agent):
    """Test getting a specific conversation."""
    conv = Conversation(
        agent_id=test_agent.id,
        user_id=test_user.id,
        title="Test Conv"
    )
    db_session.add(conv)
    db_session.commit()
    
    response = client.get(
        f"/api/v1/conversations/{conv.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Conv"
    assert data["id"] == str(conv.id)
    assert "messages" in data


def test_conversation_ownership(client, auth_headers, db_session, test_agent):
    """Test that users can only access their own conversations."""
    from app.models.user import User
    from app.core.security import get_password_hash
    from app.models.conversation import Conversation
    
    other_user = User(
        email="other@example.com",
        password_hash=get_password_hash("password123")
    )
    db_session.add(other_user)
    db_session.commit()
    
    other_conv = Conversation(
        agent_id=test_agent.id,
        user_id=other_user.id,
        title="Other Conv"
    )
    db_session.add(other_conv)
    db_session.commit()
    
    # Try to access other user's conversation
    response = client.get(
        f"/api/v1/conversations/{other_conv.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 404

