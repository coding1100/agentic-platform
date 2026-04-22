import json
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

import google.generativeai as genai
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user_state import UserState
from app.schemas.tutor import (
    TutorAcademicLevel,
    TutorAction,
    TutorExecuteRequest,
    TutorExecuteResponse,
    TutorLearningMode,
    TutorPracticeFormat,
    TutorPracticeQuestion,
    TutorPracticeSet,
    TutorProgressSummary,
    TutorRecentResult,
    TutorRecentSource,
    TutorSourceKind,
    TutorWorkspaceState,
)


class TutorWorkspaceService:
    """Structured Tutor workflow service backed by persisted workspace state."""

    MAX_SOURCE_TEXT = 20000
    MAX_RECENT_ITEMS = 8
    FLASH_MODEL = "gemini-2.5-flash"

    def __init__(self) -> None:
        self._configured = False

    def get_workspace(self, db: Session, user_id: UUID, agent_id: UUID) -> TutorWorkspaceState:
        state = self._get_state_row(db, user_id, agent_id)
        if not state:
            return TutorWorkspaceState()
        return self._normalize_workspace_state(state.data or {})

    def save_workspace(
        self,
        db: Session,
        user_id: UUID,
        agent_id: UUID,
        workspace: TutorWorkspaceState,
    ) -> TutorWorkspaceState:
        normalized = self._normalize_workspace_state(workspace.model_dump())
        state = self._get_state_row(db, user_id, agent_id)
        if state:
            state.data = normalized.model_dump(mode="json")
        else:
            state = UserState(
                user_id=user_id,
                namespace=self._namespace(agent_id),
                data=normalized.model_dump(mode="json"),
            )
            db.add(state)

        db.commit()
        db.refresh(state)
        return self._normalize_workspace_state(state.data or {})

    def execute(
        self,
        db: Session,
        user_id: UUID,
        agent_id: UUID,
        request: TutorExecuteRequest,
    ) -> TutorExecuteResponse:
        workspace = self.get_workspace(db, user_id, agent_id)
        source_text = (request.source_text or "").strip()
        if source_text:
            source_text = source_text[: self.MAX_SOURCE_TEXT]

        structured = self._generate_structured_response(request=request, source_text=source_text)
        response = self._normalize_execute_response(request=request, payload=structured, workspace=workspace)

        updated_workspace = self._apply_execution_to_workspace(
            workspace=workspace,
            request=request,
            response=response,
            source_text=source_text,
        )
        saved = self.save_workspace(db, user_id, agent_id, updated_workspace)
        return response.model_copy(update={"progress_snapshot": saved.progress})

    def _namespace(self, agent_id: UUID) -> str:
        return f"tutor:{agent_id}"

    def _get_state_row(self, db: Session, user_id: UUID, agent_id: UUID) -> Optional[UserState]:
        return db.query(UserState).filter(
            UserState.user_id == user_id,
            UserState.namespace == self._namespace(agent_id),
        ).first()

    def _normalize_workspace_state(self, payload: Dict[str, Any]) -> TutorWorkspaceState:
        try:
            workspace = TutorWorkspaceState.model_validate(payload or {})
        except Exception:
            workspace = TutorWorkspaceState()

        mastery = {}
        for topic, value in workspace.progress.mastery_by_topic.items():
            try:
                mastery[topic] = max(0.0, min(100.0, float(value)))
            except (TypeError, ValueError):
                continue
        workspace.progress.mastery_by_topic = mastery

        workspace.recent_sources = workspace.recent_sources[: self.MAX_RECENT_ITEMS]
        workspace.recent_results = workspace.recent_results[: self.MAX_RECENT_ITEMS]
        workspace.progress.recent_activity = workspace.progress.recent_activity[: self.MAX_RECENT_ITEMS]
        return workspace

    def _generate_structured_response(
        self,
        request: TutorExecuteRequest,
        source_text: str,
    ) -> Dict[str, Any]:
        self._ensure_client()
        prompt = self._build_prompt(request=request, source_text=source_text)
        model = genai.GenerativeModel(
            model_name=self.FLASH_MODEL,
            generation_config={
                "temperature": 0.4,
                "top_p": 0.9,
                "top_k": 32,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",
            },
        )
        response = model.generate_content(prompt)
        raw = response.text if hasattr(response, "text") else str(response)
        return self._parse_json_payload(raw)

    def _build_prompt(self, request: TutorExecuteRequest, source_text: str) -> str:
        question_count = request.question_count or (5 if request.action == TutorAction.PRACTICE else 3)
        practice_format = (request.practice_format or TutorPracticeFormat.MIXED).value
        source_label = request.source_kind.value if request.source_kind else "notes"
        prompt = (request.prompt or "").strip()

        return f"""
You are an AI-powered Tutor Tool for a software platform. You are not a human teacher, tutor, or coach.
You must return only valid JSON and no markdown fences.

Learner context:
- Subject: {request.subject}
- Academic level: {request.academic_level.value}
- Optional learner name: {request.learner_name or "not provided"}
- Action: {request.action.value}
- Learning mode: {request.learning_mode.value}
- Requested practice format: {practice_format}
- Requested question count: {question_count}

User prompt:
{prompt or "No extra prompt was provided. Infer the most helpful outcome for the selected action and mode."}

Source details:
- Source kind: {source_label}
- Source name: {request.source_name or "not provided"}
- Source text present: {"yes" if source_text else "no"}
- Source text:
{source_text or "No source text was provided."}

Return JSON with this exact top-level shape:
{{
  "summary": "optional string or null",
  "explanation": "string",
  "steps": ["string", "string"],
  "key_concepts": ["string", "string"],
  "suggested_next_actions": ["string", "string"],
  "practice_set": {{
    "title": "string",
    "instructions": "string",
    "questions": [
      {{
        "id": "q1",
        "prompt": "string",
        "type": "multiple_choice|short_answer",
        "concept": "string or null",
        "options": [
          {{"id": "A", "text": "string"}},
          {{"id": "B", "text": "string"}}
        ],
        "answer": "string",
        "explanation": "string"
      }}
    ]
  }}
}}

Requirements:
- Always include Explanation, Steps, Key Concepts, Suggested Next Actions, and Practice Set.
- For upload_notes, also include a concise Summary.
- Practice questions must match the requested subject, academic level, action, and learning mode.
- Use exactly {question_count} practice questions when possible.
- Prefer multiple choice only when the practice format is multiple_choice, short_answer only when short_answer, and a thoughtful mix when mixed.
- Keep steps actionable and concise.
- Make the output suitable for an AI learning tool embedded in software, not a human teaching service.
""".strip()

    def _parse_json_payload(self, raw: str) -> Dict[str, Any]:
        text = (raw or "").strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            first_brace = text.find("{")
            last_brace = text.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                return json.loads(text[first_brace : last_brace + 1])
            raise

    def _ensure_client(self) -> None:
        if self._configured:
            return
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY must be set in environment variables")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._configured = True

    def _normalize_execute_response(
        self,
        request: TutorExecuteRequest,
        payload: Dict[str, Any],
        workspace: TutorWorkspaceState,
    ) -> TutorExecuteResponse:
        practice_payload = payload.get("practice_set") if isinstance(payload, dict) else {}
        default_count = request.question_count or (5 if request.action == TutorAction.PRACTICE else 3)
        practice_set = self._normalize_practice_set(practice_payload, request.practice_format, default_count, request.subject)

        steps = self._string_list(payload.get("steps"), fallback=["Review the explanation carefully.", "Complete the practice set.", "Use the next action to continue learning."])
        key_concepts = self._string_list(payload.get("key_concepts"), fallback=[request.subject, request.learning_mode.value.replace("_", " ")])
        next_actions = self._string_list(
            payload.get("suggested_next_actions"),
            fallback=["Ask a follow-up question", "Generate more practice", "Upload notes for source-based help"],
        )

        summary = payload.get("summary")
        if request.action == TutorAction.UPLOAD_NOTES and not isinstance(summary, str):
            summary = f"AI summary prepared for {request.subject} using the uploaded {request.source_kind.value if request.source_kind else 'notes'}."
        if summary is not None and not isinstance(summary, str):
            summary = str(summary)

        explanation = payload.get("explanation")
        if not isinstance(explanation, str) or not explanation.strip():
            explanation = f"This AI tutor workspace prepared a guided {request.action.value.replace('_', ' ')} flow for {request.subject} at the {request.academic_level.value.replace('_', ' ')} level."

        return TutorExecuteResponse(
            action=request.action,
            learning_mode=request.learning_mode,
            subject=request.subject.strip(),
            academic_level=request.academic_level,
            learner_name=(request.learner_name or workspace.learner_name),
            summary=summary,
            explanation=explanation.strip(),
            steps=steps,
            practice_set=practice_set,
            key_concepts=key_concepts,
            progress_snapshot=workspace.progress,
            suggested_next_actions=next_actions,
        )

    def _normalize_practice_set(
        self,
        payload: Any,
        requested_format: Optional[TutorPracticeFormat],
        question_count: int,
        subject: str,
    ) -> TutorPracticeSet:
        if not isinstance(payload, dict):
            payload = {}

        questions = []
        raw_questions = payload.get("questions")
        if isinstance(raw_questions, list):
            for index, item in enumerate(raw_questions, start=1):
                if not isinstance(item, dict):
                    continue
                question_type = item.get("type")
                if question_type not in {TutorPracticeFormat.MULTIPLE_CHOICE.value, TutorPracticeFormat.SHORT_ANSWER.value}:
                    question_type = requested_format.value if requested_format and requested_format != TutorPracticeFormat.MIXED else (
                        TutorPracticeFormat.MULTIPLE_CHOICE.value if index % 2 else TutorPracticeFormat.SHORT_ANSWER.value
                    )

                options = []
                if question_type == TutorPracticeFormat.MULTIPLE_CHOICE.value:
                    raw_options = item.get("options")
                    if isinstance(raw_options, list):
                        for option_index, option in enumerate(raw_options, start=1):
                            if not isinstance(option, dict):
                                continue
                            option_id = str(option.get("id") or chr(64 + option_index))
                            option_text = str(option.get("text") or "").strip()
                            if option_text:
                                options.append({"id": option_id, "text": option_text})

                prompt = str(item.get("prompt") or "").strip()
                answer = item.get("answer")
                explanation = item.get("explanation")
                concept = item.get("concept")
                if not prompt:
                    continue
                questions.append(
                    TutorPracticeQuestion(
                        id=str(item.get("id") or f"q{index}"),
                        prompt=prompt,
                        type=TutorPracticeFormat(question_type),
                        concept=str(concept).strip() if concept else None,
                        options=options,
                        answer=str(answer).strip() if answer is not None else None,
                        explanation=str(explanation).strip() if explanation is not None else None,
                    )
                )

        if not questions:
            fallback_type = requested_format or TutorPracticeFormat.MIXED
            for index in range(1, min(question_count, 3) + 1):
                question_type = (
                    TutorPracticeFormat.MULTIPLE_CHOICE
                    if fallback_type == TutorPracticeFormat.MULTIPLE_CHOICE
                    else TutorPracticeFormat.SHORT_ANSWER
                    if fallback_type == TutorPracticeFormat.SHORT_ANSWER
                    else TutorPracticeFormat.MULTIPLE_CHOICE
                    if index % 2
                    else TutorPracticeFormat.SHORT_ANSWER
                )
                options = []
                answer = "A concise answer."
                if question_type == TutorPracticeFormat.MULTIPLE_CHOICE:
                    options = [
                        {"id": "A", "text": f"Core idea about {subject}"},
                        {"id": "B", "text": f"Common misconception about {subject}"},
                        {"id": "C", "text": f"Unrelated detail about {subject}"},
                        {"id": "D", "text": f"Advanced exception in {subject}"},
                    ]
                    answer = "A"
                questions.append(
                    TutorPracticeQuestion(
                        id=f"q{index}",
                        prompt=f"Practice question {index} for {subject}.",
                        type=question_type,
                        concept=subject,
                        options=options,
                        answer=answer,
                        explanation=f"Use the explanation section to reason through this {subject} question.",
                    )
                )

        title = payload.get("title")
        instructions = payload.get("instructions")
        if not isinstance(title, str) or not title.strip():
            title = f"{subject} practice set"
        if not isinstance(instructions, str) or not instructions.strip():
            instructions = "Complete each question, then review the answer and explanation."

        return TutorPracticeSet(
            title=title.strip(),
            instructions=instructions.strip(),
            questions=questions[:question_count],
        )

    def _apply_execution_to_workspace(
        self,
        workspace: TutorWorkspaceState,
        request: TutorExecuteRequest,
        response: TutorExecuteResponse,
        source_text: str,
    ) -> TutorWorkspaceState:
        progress = workspace.progress
        progress.sessions_completed += 1
        progress.recent_activity = [
            f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M')} - {request.action.value.replace('_', ' ')} in {request.subject}",
            *progress.recent_activity,
        ][: self.MAX_RECENT_ITEMS]
        progress.next_recommended_action = response.suggested_next_actions[0] if response.suggested_next_actions else None

        recent_sources = list(workspace.recent_sources)
        if source_text:
            progress.source_sessions += 1
            recent_sources.insert(
                0,
                TutorRecentSource(
                    name=(request.source_name or f"{request.subject} source").strip(),
                    kind=request.source_kind or TutorSourceKind.NOTES,
                    char_count=len(source_text),
                    added_at=datetime.utcnow(),
                ),
            )

        recent_results = list(workspace.recent_results)
        recent_results.insert(
            0,
            TutorRecentResult(
                action=request.action,
                learning_mode=request.learning_mode,
                title=response.practice_set.title,
                score=None,
                weak_topics=[],
                created_at=datetime.utcnow(),
            ),
        )

        return TutorWorkspaceState(
            subject=request.subject.strip(),
            academic_level=request.academic_level,
            learner_name=(request.learner_name or workspace.learner_name),
            selected_action=request.action,
            selected_mode=request.learning_mode,
            progress=progress,
            recent_sources=recent_sources[: self.MAX_RECENT_ITEMS],
            recent_results=recent_results[: self.MAX_RECENT_ITEMS],
        )

    def _string_list(self, value: Any, fallback: list[str]) -> list[str]:
        if isinstance(value, list):
            result = [str(item).strip() for item in value if str(item).strip()]
            if result:
                return result[:6]
        return fallback
