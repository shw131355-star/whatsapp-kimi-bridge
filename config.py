import os
from typing import List

APP_NAME = "WhatsApp Kimi Bridge"
APP_VERSION = "1.2.0"

GREEN_API_URL = os.environ.get("GREEN_API_URL", "")
GREEN_API_INSTANCE_ID = os.environ.get("GREEN_API_INSTANCE_ID", "")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN", "")

KIMI_API_KEY = os.environ.get("KIMI_API_KEY", "")
KIMI_API_URL = os.environ.get("KIMI_API_URL", "https://api.moonshot.ai/v1")
KIMI_DEFAULT_MODEL = os.environ.get("KIMI_DEFAULT_MODEL", "kimi-k2.5")
KIMI_MAX_HISTORY = int(os.environ.get("KIMI_MAX_HISTORY", "20"))

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = os.environ.get("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "x-ai/grok-4.3")
OPENROUTER_MAX_HISTORY = int(os.environ.get("OPENROUTER_MAX_HISTORY", "20"))

GIRLFRIEND_PHONES = os.environ.get("GIRLFRIEND_PHONES", "")

THINKING_ENABLED_DEFAULT = os.environ.get("THINKING_ENABLED_DEFAULT", "false").lower() == "true"

ALLOWED_PHONES = os.environ.get("ALLOWED_PHONES", "")

PORT = int(os.environ.get("PORT", "8000"))


def _normalize_phone(phone: str) -> str:
    return phone.replace("+", "").replace(" ", "").replace("-", "")


def get_allowed_phones() -> List[str]:
    if not ALLOWED_PHONES:
        return []
    return [p.strip() for p in ALLOWED_PHONES.split(",") if p.strip()]


def get_girlfriend_phones() -> List[str]:
    if not GIRLFRIEND_PHONES:
        return []
    return [p.strip() for p in GIRLFRIEND_PHONES.split(",") if p.strip()]


def is_phone_allowed(phone: str) -> bool:
    allowed = get_allowed_phones()
    if not allowed:
        return True
    normalized = _normalize_phone(phone)
    return any(_normalize_phone(a) == normalized for a in allowed)


def is_girlfriend_phone(phone: str) -> bool:
    girlfriend_phones = get_girlfriend_phones()
    if not girlfriend_phones:
        return False
    normalized = _normalize_phone(phone)
    return any(_normalize_phone(g) == normalized for g in girlfriend_phones)


def _mask(value: str, visible: int = 4) -> str:
    if not value:
        return "<empty>"
    if len(value) <= visible * 2:
        return "***" + value[-visible:] if value[-visible:] else "***"
    return value[:visible] + "***" + value[-visible:]


def safe_config_log() -> dict:
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "green_api_url": GREEN_API_URL,
        "green_api_instance_id": GREEN_API_INSTANCE_ID,
        "green_api_token": _mask(GREEN_API_TOKEN),
        "kimi_api_url": KIMI_API_URL,
        "kimi_api_key": _mask(KIMI_API_KEY),
        "kimi_default_model": KIMI_DEFAULT_MODEL,
        "kimi_max_history": KIMI_MAX_HISTORY,
        "openrouter_api_url": OPENROUTER_API_URL,
        "openrouter_api_key": _mask(OPENROUTER_API_KEY),
        "openrouter_model": OPENROUTER_MODEL,
        "openrouter_max_history": OPENROUTER_MAX_HISTORY,
        "girlfriend_phones": get_girlfriend_phones(),
        "thinking_default": THINKING_ENABLED_DEFAULT,
        "allowed_phones": get_allowed_phones(),
        "port": PORT,
    }
