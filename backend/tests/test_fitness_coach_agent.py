import json

from app.tools.prebuilt_agents import (
    PREBUILT_AGENT_SLUGS,
    _generate_fitness_coach_response,
)


def test_fitness_coach_slug_registered():
    assert PREBUILT_AGENT_SLUGS["fitness_coach_agent"] == "health.fitness_coach_agent"


def test_fitness_coach_invalid_action_returns_error():
    result = json.loads(_generate_fitness_coach_response("not_supported", {}))
    assert result["status"] == "error"
    assert result["error"] == "invalid_action"


def test_fitness_coach_profile_baseline_requires_context():
    result = json.loads(_generate_fitness_coach_response("profile_baseline", {}))
    assert result["status"] == "error"
    assert result["error"] == "insufficient_input"


def test_fitness_coach_feedback_requires_sessions_and_plan():
    missing_sessions = json.loads(
        _generate_fitness_coach_response("log_workout_feedback", {"plan_report": {}})
    )
    assert missing_sessions["status"] == "error"
    assert missing_sessions["error"] == "completed_sessions_required"

    missing_plan = json.loads(
        _generate_fitness_coach_response(
            "log_workout_feedback",
            {"completed_sessions": ["Session A"]},
        )
    )
    assert missing_plan["status"] == "error"
    assert missing_plan["error"] == "plan_report_required"


def test_fitness_coach_goal_required_actions():
    for action in ("generate_adaptive_plan", "challenge_mode", "progress_reassessment"):
        result = json.loads(_generate_fitness_coach_response(action, {}))
        assert result["status"] == "error"
        assert result["error"] == "primary_goal_required"
