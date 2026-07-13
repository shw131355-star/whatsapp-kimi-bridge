import os
from typing import List

APP_NAME = "WhatsApp Kimi Bridge"
APP_VERSION = "1.0.0"

GREEN_API_URL = os.environ.get("GREEN_API_URL", "")
GREEN_API_INSTANCE_ID = os.environ.get("GREEN_API_INSTANCE_ID", "")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN", "")

KIMI_API_KEY = os.environ.get("KIMI_API_KEY", "")
KIMI_API_URL = os.environ.get("KIMI_API_URL", "https://api.moonshot.cn/v1")
KIMI_DEFAULT_MODEL = os.environ.get("KIMI_DEFAULT_MODEL", "kimi-k2")
KIMI_MAX_HISTORY = int(os.environ.get("KIMI_MAX_HISTORY", "50"))

THINKING_ENABLED_DEFAULT = os.environ.get("THINKING_ENABLED_DEFAULT", "false").lower() == "true"

ALLOWED_PHONES = os.environ.get("ALLOWED_PHONES", "")

PORT = int(os.environ.get("PORT", "8000"))


def get_allowed_phones() -> List[str]:
    if not ALLOWED_PHONES:
        return []
    return [p.strip() for p in ALLOWED_PHONES.split(",") if p.strip()]


def is_phone_allowed(phone: str) -> bool:
    allowed = get_allowed_phones()
    if not allowed:
        return True
    normalized = phone.replace("+", "").replace(" ", "").replace("-", "")
    return any(a.replace("+", "").replace(" ", "").replace("-", "") == normalized for a in allowed)
