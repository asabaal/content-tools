"""AI background image generation via SD3 Medium subprocess."""

import asyncio
import json

from src.config.defaults import (
    DEFAULT_AI_BASE_URL,
    DEFAULT_AI_MODEL,
    SD3_DEFAULT_GUIDANCE,
    SD3_DEFAULT_HEIGHT,
    SD3_DEFAULT_STEPS,
    SD3_DEFAULT_WIDTH,
    SD3_MODEL_PATH,
    SD3_PYTHON,
    SD3_SCRIPT,
    SD3_TIMEOUT,
)
from src.errors.exceptions import RendererError


async def generate_image_prompt_from_theme(theme: str) -> str:
    """Auto-generate an image background prompt from the monthly theme via Ollama."""
    import httpx

    prompt = (
        "Generate a single image generation prompt for an AI text-to-image model. "
        "The image will be used as a background for social media posts with text overlay. "
        "The image should be: abstract or atmospheric, no text, no people, no faces, "
        "soft and muted colors (not too bright), suitable for dark or light text overlay. "
        f"The monthly content theme is: '{theme}'. "
        "Output ONLY the image prompt, nothing else. Keep it under 40 words."
    )

    payload = {
        "model": DEFAULT_AI_MODEL,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {"temperature": 0.4, "top_p": 0.9},
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(f"{DEFAULT_AI_BASE_URL}/api/generate", json=payload)
        response.raise_for_status()
        result = response.json().get("response", "").strip()
        if not result:
            raise RendererError("Empty response from Ollama for image prompt generation")
        return result


async def generate_background_image(
    prompt: str,
    output_path: str,
    width: int = SD3_DEFAULT_WIDTH,
    height: int = SD3_DEFAULT_HEIGHT,
    steps: int = SD3_DEFAULT_STEPS,
    guidance: float = SD3_DEFAULT_GUIDANCE,
    seed: int | None = None,
    model_path: str | None = None,
) -> str:
    """Call SD3 via subprocess to generate a background image. Returns path to PNG file."""
    cmd = [
        SD3_PYTHON,
        SD3_SCRIPT,
        "--prompt", prompt,
        "--width", str(width),
        "--height", str(height),
        "--steps", str(steps),
        "--guidance", str(guidance),
        "--model-path", model_path or SD3_MODEL_PATH,
        "--outfile", output_path,
    ]
    if seed is not None:
        cmd.extend(["--seed", str(seed)])

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=SD3_TIMEOUT
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise RendererError(f"SD3 image generation timed out after {SD3_TIMEOUT}s")

    if proc.returncode != 0:
        stderr_msg = stderr.decode("utf-8", errors="replace").strip() if stderr else "unknown error"
        stdout_msg = stdout.decode("utf-8", errors="replace").strip() if stdout else ""
        raise RendererError(f"SD3 failed (exit {proc.returncode}): {stderr_msg} {stdout_msg}")

    try:
        data = json.loads(stdout.decode("utf-8").strip())
    except json.JSONDecodeError:
        raise RendererError(f"SD3 returned non-JSON output: {stdout.decode('utf-8', errors='replace').strip()}")

    if data.get("status") != "ok":
        raise RendererError(f"SD3 error: {data.get('message', 'unknown')}")

    return data["path"]
