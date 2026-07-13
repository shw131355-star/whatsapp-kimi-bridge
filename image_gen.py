import logging
import random
import urllib.parse
import config

logger = logging.getLogger(__name__)


def generate_girlfriend_image_url(english_prompt: str = "", seed: int = None) -> str:
    base_prompt = (
        "attractive young Israeli woman age 19, gentle feminine features, "
        "smooth olive skin, warm brown eyes, dark brown wavy hair, "
        "subtle natural makeup, friendly warm expression, "
        "pretty but normal girl next door look, not a model, "
        "natural bedroom lighting, realistic skin texture, casual selfie style, "
        "same face in every photo, consistent facial features"
    )

    if english_prompt:
        full_prompt = f"{base_prompt}, {english_prompt}"
    else:
        full_prompt = base_prompt

    if seed is None:
        seed = random.randint(1, 1000000)
    width = 1024
    height = 1024

    encoded = urllib.parse.quote(full_prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?seed={seed}&width={width}&height={height}&nologo=true"
    )

    logger.info("Generated Maya image URL for prompt: %s (seed=%s)", english_prompt, seed)
    return url
