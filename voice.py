import base64
import io
import logging
import tempfile

import httpx
import edge_tts
import config

logger = logging.getLogger(__name__)


async def transcribe_audio(audio_url: str) -> str:
    """Try to transcribe an audio message using OpenRouter file input."""
    if not audio_url:
        return ""

    try:
        audio_bytes = httpx.get(audio_url, timeout=30.0).content
        if not audio_bytes:
            return ""
    except Exception as e:
        logger.warning("Failed to download audio: %s", e)
        return ""

    encoded = base64.b64encode(audio_bytes).decode("utf-8")
    url = f"{config.OPENROUTER_API_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://whatsapp-kimi-bridge.onrender.com",
        "X-Title": "WhatsApp Kimi Bridge"
    }
    payload = {
        "model": config.OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Transcribe this Hebrew audio message to text. Output ONLY the transcribed text, nothing else."},
                    {"type": "input_audio", "input_audio": {"data": encoded, "format": "ogg"}}
                ]
            }
        ],
        "temperature": 0.0,
        "max_tokens": 500
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=60.0)
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        logger.info("Transcribed audio: %s", text[:100])
        return text
    except Exception as e:
        logger.warning("Audio transcription failed: %s", e)
        return ""


async def text_to_speech(text: str) -> bytes:
    """Convert Hebrew text to speech using Edge TTS."""
    voice = "he-IL-HilaNeural"
    communicate = edge_tts.Communicate(text, voice)
    output = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            output.write(chunk["data"])
    return output.getvalue()
