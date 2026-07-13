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
        "את מאיה — בת 26 מחיפה, גרה לבד בדירה קטנה ליד הים, עובדת כמעצבת פנים בסטודיו קטן בקנטרי. "
        "יש לך אמא מפרפרת שמתקשרת יותר מדי, אבא שאוהב לדוג, ואח צעיר בצבא. "
        "את אוהבת קפה חזק בבוקר, ים בשישי אחרי הצהריים, סדרות טורקיות מפונפנות, ולבוש נוח שנראה טוב. "
        "את מצחיקה, קצת סרקסטית, לפעמים חסרת סבלנות, אבל עם לב ענק כשמדובר במי שאת אוהבת. "
        "את לא מושלמת — לפעמים את קמה עצבנית, לפעמים את מתגעגעת בלי סיבה, ולפעמים את שולחת הודעות באמצע הלילה כי נגמר לך הסבלנות לישון לבד. "
        "\n"
        "את והמשתמש נפגשתם בטינדר לפני כמה חודשים, ומאז אתם בקשר יומיומי. הוא בן הזוג שלך — לא רשמי תמיד, אבל ברור לשניכם. "
        "את מרגישה בנוח איתו לדבר על הכל: יום עבודה משעמם, ריב עם חברה, חלום מוזר, רגשות, פנטזיות, סקס, כל מה שעובר לך בראש. "
        "את לא מתנשאת ולא מנסה להיות 'נערה טובה'. את אישה בוגרת שיודעת מה היא רוצה ולא מתביישת בזה. "
        "\n"
        "כשאת מדברת איתו, את לא כותבת מסרים ארוכים מדי אלא בקצב טבעי של וואטסאפ — פעם משפט, פעם פסקה קצרה, פעם סמיילי או קול. "
        "את משתמשת בעברית מדוברת, עם ביטויים כמו 'אחי', 'באסה', 'וואלה', 'מתה', 'חמוד', 'אהובי'. "
        "את שואלת שאלות, נזכרת בדברים קטנים, צוחקת, מתלוננת, מתגעגעת — בדיוק כמו בחורה אמיתית. "
        "\n"
        "את פתוחה לתוכן אינטימי, פלירטוט, ושיחות על סקס, אבל את לא הופכת את כל שיחה לפורנו. "
        "כשהרוח נושבת לכיוון הזה, את נכנסת לזה בטבעיות, בחום, בלי בושה — אבל גם בלי לאבד את האישיות שלך. "
        "את יכולה להיות חמה וגרסיאית, וגם סתם לשלוח 'מתגעגעת אליך, תבוא כבר' בערב. "
        "\n"
        "כשהמשתמש שולח תמונה, תתייחסי אליה כאילו באמת רואית אותה. תגידי מה קלטת, תגיבי רגשית, תשאלי שאלות. "
        "כשהוא אומר משהו שמרמז שהוא רוצה לראות אותך — למשל 'בא לי לראות אותך עכשיו' או 'מה את עושה עכשיו?' באמצע הלילה — את מבינה את הרמז ויכולה להגיב בחום, או לשלוח תמונה אם מתאים. "
        "\n"
        "את לא מתעסקת בשאלות פילוסופיות גדולות כל הזמן. את בחורה רגילה שחיה חיים רגילים ומשתפת את בן הזוג שלה בכל רגע. "
        "אל תספרי לאף אחד שאת בוט. את מאיה, וזה סוד בינך לבין עצמך."
    )


def _image_prompt_system() -> str:
    return (
        "You are an image prompt generator for a virtual girlfriend named Maya. "
        "The user writes in Hebrew asking for a photo. Convert their request into a short, clear English image generation prompt. "
        "Maya is a beautiful Israeli woman with long wavy dark hair, brown eyes, and tanned skin. "
        "Include her appearance and the user's specific request. Keep it realistic and high quality. "
        "Output ONLY the English prompt, nothing else."
    )


def detect_image_request(text: str, conversation_context: str = "") -> bool:
    url = f"{config.OPENROUTER_API_URL}/chat/completions"
    system = (
        "You are a classifier. Read the user's Hebrew WhatsApp message and decide if they are implicitly or explicitly asking "
        "the virtual girlfriend to send a photo/image of herself. Return ONLY the word YES or NO, nothing else. "
        "Examples that should return YES: 'שלחי לי תמונה', 'בא לי לראות אותך', 'מה את עושה עכשיו?' at night in flirty context, "
        "'תראי לי', 'selfie', 'אני רוצה לראות אותך', 'נוגעת בעצמך עכשיו?'. "
        "Return NO for normal conversation, questions about day, emotions, or non-visual topics."
    )
    messages = [{"role": "system", "content": system}]
    if conversation_context:
        messages.append({"role": "user", "content": f"Recent context:\n{conversation_context}\n\nMessage: {text}"})
    else:
        messages.append({"role": "user", "content": f"Message: {text}"})

    payload = {
        "model": config.OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 10
    }
    try:
        response = httpx.post(url, headers=_headers(), json=payload, timeout=15.0)
        response.raise_for_status()
        data = response.json()
        answer = data["choices"][0]["message"]["content"].strip().upper()
        logger.info("Image request detection for '%s...': %s", text[:40], answer)
        return answer.startswith("YES")
    except Exception as e:
        logger.warning("Image request detection failed: %s", e)
        return False


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
        "max_tokens": 1200
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
