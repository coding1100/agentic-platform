from app.services.avatar_interview_worker import (
    DEFAULT_STT_MODEL,
    DEFAULT_TTS_MODEL,
    SUPPORTED_INFERENCE_STT_PREFIXES,
    SUPPORTED_INFERENCE_TTS_PREFIXES,
    _sanitize_inference_model,
)


def test_sanitize_inference_model_accepts_supported_prefix() -> None:
    value = _sanitize_inference_model(
        "deepgram/nova-3-general:en",
        SUPPORTED_INFERENCE_STT_PREFIXES,
        DEFAULT_STT_MODEL,
        "STT",
    )
    assert value == "deepgram/nova-3-general:en"


def test_sanitize_inference_model_falls_back_for_unsupported_provider() -> None:
    value = _sanitize_inference_model(
        "openai/gpt-4o-mini-transcribe",
        SUPPORTED_INFERENCE_STT_PREFIXES,
        DEFAULT_STT_MODEL,
        "STT",
    )
    assert value == DEFAULT_STT_MODEL


def test_sanitize_inference_model_falls_back_for_unsupported_tts_provider() -> None:
    value = _sanitize_inference_model(
        "openai/gpt-4o-mini-tts:alloy",
        SUPPORTED_INFERENCE_TTS_PREFIXES,
        DEFAULT_TTS_MODEL,
        "TTS",
    )
    assert value == DEFAULT_TTS_MODEL
