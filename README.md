# WhatsApp Kimi Bridge

גשר שמחבר בין WhatsApp (דרך Green API) לבין Kimi API של Moonshot AI ול-OpenRouter.

## יכולות

- קבלת ושליחת הודעות בוואטסאפ.
- שני בוטים שונים לפי מספר טלפון:
  - **Kimi** — עוזר AI כללי (Moonshot AI).
  - **נעמה** — חברה וירטואלית חמה ופתוחה (דרך OpenRouter).
- קבלת תמונות מהמשתמש ותיאור פלירטטי בתשובה.
- פקודות לניהול שיחות.
- הגבלה למספרי טלפון מורשים בלבד.
- שמירת היסטוריית שיחות ב-SQLite.

## פקודות בוט

- `/new` — פתיחת שיחה חדשה
- `/list` — רשימת השיחות האחרונות
- `/switch <מספר>` — מעבר לשיחה אחרת
- `/model` — הצגת המודל הנוכחי (רק ב-Kimi)
- `/model <שם>` — החלפת מודל (רק ב-Kimi)
- `/thinking on/off` — הפעלה/כיבוי מצב חשיבה (רק ב-Kimi)
- `/photo` — נעמה שולחת תמונה (רק בשיחה עם נעמה)
- `/photo <תיאור>` — תמונה בסגנון ספציפי
- `/help` — רשימת פקודות

## משתני סביבה

| משתנה | תיאור |
|-------|-------|
| `GREEN_API_URL` | כתובת ה-API של Green API (למשל `https://7107.api.greenapi.com`) |
| `GREEN_API_INSTANCE_ID` | מספר ה-instance ב-Green API |
| `GREEN_API_TOKEN` | ה-token של ה-instance |
| `KIMI_API_KEY` | מפתח API של Kimi/Moonshot |
| `KIMI_API_URL` | כתובת Kimi API (ברירת מחדל: `https://api.moonshot.ai/v1`) |
| `KIMI_DEFAULT_MODEL` | מודל ברירת מחדל ל-Kimi (ברירת מחדל: `kimi-k2.5`) |
| `OPENROUTER_API_KEY` | מפתח API של OpenRouter לחברה הוירטואלית |
| `OPENROUTER_MODEL` | מודל OpenRouter (ברירת מחדל: `meta-llama/llama-3.2-90b-vision-instruct`) |
| `ALLOWED_PHONES` | רשימת מספרי טלפון מורשים, מופרדים בפסיקים (ריק = הכל מורשה) |
| `GIRLFRIEND_PHONES` | מספרי טלפון שמופעלים כחברה וירטואלית (מופרדים בפסיקים) |

## הגדרת ניתוב בין בוטים

כל המספרים ב-`ALLOWED_PHONES` יכולים לדבר עם הבוט.

- מספרים שרשומים ב-`GIRLFRIEND_PHONES` → יקבלו את **נעמה** מ-OpenRouter.
- כל שאר המספרים המורשים → יקבלו את **Kimi**.

## פריסה ב-Render

1. חברו את הריפו ב-GitHub ל-Render.
2. צרו Web Service חדש מהריפו הזה.
3. הגדירו את משתני הסביבה בלשונית Environment.
4. אחרי הפריסה, העתיקו את כתובת ה-URL הציבורית של השירות.
5. בקונסולה של Green API, הגדירו את ה-webhook URL ל-`https://<your-render-url>/webhook`.

## הרצה מקומית

```bash
pip install -r requirements.txt
export GREEN_API_URL=...
export GREEN_API_INSTANCE_ID=...
export GREEN_API_TOKEN=...
export KIMI_API_KEY=...
export OPENROUTER_API_KEY=...
export ALLOWED_PHONES=...
export GIRLFRIEND_PHONES=...
uvicorn main:app --reload
```
