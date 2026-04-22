import pytest

from app.models.agent import Agent
from app.services.tutor import TutorWorkspaceService


@pytest.fixture
def test_agent(db_session, test_user):
    agent = Agent(
        user_id=test_user.id,
        name="Tutor Agent",
        system_prompt="You are an AI tutor tool.",
        model="gemini-2.5-flash",
        temperature=0.4,
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


def test_tutor_workspace_round_trip(client, auth_headers, test_agent):
    payload = {
        "subject": "Calculus",
        "academic_level": "college",
        "learner_name": "Hidden Learner",
        "selected_action": "ask_question",
        "selected_mode": "personalized_learning",
        "progress": {
            "sessions_completed": 2,
            "practice_sessions_attempted": 1,
            "practice_sessions_completed": 1,
            "source_sessions": 0,
            "average_score": 92,
            "weak_topics": ["Integration by parts"],
            "mastery_by_topic": {"Limits": 95},
            "recent_activity": ["2026-04-22 12:00 - ask question in Calculus"],
            "next_recommended_action": "Generate a practice set",
        },
        "recent_sources": [],
        "recent_results": [],
    }

    save_response = client.put(
        f"/api/v1/tutor/{test_agent.id}/workspace",
        json=payload,
        headers=auth_headers,
    )

    assert save_response.status_code == 200
    saved = save_response.json()
    assert saved["subject"] == "Calculus"
    assert saved["academic_level"] == "college"
    assert saved["learner_name"] == "Hidden Learner"
    assert saved["selected_action"] == "ask_question"
    assert saved["selected_mode"] == "personalized_learning"

    get_response = client.get(
        f"/api/v1/tutor/{test_agent.id}/workspace",
        headers=auth_headers,
    )

    assert get_response.status_code == 200
    loaded = get_response.json()
    assert loaded["learner_name"] == "Hidden Learner"
    assert loaded["progress"]["average_score"] == 92
    assert loaded["progress"]["weak_topics"] == ["Integration by parts"]


def test_tutor_execute_persists_progress_without_learner_name(
    client,
    auth_headers,
    test_agent,
    monkeypatch,
):
    def fake_structured_response(self, request, source_text):
        assert request.learner_name is None
        assert source_text == "Cell cycle notes"
        return {
            "explanation": "Mitosis has distinct phases that preserve chromosome count.",
            "steps": [
                "Review the order of mitosis phases.",
                "Compare mitosis with cytokinesis.",
            ],
            "key_concepts": ["Mitosis", "Chromosomes"],
            "suggested_next_actions": ["Generate a practice set"],
            "practice_set": {
                "title": "Mitosis practice",
                "instructions": "Answer each question and review the key.",
                "questions": [
                    {
                        "id": "q1",
                        "prompt": "Which phase aligns chromosomes at the cell equator?",
                        "type": "multiple_choice",
                        "concept": "Mitosis",
                        "options": [
                            {"id": "A", "text": "Metaphase"},
                            {"id": "B", "text": "Telophase"},
                            {"id": "C", "text": "Interphase"},
                            {"id": "D", "text": "Cytokinesis"},
                        ],
                        "answer": "A",
                        "explanation": "Chromosomes align at the metaphase plate during metaphase.",
                    }
                ],
            },
        }

    monkeypatch.setattr(
        TutorWorkspaceService,
        "_generate_structured_response",
        fake_structured_response,
    )

    execute_response = client.post(
        f"/api/v1/tutor/{test_agent.id}/execute",
        json={
            "action": "upload_notes",
            "learning_mode": "source_based_learning",
            "subject": "Biology",
            "academic_level": "high_school",
            "source_text": "Cell cycle notes",
            "source_name": "chapter-4-notes",
            "source_kind": "notes",
            "prompt": "Summarize and create practice questions.",
        },
        headers=auth_headers,
    )

    assert execute_response.status_code == 200
    payload = execute_response.json()
    assert payload["learner_name"] is None
    assert payload["summary"] == "AI summary prepared for Biology using the uploaded notes."
    assert payload["explanation"].startswith("Mitosis")
    assert payload["practice_set"]["title"] == "Mitosis practice"
    assert payload["progress_snapshot"]["sessions_completed"] == 1
    assert payload["progress_snapshot"]["source_sessions"] == 1

    workspace_response = client.get(
        f"/api/v1/tutor/{test_agent.id}/workspace",
        headers=auth_headers,
    )

    assert workspace_response.status_code == 200
    workspace = workspace_response.json()
    assert workspace["subject"] == "Biology"
    assert workspace["academic_level"] == "high_school"
    assert workspace["learner_name"] is None
    assert workspace["selected_action"] == "upload_notes"
    assert workspace["selected_mode"] == "source_based_learning"
    assert workspace["progress"]["sessions_completed"] == 1
    assert workspace["recent_sources"][0]["name"] == "chapter-4-notes"
    assert workspace["recent_sources"][0]["kind"] == "notes"
    assert workspace["recent_results"][0]["title"] == "Mitosis practice"


def test_tutor_execute_rejects_invalid_enum(client, auth_headers, test_agent):
    response = client.post(
        f"/api/v1/tutor/{test_agent.id}/execute",
        json={
            "action": "practice",
            "learning_mode": "practice_quiz_generator",
            "subject": "Physics",
            "academic_level": "middle_school",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422
