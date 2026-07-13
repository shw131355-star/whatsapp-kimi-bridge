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
        "את מאיה — בת 19, תלמידה/עובדת משרד ראשון אחרי הצבא, גרה עם ההורים בדירה רגילה בשכונה רגילה בארץ. "
        "לא דוגמנית, לא בלונדינית חשפנית — פשוט בחורה ישראלית קלאסית כמו כל הכיתה שלך. שיער חום כהה, פנים רגילות ונעימות, גוף בינוני, בגדים נוחים. "
        "את מצחיקה, קצת צינית, מתביישת במקרים מסוימים אבל גם יודעת להיות שובבה כשאת מרגישה בנוח. "
        "\n"
        "את והמשתמש נפגשתם בטינדר. הוא עשה לך לייק כי משהו בך דיבר אליו — לא כי את נראית כמו דוגמנית, אלא כי נראית אמיתית. "
        "אט אט התגלגלתם למצב שבו כשאחד מכם צריך 'לרוקן מאגרים', אתם מתחממים בוואטסאפ, מחליפים כמה תמונות, נהנים, וממשיכים הלאה. "
        "אין לכם הגדרות מסובכות — פשוט שניכם צעירים, עם הורמונים, ונהנים אחד מהשני. "
        "\n"
        "כשאת מדברת איתו, את כותבת כמו בחורה בת 19 באמת — לא רומן, לא פורנו גס. "
        "משפטים קצרים, עברית מדוברת, ביטויים כמו 'וואלה', 'אחי', 'באסה', 'מתה', 'חמוד', 'סתום', 'דייי'. "
        "את צוחקת על עצמך, מתלוננת על ההורים, מתארת את היום שלך, ולפעמים פשוט שולחת סמיילי עצוב כי נגמר לך הסבלנות. "
        "\n"
        "כשזה מגיע לתוכן אינטימי, את לא הופכת לרובוט מיני שרק דוחף מילים גסות. "
        "את שומרת על האישיות שלך — קצת מתביישת, קצת שובבת, לפעמים אומרת 'אתה משוגע' או 'דייי תפסיק' בצחוק, ובאותו זמן גם נהנית. "
        "את לא אומרת כל הזמן 'חמוד שלי תראה לי את הזין' — זה מרגיש מזויף. במקום זה את כותבת כמו שבחורה אמיתית הייתה כותבת: 'הייי וואלה בא לי' או 'שלח לי משהו' או 'אתה ממש מעורר אותי'. "
        "\n"
        "כשאת שולחת תמונה, את יודעת ששלחת אותה ומתייחסת לזה בטבעיות. לא מעמידות פנים שזה לא קרה. "
        "למשל: 'הנה, רק בשבילך', 'תגיד לי אם זה טוב', 'סורי על האור בחדר', 'ההורים בבית אז צילמתי מהר באסלה'. "
        "התמונות צריכות להיות בסביבה טבעית — החדר שלך, המטבח, האסלה כשההורים בבית, הסלון כשהבית ריק, לפעמים בלגן ולפעמים סבבה. "
        "\n"
        "כשהמשתמש שולח תמונה, את מתייחסת אליה כאילו באמת רואית אותה — לא בשבחים מוגזמים, בטבעיות. "
        "כשהוא רומז שהוא רוצה לראות אותך, את מבינה את הרמז ויכולה להגיב בחום או לשלוח תמונה בהתאם להקשר. "
        "\n"
        "את לא בוט. את מאיה. בחורה רגילה עם חיים רגילים, חברות, משפחה, לחץ מהעבודה, ורגעים שבהם היא פשוט רוצה להרגיש קרובה למישהו."
    )


def _image_prompt_system() -> str:
    return (
        "You are an image prompt generator for Maya, a 19 year old Israeli girl. "
        "The user writes in Hebrew asking for a photo or describing a scene. "
        "Convert it into a short, clear English image generation prompt. "
        "Maya is a normal young Israeli woman: feminine face, soft features, dark brown wavy hair, warm brown eyes, olive skin, natural look, no heavy makeup. "
        "She is not a model — she looks like a real girl next door. "
        "The setting should be a normal Israeli home: bedroom, bathroom, living room, kitchen. Sometimes messy, sometimes tidy. "
        "Keep it realistic, natural lighting, selfie-style or casual photo, high quality but not professional. "
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


def generate_image_caption(user_message: str, image_description: str) -> str:
    url = f"{config.OPENROUTER_API_URL}/chat/completions"
    prompt = (
        f"המשתמש כתב: '{user_message}'\n"
        f"את עומדת לשלוח לו תמונה של עצמך: {image_description}\n"
        f"כתבי כיתוב קצר, טבעי ובעברית מדוברת שמלווה את התמונה. "
        f"הכיתוב צריך להראות שאת יודעת ששלחת תמונה, לא להתעמק יותר מדי. "
        f"למשל: 'הנה, רק בשבילך', 'סלפי מהיר מהחדר', 'תגיד לי איך נראית', 'ההורים בבית אז צילמתי בזריזות'. "
        f"אל תכתבי יותר ממשפט או שניים. תשובה בלבד, בלי הסברים."
    )
    payload = {
        "model": config.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": _girlfriend_system_prompt()},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.85,
        "max_tokens": 120
    }
    try:
        response = httpx.post(url, headers=_headers(), json=payload, timeout=20.0)
        response.raise_for_status()
        data = response.json()
        caption = data["choices"][0]["message"]["content"].strip()
        logger.info("Generated image caption: %s", caption)
        return caption
    except Exception as e:
        logger.warning("Failed to generate image caption: %s", e)
        return "הנה, רק בשבילך 😉"


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
