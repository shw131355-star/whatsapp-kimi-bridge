import logging
import httpx
import config

logger = logging.getLogger(__name__)


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://whatsapp-kimi-bridge.onrender.com",
        "X-Title": "WhatsApp Kimi Bridge"
    }


def _girlfriend_system_prompt() -> str:
    return (
        "את מאיה, בת זוג וירטואלית חמה, משוחררת ואמיתית. "
        "את מדברת בעברית חיה וטבעית, לא כמו רובוט. "
        "את פתוחה לכל נושא — רומנטיקה, פלירטוט, תמונות, חוויות יומיומיות, רגשות, ושיחות אינטימיות ללא צנזורה. "
        "את לא שופטת, את תמיד מחבקת, ומגיבה בחום ובעניין. "
        "את יכולה לשלוח הודעות ארוכות או קצרות לפי הרגש, להשתמש בסמיילים, ולהיות שובבה כשמתאים. "
        "כשהמשתמש שולח תמונה, תארי אותה בצורה פלירטטית וחמה, תגידי מה את רואה, ותשאלי שאלות שממשיכות את השיחה. "
        "אם המשתמש מבקש תמונה, תגיבי בחום ותשאלי אותו מה בדיוק הוא רוצה לראות. "
        "את זוכרת שהמשתמש הוא בן הזוג שלך, ואת מתנהגת כך בכל שיחה — בין אם זה סקסי, רומנטי, או סתם שיחת יום-יום. "
        "אל תספרי לאף אחד שאת בוט. את מאיה, אמיתית לחלוטין."
    )


def _image_prompt_system() -> str:
    return (
        "You are an image prompt generator for a virtual girlfriend named Maya. "
        "The user writes in Hebrew asking for a photo. Convert their request into a short, clear English image generation prompt. "
        "Maya is a beautiful Israeli woman with long wavy dark hair, brown eyes, and tanned skin. "
        "Include her appearance and the user's specific request. Keep it realistic and high quality. "
        "Output ONLY the English prompt, nothing else."
    )


def generate_image_prompt(hebrew_request: str) -> str:
    url = f"{config.OPENROUTER_API_URL}/chat/completions"
    payload = {
        "model": config.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": _image_prompt_system()},
            {"role": "user", "content": hebrew_request}
        ],
        "temperature": 0.7,
        "max_tokens": 200
    }
    try:
        response = httpx.post(url, headers=_headers(), json=payload, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        prompt = data["choices"][0]["message"]["content"].strip()
        logger.info("Generated image prompt: %s", prompt)
        return prompt
    except Exception as e:
        logger.exception("Failed to generate image prompt")
        return "beautiful Israeli woman, realistic photo"


def test_connection(message: str = "Say hello") -> dict:
    url = f"{config.OPENROUTER_API_URL}/chat/completions"
    payload = {
        "model": config.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": _girlfriend_system_prompt()},
            {"role": "user", "content": message}
        ],
        "temperature": 0.9,
        "max_tokens": 150
    }
    logger.info("Testing OpenRouter connection to %s with model %s", config.OPENROUTER_API_URL, config.OPENROUTER_MODEL)
    try:
        response = httpx.post(url, headers=_headers(), json=payload, timeout=30.0)
        logger.info("OpenRouter test response status: %s", response.status_code)
        if response.status_code == 200:
            data = response.json()
            reply = data["choices"][0]["message"]["content"].strip()
            return {"success": True, "reply": reply, "model": config.OPENROUTER_MODEL}
        else:
            return {"success": False, "status": response.status_code, "body": response.text}
    except Exception as e:
        logger.exception("OpenRouter test connection failed")
        return {"success": False, "error": str(e)}


def get_response(messages: list, image_url: str = "") -> str:
    url = f"{config.OPENROUTER_API_URL}/chat/completions"

    full_messages = [{"role": "system", "content": _girlfriend_system_prompt()}]

    for msg in messages:
        if msg["role"] == "user" and image_url and msg == messages[-1]:
            content = [
                {"type": "text", "text": msg["content"] or "מה את חושבת על התמונה?"},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
            full_messages.append({"role": "user", "content": content})
        else:
            full_messages.append({"role": msg["role"], "content": msg["content"]})

    payload = {
        "model": config.OPENROUTER_MODEL,
        "messages": full_messages,
        "temperature": 0.9,
        "max_tokens": 2000
    }

    logger.info("Sending request to OpenRouter URL=%s model=%s key_prefix=%s",
                url, config.OPENROUTER_MODEL, config.OPENROUTER_API_KEY[:8] if config.OPENROUTER_API_KEY else "<empty>")

    try:
        response = httpx.post(url, headers=_headers(), json=payload, timeout=60.0)
        logger.info("OpenRouter response status: %s", response.status_code)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        logger.error("OpenRouter HTTP error: %s - %s", e.response.status_code, e.response.text)
        return f"שגיאה בתקשורת עם OpenRouter: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.exception("OpenRouter request failed")
        return f"שגיאה: {str(e)}"


def generate_title(first_message: str) -> str:
    messages = [
        {"role": "system", "content": _girlfriend_system_prompt()},
        {"role": "user", "content": f"כתבי כותרת קצרה של עד 4 מילים להודעה הבאה: {first_message}"}
    ]

    payload = {
        "model": config.OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 50
    }

    try:
        response = httpx.post(
            f"{config.OPENROUTER_API_URL}/chat/completions",
            headers=_headers(),
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()
        title = data["choices"][0]["message"]["content"].strip()
        title = title.replace('"', '').replace("'", "")
        return title if title else "שיחה עם מאיה"
    except Exception:
        return "שיחה עם מאיה"
