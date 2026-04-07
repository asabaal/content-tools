"""Background music generation via ACE-Step subprocess."""

import json
import subprocess

from src.config.defaults import (
    ACE_STEP_DEFAULT_GUIDANCE,
    ACE_STEP_DEFAULT_STEPS,
    ACE_STEP_PYTHON,
    ACE_STEP_SCRIPT,
    ACE_STEP_TAIL_MAX,
    ACE_STEP_TAIL_RATIO,
    ACE_STEP_TTS_DELAY,
    ACE_STEP_TIMEOUT,
    DEFAULT_AI_BASE_URL,
    DEFAULT_AI_MODEL,
)
from src.errors.exceptions import RendererError


def calculate_music_duration(max_tts_duration: float) -> float:
    tail = min(ACE_STEP_TAIL_MAX, max_tts_duration * ACE_STEP_TAIL_RATIO)
    return ACE_STEP_TTS_DELAY + max_tts_duration + tail


def calculate_slot_video_duration(tts_duration: float) -> float:
    tail = min(ACE_STEP_TAIL_MAX, tts_duration * ACE_STEP_TAIL_RATIO)
    return ACE_STEP_TTS_DELAY + tts_duration + tail


async def generate_music_prompt_from_theme(theme: str) -> str:
    """Auto-generate a background music prompt from the monthly theme via Ollama."""
    import httpx

    prompt = (
        "Generate a single music prompt for AI background music generation. "
        "The prompt should describe mood, instruments, tempo, and atmosphere. "
        "It must be instrumental (no vocals, no percussion). "
        f"The monthly content theme is: '{theme}'. "
        "Output ONLY the music prompt, nothing else. Keep it under 30 words."
    )

    payload = {
        "model": DEFAULT_AI_MODEL,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {"temperature": 0.3, "top_p": 0.9},
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(f"{DEFAULT_AI_BASE_URL}/api/generate", json=payload)
        response.raise_for_status()
        result = response.json().get("response", "").strip()
        if not result:
            raise RendererError("Empty response from Ollama for music prompt generation")
        return result


def generate_background_music(
    prompt: str,
    duration: float,
    output_path: str,
    steps: int = ACE_STEP_DEFAULT_STEPS,
    guidance: float = ACE_STEP_DEFAULT_GUIDANCE,
    seed: int | None = None,
) -> str:
    """Call ACE-Step via subprocess. Returns path to WAV file."""
    cmd = [
        ACE_STEP_PYTHON,
        ACE_STEP_SCRIPT,
        "--prompt", prompt,
        "--duration", str(duration),
        "--steps", str(steps),
        "--guidance", str(guidance),
        "--outfile", output_path,
    ]
    if seed is not None:
        cmd.extend(["--seed", str(seed)])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=ACE_STEP_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        raise RendererError(f"ACE-Step timed out after {ACE_STEP_TIMEOUT}s")

    if result.returncode != 0:
        stderr_msg = result.stderr.strip() if result.stderr else "unknown error"
        stdout_msg = result.stdout.strip() if result.stdout else ""
        raise RendererError(f"ACE-Step failed (exit {result.returncode}): {stderr_msg} {stdout_msg}")

    try:
        data = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        raise RendererError(f"ACE-Step returned non-JSON output: {result.stdout.strip()}")

    if data.get("status") != "ok":
        raise RendererError(f"ACE-Step error: {data.get('message', 'unknown')}")

    return data["path"]
