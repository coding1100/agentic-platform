from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import pyttsx3
import io
import tempfile
import os

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    rate: int = 150  # Speech rate (words per minute)
    volume: float = 0.9  # Volume (0.0 to 1.0)


@router.post("/speak")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using pyttsx3 (local, no internet required).
    Returns audio file as response.
    """
    try:
        # Initialize TTS engine
        engine = pyttsx3.init()
        
        # Set properties
        engine.setProperty('rate', request.rate)
        engine.setProperty('volume', request.volume)
        
        # Try to set a better voice (if available)
        voices = engine.getProperty('voices')
        if voices:
            # Prefer female voice if available, otherwise use first available
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            else:
                engine.setProperty('voice', voices[0].id)
        
        # Save to temporary file (pyttsx3 saves as WAV on most systems)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_path = tmp_file.name
        
        # Generate speech and save to file
        engine.save_to_file(request.text, tmp_path)
        engine.runAndWait()
        
        # Wait a moment for file to be written
        import time
        time.sleep(0.5)
        
        # Read the generated audio file
        if os.path.exists(tmp_path):
            with open(tmp_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            return Response(
                content=audio_data,
                media_type="audio/wav",
                headers={
                    "Content-Disposition": f'inline; filename="speech.wav"'
                }
            )
        else:
            raise Exception("Failed to generate audio file")
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"TTS Error: {str(e)}"
        )

