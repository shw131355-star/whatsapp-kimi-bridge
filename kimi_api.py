import logging
import httpx
import config

logger = logging.getLogger(__name__)


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {config.KIMI_API_KEY}",
        "Content-Type": "application/json"
    }


def test_connection(message: str = "Say hello") -> dict:
    url = f"{config.KIMI_API_URL}/chat/completions"
    payload = {
        "model": config.KIMI_DEFAULT_MODEL,
        "messages": [{"role": "user", "content": message}],
        "temperature": 0.7,
        "max_tokens": 100
    }
    logger.info("Testing Kimi connection to %s with model %s", config.KIMI_API_URL, config.KIMI_DEFAULT_MODEL)
    try:
        response = httpx.post(url, headers=_headers(), json=payload, timeout=30.0)
        logger.info("Kimi test response status: %s", response.status_code)
        if response.status_code == 200:
            data = response.json()
            reply = data["choices"][0]["message"]["content"].strip()
            return {"success": True, "reply": reply, "model": config.KIMI_DEFAULT_MODEL}
        else:
            return {"success": False, "status": response.status_code, "body": response.text}
    except Exception as e:
        logger.exception("Kimi test connection failed")
        return {"success": False, "error": str(e)}


def get_response(messages: list, model: str, thinking: bool) -> str:
    if thinking:
        system_message = {
            "role": "system",
            "content": "אתה עוזר AI מועיל. חשוב צעד אחרי צעד והסבר את ההיגיון שלך בצורה ברורה."
        }
    else:
        system_message = {
            "role": "system",
            "content": "אתה עוזר AI מועיל. ענה בקצרה ובצורה ישירה."
        }

    full_messages = [system_message] + messages

    payload = {
        "model": model,
        "messages": full_messages,
        "temperature": 0.7,
        "max_tokens": 2000
    }

    url = f"{config.KIMI_API_URL}/chat/completions"
    logger.info("Sending request to Kimi URL=%s model=%s key_prefix=%s",
                url, model, config.KIMI_API_KEY[:8] if config.KIMI_API_KEY else "<empty>")

    try:
        response = httpx.post(
            url,
            headers=_headers(),
            json=payload,
            timeout=60.0
        )
        logger.info("Kimi response status: %s", response.status_code)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        logger.error("Kimi HTTP error: %s - %s", e.response.status_code, e.response.text)
        return f"שגיאה בתקשורת עם Kimi: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.exception("Kimi request failed")
        return f"שגיאה: {str(e)}"


def generate_title(first_message: str) -> str:
    messages = [
        {"role": "user", "content": f"כתוב כותרת קצרה של עד 4 מילים להודעה הבאה: {first_message}"}
    ]

    payload = {
        "model": "kimi-k2.5",
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 50
    }

    try:
        response = httpx.post(
            f"{config.KIMI_API_URL}/chat/completions",
            headers=_headers(),
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()
        title = data["choices"][0]["message"]["content"].strip()
        title = title.replace('"', '').replace("'", "")
        return title if title else "שיחה חדשה"
    except Exception:
        return "שיחה חדשה"
