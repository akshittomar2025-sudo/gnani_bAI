import os
import base64
import mimetypes
from urllib.parse import urlparse

import httpx
from fastmcp import FastMCP

GNANI_API_KEY = os.environ.get("GNANI_API_KEY")
GNANI_STT_URL = "https://api.vachana.ai/stt/v3"

mcp = FastMCP(
    "Gnani bAI",
    instructions=(
        "Speech-to-text tools for bAI. Use transcribe_cook_audio when a cook "
        "voice-note URL is available. Return the transcript to bAI; bAI, not "
        "Gnani, decides what the household state means."
    ),
)

def _filename_from_url(url: str) -> str:
    path = urlparse(url).path
    name = path.rsplit("/", 1)[-1] if path else ""
    return name or "cook_audio.wav"

async def _load_audio(audio_url: str):
    if audio_url.startswith("data:"):
        header, payload = audio_url.split(",", 1)
        content_type = header.split(";")[0].replace("data:", "") or "audio/wav"
        audio_bytes = base64.b64decode(payload)
        ext = mimetypes.guess_extension(content_type) or ".wav"
        return audio_bytes, f"cook_audio{ext}", content_type

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(audio_url)
        response.raise_for_status()
        audio_bytes = response.content
        content_type = response.headers.get("content-type", "").split(";")[0]
        filename = _filename_from_url(str(response.url))
        if not content_type.startswith("audio/"):
            guessed, _ = mimetypes.guess_type(filename)
            content_type = guessed or "application/octet-stream"
        return audio_bytes, filename, content_type

@mcp.tool
async def transcribe_cook_audio(
    audio_url: str,
    language_code: str = "en-IN",
    output_format: str = "transcribe",
) -> dict:
    """
    Transcribe a short cook voice note using Gnani Speech-to-Text.

    Args:
        audio_url: Public HTTPS URL of a short audio file (WAV, MP3, OGG,
                   FLAC, AAC or M4A), or a data:audio/...;base64 URL.
        language_code: Gnani language code. Use en-IN for Latin/English output
                       or hi-IN for Hindi/Devanagari output.
        output_format: 'transcribe' for ITN-normalized output or 'verbatim'
                       for raw spoken-form output.
    """
    if not GNANI_API_KEY:
        return {"success": False, "error": "GNANI_API_KEY is not configured on the MCP server."}

    allowed_languages = {
        "bn-IN", "en-IN", "gu-IN", "hi-IN", "kn-IN",
        "ml-IN", "mr-IN", "pa-IN", "ta-IN", "te-IN"
    }
    if language_code not in allowed_languages:
        return {"success": False, "error": f"Unsupported language_code: {language_code}"}

    if output_format not in {"transcribe", "verbatim"}:
        return {"success": False, "error": "output_format must be 'transcribe' or 'verbatim'"}

    try:
        audio_bytes, filename, content_type = await _load_audio(audio_url)

        headers = {"X-API-Key-ID": GNANI_API_KEY}
        files = {"audio_file": (filename, audio_bytes, content_type)}
        data = {"language_code": language_code, "format": output_format}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                GNANI_STT_URL,
                headers=headers,
                files=files,
                data=data,
            )

        try:
            payload = response.json()
        except Exception:
            payload = {"raw_response": response.text}

        if response.status_code >= 400:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": payload,
            }

        return {
            "success": bool(payload.get("success", True)),
            "transcript": payload.get("transcript", ""),
            "request_id": payload.get("request_id"),
            "language_code": language_code,
        }

    except httpx.HTTPStatusError as exc:
        return {
            "success": False,
            "error": f"Could not download audio: HTTP {exc.response.status_code}",
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"{type(exc).__name__}: {exc}",
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
        path="/mcp",
    )
