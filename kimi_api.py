import httpx
import config


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {config.KIMI_API_KEY}",
        "Content-Type": "application/json"
    }


def get_response(messages: list, model: str, thinking: bool) -> str:
    if thinking:
        system_message = {
            "role": "system",
            "content": "אתה עוזר AI מועיל. חשוב צעד אחר צעד והסבר את ההיגיון שלך בצורה ברורה."
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

    try:
        response = httpx.post(
            f"{config.KIMI_API_URL}/chat/completions",
            headers=_headers(),
            json=payload,
            timeout=60.0
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        return f"שגיאה בתקשורת עם Kimi: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"שגיאה: {str(e)}"


def generate_title(first_message: str) -> str:
    messages = [
        {"role": "user", "content": f"כתוב כותרת קצרה של עד 4 מילים להודעה הבאה: {first_message}"}
    ]

    payload = {
        "model": "kimi-k2",
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
