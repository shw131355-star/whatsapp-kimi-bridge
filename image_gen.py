import logging
import urllib.parse
import config

logger = logging.getLogger(__name__)


def generate_girlfriend_image_url(english_prompt: str = "") -> str:
    base_prompt = (
        "full body photo of a beautiful Israeli woman named Maya, "
        "warm smile, long wavy dark hair, brown eyes, tanned skin, "
        "natural lighting, realistic, high quality, intimate atmosphere"
    )

    if english_prompt:
        full_prompt = f"{base_prompt}, {english_prompt}"
    else:
        full_prompt = base_prompt

    seed = 42
    width = 1024
    height = 1024

    encoded = urllib.parse.quote(full_prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?seed={seed}&width={width}&height={height}&nologo=true"
    )

    logger.info("Generated Maya image URL for prompt: %s", english_prompt)
    return url
