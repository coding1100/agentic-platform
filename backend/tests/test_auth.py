import pytest
from app.models.user import User


def test_signup_success(client, db_session):
    """Test successful user signup."""
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "newuser@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "password_hash" not in data


def test_signup_duplicate_email(client, test_user):
    """Test signup with duplicate email."""
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client, test_user):
    """Test login with invalid credentials."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_get_current_user(client, auth_headers, test_user):
    """Test getting current user info."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == str(test_user.id)


def test_get_current_user_unauthorized(client):
    """Test getting current user without authentication."""
    response = client.get("/api/v1/auth/me")
    
    assert response.status_code == 401

