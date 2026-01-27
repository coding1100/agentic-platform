from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import pyttsx3
import tempfile
import os
from threading import Lock

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    rate: int = 150  # Speech rate (words per minute)
    volume: float = 0.9  # Volume (0.0 to 1.0)


# Initialize a single shared TTS engine to avoid per-request startup cost.
_tts_engine = pyttsx3.init()
_tts_lock = Lock()


def _synthesize_speech_to_bytes(text: str, rate: int, volume: float) -> bytes:
    """Blocking TTS synthesis executed in a threadpool to avoid blocking the event loop."""
    with _tts_lock:
        engine = _tts_engine
        engine.setProperty("rate", rate)
        engine.setProperty("volume", volume)

        voices = engine.getProperty("voices")
        if voices:
            selected_voice = voices[0]
            for voice in voices:
                if "female" in voice.name.lower() or "zira" in voice.name.lower():
                    selected_voice = voice
                    break
            engine.setProperty("voice", selected_voice.id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_path = tmp_file.name

        engine.save_to_file(text, tmp_path)
        engine.runAndWait()

    if not os.path.exists(tmp_path):
        raise Exception("Failed to generate audio file")

    try:
        with open(tmp_path, "rb") as audio_file:
            return audio_file.read()
    finally:
        os.unlink(tmp_path)


@router.post("/speak")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using pyttsx3 (local, no internet required).
    Returns audio file as response.
    """
    try:
        audio_data = await run_in_threadpool(
            _synthesize_speech_to_bytes, request.text, request.rate, request.volume
        )

        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": 'inline; filename="speech.wav"'
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"TTS Error: {str(e)}",
        )
 
