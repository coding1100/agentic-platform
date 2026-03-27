import json

from livekit import api as livekit_api
from app.core.config import settings
from app.models.agent import Agent


def _set_livekit_test_env() -> None:
    settings.LIVEKIT_URL = "wss://test.livekit.example"
    settings.LIVEKIT_API_KEY = "test_key"
    settings.LIVEKIT_API_SECRET = "test_secret"


def _create_realtime_agent(db_session, test_user, avatar_id: str | None = None) -> Agent:
    agent = Agent(
        user_id=test_user.id,
        name="Realtime Interview Agent",
        description="Avatar interview agent",
        system_prompt="Conduct realistic interview sessions.",
        interaction_mode="avatar_realtime",
        livekit_agent_name="avatar-interview-agent",
        avatar_provider="browser",
        avatar_id=avatar_id,
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


def test_upsert_and_get_embed_deployment(client, auth_headers, db_session, test_user):
    _set_livekit_test_env()
    agent = _create_realtime_agent(db_session, test_user)

    upsert_resp = client.put(
        f"/api/v1/realtime/agents/{agent.id}/embed",
        headers=auth_headers,
        json={
            "is_active": True,
            "allowed_origins": ["https://customer.example.com"],
            "token_ttl_seconds": 600,
            "max_concurrent_sessions": 2,
            "room_name_prefix": "customer-interviews",
        },
    )
    assert upsert_resp.status_code == 200
    deployment = upsert_resp.json()
    assert deployment["agent_id"] == str(agent.id)
    assert deployment["embed_id"].startswith("emb_")
    assert deployment["token_ttl_seconds"] == 600
    assert deployment["max_concurrent_sessions"] == 2

    get_resp = client.get(
        f"/api/v1/realtime/agents/{agent.id}/embed",
        headers=auth_headers,
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["embed_id"] == deployment["embed_id"]


def test_create_realtime_token_for_authenticated_user(client, auth_headers, db_session, test_user):
    _set_livekit_test_env()
    agent = _create_realtime_agent(db_session, test_user)

    token_resp = client.post(
        f"/api/v1/realtime/agents/{agent.id}/token",
        headers=auth_headers,
        json={"participant_name": "Umair"},
    )
    assert token_resp.status_code == 201
    body = token_resp.json()

    assert body["server_url"] == settings.LIVEKIT_URL
    assert body["participant_token"]
    assert body["agent_id"] == str(agent.id)
    assert body["participant_name"] == "Umair"

    claims = livekit_api.TokenVerifier(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET).verify(
        body["participant_token"]
    )
    assert claims.video is not None
    assert claims.video.room == body["room_name"]
    assert claims.room_config is not None
    assert len(claims.room_config.agents) == 1
    assert claims.room_config.agents[0].agent_name == "avatar-interview-agent"
    dispatch_metadata = json.loads(claims.room_config.agents[0].metadata)
    assert dispatch_metadata["agent_id"] == str(agent.id)
    assert dispatch_metadata["instructions"] == "Conduct realistic interview sessions."


def test_public_embed_token_success_and_origin_block(client, auth_headers, db_session, test_user):
    _set_livekit_test_env()
    agent = _create_realtime_agent(db_session, test_user)

    deployment_resp = client.put(
        f"/api/v1/realtime/agents/{agent.id}/embed",
        headers=auth_headers,
        json={
            "is_active": True,
            "allowed_origins": ["https://allowed.example.com"],
            "token_ttl_seconds": 900,
            "max_concurrent_sessions": 1,
        },
    )
    assert deployment_resp.status_code == 200
    embed_id = deployment_resp.json()["embed_id"]

    allowed_token_resp = client.post(
        f"/api/v1/public/realtime/embed/{embed_id}/token",
        headers={"Origin": "https://allowed.example.com"},
        json={"participant_name": "Candidate"},
    )
    assert allowed_token_resp.status_code == 201
    allowed_payload = allowed_token_resp.json()
    assert allowed_payload["embed_id"] == embed_id
    assert allowed_payload["participant_name"] == "Candidate"

    blocked_token_resp = client.post(
        f"/api/v1/public/realtime/embed/{embed_id}/token",
        headers={"Origin": "https://blocked.example.com"},
        json={"participant_name": "Candidate"},
    )
    assert blocked_token_resp.status_code == 403


def test_public_embed_concurrency_limit_and_session_end(client, auth_headers, db_session, test_user):
    _set_livekit_test_env()
    agent = _create_realtime_agent(db_session, test_user)

    deployment_resp = client.put(
        f"/api/v1/realtime/agents/{agent.id}/embed",
        headers=auth_headers,
        json={
            "is_active": True,
            "allowed_origins": ["https://allowed.example.com"],
            "token_ttl_seconds": 900,
            "max_concurrent_sessions": 1,
        },
    )
    assert deployment_resp.status_code == 200
    embed_id = deployment_resp.json()["embed_id"]

    first_resp = client.post(
        f"/api/v1/public/realtime/embed/{embed_id}/token",
        headers={"Origin": "https://allowed.example.com"},
        json={"participant_name": "Candidate One"},
    )
    assert first_resp.status_code == 201
    first_session_id = first_resp.json()["session_id"]

    second_resp = client.post(
        f"/api/v1/public/realtime/embed/{embed_id}/token",
        headers={"Origin": "https://allowed.example.com"},
        json={"participant_name": "Candidate Two"},
    )
    assert second_resp.status_code == 429

    end_resp = client.post(
        f"/api/v1/realtime/sessions/{first_session_id}/end",
        headers=auth_headers,
    )
    assert end_resp.status_code == 200
    assert end_resp.json()["status"] == "ended"

    third_resp = client.post(
        f"/api/v1/public/realtime/embed/{embed_id}/token",
        headers={"Origin": "https://allowed.example.com"},
        json={"participant_name": "Candidate Three"},
    )
    assert third_resp.status_code == 201


def test_public_embed_can_end_session_without_auth_key(client, auth_headers, db_session, test_user):
    _set_livekit_test_env()
    agent = _create_realtime_agent(db_session, test_user)

    deployment_resp = client.put(
        f"/api/v1/realtime/agents/{agent.id}/embed",
        headers=auth_headers,
        json={
            "is_active": True,
            "allowed_origins": ["https://customer.example.com"],
            "token_ttl_seconds": 900,
            "max_concurrent_sessions": 1,
        },
    )
    assert deployment_resp.status_code == 200
    embed_id = deployment_resp.json()["embed_id"]

    token_resp = client.post(
        f"/api/v1/public/realtime/embed/{embed_id}/token",
        headers={"Origin": "https://customer.example.com"},
        json={"participant_name": "Candidate"},
    )
    assert token_resp.status_code == 201
    session_id = token_resp.json()["session_id"]

    end_resp = client.post(
        f"/api/v1/public/realtime/embed/{embed_id}/sessions/{session_id}/end",
        headers={"Origin": "https://customer.example.com"},
        json={"origin_hint": "https://customer.example.com"},
    )
    assert end_resp.status_code == 204

    second_resp = client.post(
        f"/api/v1/public/realtime/embed/{embed_id}/token",
        headers={"Origin": "https://customer.example.com"},
        json={"participant_name": "Candidate 2"},
    )
    assert second_resp.status_code == 201


def test_embed_origins_accept_ports(client, auth_headers, db_session, test_user):
    _set_livekit_test_env()
    agent = _create_realtime_agent(db_session, test_user)

    deployment_resp = client.put(
        f"/api/v1/realtime/agents/{agent.id}/embed",
        headers=auth_headers,
        json={
            "is_active": True,
            "allowed_origins": ["http://localhost:5173"],
            "token_ttl_seconds": 900,
            "max_concurrent_sessions": 2,
        },
    )
    assert deployment_resp.status_code == 200

    embed_id = deployment_resp.json()["embed_id"]
    token_resp = client.post(
        f"/api/v1/public/realtime/embed/{embed_id}/token",
        headers={"Origin": "http://localhost:5173"},
        json={"participant_name": "Local Candidate"},
    )
    assert token_resp.status_code == 201
