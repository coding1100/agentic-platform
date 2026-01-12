import pytest
from app.models.agent import Agent


def test_create_agent(client, auth_headers):
    """Test creating a new agent."""
    response = client.post(
        "/api/v1/agents",
        json={
            "name": "Test Agent",
            "description": "A test agent",
            "system_prompt": "You are a helpful assistant.",
            "model": "gemini-2.5-pro",
            "temperature": 0.7
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Agent"
    assert data["description"] == "A test agent"
    assert data["system_prompt"] == "You are a helpful assistant."
    assert "id" in data


def test_list_agents(client, auth_headers, db_session, test_user):
    """Test listing agents."""
    # Create test agents
    agent1 = Agent(
        user_id=test_user.id,
        name="Agent 1",
        system_prompt="Prompt 1"
    )
    agent2 = Agent(
        user_id=test_user.id,
        name="Agent 2",
        system_prompt="Prompt 2"
    )
    db_session.add_all([agent1, agent2])
    db_session.commit()
    
    response = client.get("/api/v1/agents", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(agent["name"] in ["Agent 1", "Agent 2"] for agent in data)


def test_get_agent(client, auth_headers, db_session, test_user):
    """Test getting a specific agent."""
    agent = Agent(
        user_id=test_user.id,
        name="Test Agent",
        system_prompt="Test prompt"
    )
    db_session.add(agent)
    db_session.commit()
    
    response = client.get(f"/api/v1/agents/{agent.id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Agent"
    assert data["id"] == str(agent.id)


def test_get_agent_not_found(client, auth_headers):
    """Test getting non-existent agent."""
    import uuid
    fake_id = uuid.uuid4()
    response = client.get(f"/api/v1/agents/{fake_id}", headers=auth_headers)
    
    assert response.status_code == 404


def test_update_agent(client, auth_headers, db_session, test_user):
    """Test updating an agent."""
    agent = Agent(
        user_id=test_user.id,
        name="Original Name",
        system_prompt="Original prompt"
    )
    db_session.add(agent)
    db_session.commit()
    
    response = client.put(
        f"/api/v1/agents/{agent.id}",
        json={
            "name": "Updated Name",
            "temperature": 0.9
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["temperature"] == 0.9
    assert data["system_prompt"] == "Original prompt"  # Unchanged


def test_delete_agent(client, auth_headers, db_session, test_user):
    """Test deleting an agent."""
    agent = Agent(
        user_id=test_user.id,
        name="To Delete",
        system_prompt="Prompt"
    )
    db_session.add(agent)
    db_session.commit()
    agent_id = agent.id
    
    response = client.delete(f"/api/v1/agents/{agent_id}", headers=auth_headers)
    
    assert response.status_code == 204
    
    # Verify deletion
    get_response = client.get(f"/api/v1/agents/{agent_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_agent_ownership(client, auth_headers, db_session):
    """Test that users can only access their own agents."""
    # Create another user and agent
    from app.models.user import User
    from app.core.security import get_password_hash
    
    other_user = User(
        email="other@example.com",
        password_hash=get_password_hash("password123")
    )
    db_session.add(other_user)
    db_session.commit()
    
    from app.models.agent import Agent
    other_agent = Agent(
        user_id=other_user.id,
        name="Other Agent",
        system_prompt="Prompt"
    )
    db_session.add(other_agent)
    db_session.commit()
    
    # Try to access other user's agent
    response = client.get(f"/api/v1/agents/{other_agent.id}", headers=auth_headers)
    
    assert response.status_code == 404

