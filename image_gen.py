import base64
import logging
import httpx
import config

logger = logging.getLogger(__name__)


IMAGE_MODEL = "google/gemini-2.5-flash-image"


def _base_appearance() -> str:
    return (
        "Maya, a pretty 19 year old Israeli girl, "
        "dark brown wavy shoulder-length hair, warm brown eyes, olive skin, "
        "soft feminine features, natural light makeup, warm friendly expression, "
        "normal girl next door look, not a model"
    )


def generate_girlfriend_image_url(english_prompt: str = "", seed: int = None) -> str:
    """Generate an image via OpenRouter Gemini Flash Image and return a data URL."""
    base = _base_appearance()

    if english_prompt:
        full_prompt = (
            f"Realistic casual phone selfie of {base}, "
            f"{english_prompt}, natural home lighting, no filter, "
            f"authentic Israeli home interior"
        )
    else:
        full_prompt = (
            f"Realistic casual phone selfie of {base}, "
            f"in her bedroom, natural home lighting, no filter, "
            f"authentic Israeli home interior"
        )

    logger.info("Generating Gemini image for prompt: %s", english_prompt)

    url = f"{config.OPENROUTER_API_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://whatsapp-kimi-bridge.onrender.com",
        "X-Title": "WhatsApp Kimi Bridge"
    }
    payload = {
        "model": IMAGE_MODEL,
        "messages": [{"role": "user", "content": full_prompt}]
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=120.0)
        response.raise_for_status()
        data = response.json()
        message = data["choices"][0]["message"]

        if message.get("images"):
            image_data = message["images"][0]["image_url"]["url"]
            logger.info("Gemini image generated successfully")
            return image_data

        # If no image returned, log the refusal/content
        logger.warning("Gemini returned no image. Content: %s", message.get("content", "")[:200])
        return ""
    except Exception as e:
        logger.exception("Gemini image generation failed")
        return ""


def image_url_to_bytes(image_url: str) -> bytes:
    if image_url.startswith("data:image"):
        b64 = image_url.split(",", 1)[1]
        return base64.b64decode(b64)
    return httpx.get(image_url, timeout=60.0).content
