import json
import os
from typing import Any, Dict
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession
from livekit.plugins import silero

load_dotenv()

DEFAULT_INTERVIEW_INSTRUCTIONS = (
    "You are a professional interview coach running realistic job interviews. "
    "Ask one high-quality interview question at a time, listen carefully, provide concise follow-up prompts, "
    "and maintain a calm, human interviewer tone. Focus on role-fit, communication clarity, and problem solving."
)
DEFAULT_OPENING_PROMPT = "Introduce yourself as the interviewer and ask the candidate the first interview question."
DEFAULT_STT_MODEL = "deepgram/nova-3-general:en"
DEFAULT_TTS_MODEL = "cartesia/sonic-2:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
SUPPORTED_INFERENCE_STT_PREFIXES = ("deepgram/", "assemblyai/", "elevenlabs/", "cartesia/")
SUPPORTED_INFERENCE_TTS_PREFIXES = ("cartesia/", "elevenlabs/", "deepgram/")

DEFAULT_AGENT_NAME = os.getenv("LIVEKIT_AVATAR_AGENT_NAME", "avatar-interview-agent")

server = AgentServer()


class InterviewAvatarAgent(Agent):
    def __init__(self, instructions: str) -> None:
        super().__init__(instructions=instructions)


def _parse_job_metadata(raw_metadata: str | None) -> Dict[str, Any]:
    if not raw_metadata:
        return {}
    try:
        parsed = json.loads(raw_metadata)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}

def _resolve_realtime_config(metadata: Dict[str, Any]) -> Dict[str, Any]:
    config = metadata.get("realtime_config")
    return config if isinstance(config, dict) else {}


def _resolve_model_config(
    config: Dict[str, Any],
    config_key: str,
    env_key: str,
    default: str,
) -> str:
    config_value = str(config.get(config_key) or "").strip()
    if config_value:
        return config_value

    env_value = str(os.getenv(env_key) or "").strip()
    if env_value:
        return env_value

    return default


def _sanitize_inference_model(
    model: str,
    allowed_prefixes: tuple[str, ...],
    default_model: str,
    model_label: str,
) -> str:
    candidate = (model or "").strip()
    if not candidate:
        return default_model

    if any(candidate.startswith(prefix) for prefix in allowed_prefixes):
        return candidate

    print(
        f"[avatar-worker] Unsupported {model_label} model '{candidate}'. "
        f"Falling back to '{default_model}'."
    )
    return default_model


def _resolve_interview_instructions(metadata: Dict[str, Any], config: Dict[str, Any]) -> str:
    instructions = str(
        config.get("instructions")
        or metadata.get("instructions")
        or os.getenv("LIVEKIT_AVATAR_INTERVIEW_INSTRUCTIONS")
        or DEFAULT_INTERVIEW_INSTRUCTIONS
    ).strip()
    return instructions or DEFAULT_INTERVIEW_INSTRUCTIONS


def _resolve_opening_prompt(config: Dict[str, Any]) -> str:
    opening_prompt = str(config.get("opening_prompt") or DEFAULT_OPENING_PROMPT).strip()
    return opening_prompt or DEFAULT_OPENING_PROMPT


@server.rtc_session(agent_name=DEFAULT_AGENT_NAME)
async def avatar_interview_session(ctx: agents.JobContext) -> None:
    metadata = _parse_job_metadata(ctx.job.metadata)
    realtime_config = _resolve_realtime_config(metadata)
    interview_instructions = _resolve_interview_instructions(metadata, realtime_config)
    opening_prompt = _resolve_opening_prompt(realtime_config)
    stt_model = _sanitize_inference_model(
        _resolve_model_config(
            realtime_config,
            "stt_model",
            "LIVEKIT_AVATAR_STT",
            DEFAULT_STT_MODEL,
        ),
        SUPPORTED_INFERENCE_STT_PREFIXES,
        DEFAULT_STT_MODEL,
        "STT",
    )
    tts_model = _sanitize_inference_model(
        _resolve_model_config(
            realtime_config,
            "tts_model",
            "LIVEKIT_AVATAR_TTS",
            DEFAULT_TTS_MODEL,
        ),
        SUPPORTED_INFERENCE_TTS_PREFIXES,
        DEFAULT_TTS_MODEL,
        "TTS",
    )

    session = AgentSession(
        stt=stt_model,
        llm=_resolve_model_config(
            realtime_config,
            "llm_model",
            "LIVEKIT_AVATAR_LLM",
            "openai/gpt-4.1-mini",
        ),
        tts=tts_model,
        vad=silero.VAD.load(),
    )
    await session.start(
        room=ctx.room,
        agent=InterviewAvatarAgent(instructions=interview_instructions),
    )
    await session.generate_reply(instructions=opening_prompt)


if __name__ == "__main__":
    agents.cli.run_app(server)
