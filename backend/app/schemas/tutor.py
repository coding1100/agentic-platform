from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TutorAcademicLevel(str, Enum):
    HIGH_SCHOOL = "high_school"
    COLLEGE = "college"
    PHD = "phd"


class TutorAction(str, Enum):
    ASK_QUESTION = "ask_question"
    UPLOAD_NOTES = "upload_notes"
    PRACTICE = "practice"


class TutorLearningMode(str, Enum):
    PERSONALIZED_LEARNING = "personalized_learning"
    ASSIGNMENT_ASSISTANT = "assignment_assistant"
    PRACTICE_QUIZ_GENERATOR = "practice_quiz_generator"
    CONCEPT_SIMPLIFIER = "concept_simplifier"
    NOTES_SUMMARY = "notes_summary"
    EXAM_MODE = "exam_mode"
    SOURCE_BASED_LEARNING = "source_based_learning"


class TutorSourceKind(str, Enum):
    NOTES = "notes"
    PDF = "pdf"
    BOOK = "book"


class TutorPracticeFormat(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    MIXED = "mixed"


class TutorRecentSource(BaseModel):
    name: str
    kind: TutorSourceKind
    char_count: int = Field(default=0, ge=0)
    added_at: datetime


class TutorRecentResult(BaseModel):
    action: TutorAction
    learning_mode: TutorLearningMode
    title: str
    score: Optional[int] = Field(default=None, ge=0, le=100)
    weak_topics: List[str] = Field(default_factory=list)
    created_at: datetime


class TutorProgressSummary(BaseModel):
    sessions_completed: int = Field(default=0, ge=0)
    practice_sessions_attempted: int = Field(default=0, ge=0)
    practice_sessions_completed: int = Field(default=0, ge=0)
    source_sessions: int = Field(default=0, ge=0)
    average_score: Optional[float] = Field(default=None, ge=0, le=100)
    weak_topics: List[str] = Field(default_factory=list)
    mastery_by_topic: Dict[str, float] = Field(default_factory=dict)
    recent_activity: List[str] = Field(default_factory=list)
    next_recommended_action: Optional[str] = None


class TutorWorkspaceState(BaseModel):
    subject: str = ""
    academic_level: Optional[TutorAcademicLevel] = None
    learner_name: Optional[str] = None
    selected_action: Optional[TutorAction] = None
    selected_mode: Optional[TutorLearningMode] = None
    progress: TutorProgressSummary = Field(default_factory=TutorProgressSummary)
    recent_sources: List[TutorRecentSource] = Field(default_factory=list)
    recent_results: List[TutorRecentResult] = Field(default_factory=list)


class TutorPracticeOption(BaseModel):
    id: str
    text: str


class TutorPracticeQuestion(BaseModel):
    id: str
    prompt: str
    type: TutorPracticeFormat
    concept: Optional[str] = None
    options: List[TutorPracticeOption] = Field(default_factory=list)
    answer: Optional[str] = None
    explanation: Optional[str] = None


class TutorPracticeSet(BaseModel):
    title: str
    instructions: str
    questions: List[TutorPracticeQuestion] = Field(default_factory=list)


class TutorExecuteRequest(BaseModel):
    action: TutorAction
    learning_mode: TutorLearningMode
    subject: str = Field(min_length=1, max_length=200)
    academic_level: TutorAcademicLevel
    learner_name: Optional[str] = Field(default=None, max_length=200)
    prompt: Optional[str] = Field(default=None, max_length=12000)
    source_text: Optional[str] = Field(default=None, max_length=50000)
    source_name: Optional[str] = Field(default=None, max_length=255)
    source_kind: Optional[TutorSourceKind] = None
    question_count: Optional[int] = Field(default=None, ge=1, le=10)
    practice_format: Optional[TutorPracticeFormat] = None


class TutorExecuteResponse(BaseModel):
    action: TutorAction
    learning_mode: TutorLearningMode
    subject: str
    academic_level: TutorAcademicLevel
    learner_name: Optional[str] = None
    summary: Optional[str] = None
    explanation: str
    steps: List[str] = Field(default_factory=list)
    practice_set: TutorPracticeSet
    key_concepts: List[str] = Field(default_factory=list)
    progress_snapshot: TutorProgressSummary
    suggested_next_actions: List[str] = Field(default_factory=list)
