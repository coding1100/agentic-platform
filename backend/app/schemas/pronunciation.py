from pydantic import BaseModel
from typing import Optional


class PronunciationAssessmentRequest(BaseModel):
    word_or_phrase: str
    user_transcript: str
    language: str
    target_language_code: Optional[str] = None  # e.g., 'es-ES' for Spanish


class PronunciationAssessmentResponse(BaseModel):
    overall_score: int  # 0-100
    accuracy_score: int  # 0-100
    fluency_score: int  # 0-100
    intonation_score: int  # 0-100
    stress_score: int  # 0-100
    clarity_score: int  # 0-100
    feedback: str
    suggestions: list[str]
    correct_pronunciation: str
    user_pronunciation: str
    phonetic_comparison: Optional[str] = None





