# WhatsApp Kimi Bridge

גשר שמחבר בין WhatsApp (דרך Green API) לבין Kimi API של Moonshot AI.

## יכולות

- קבלת ושליחת הודעות בוואטסאפ.
- שיחה עם Kimi API דרך הודעות טקסט.
- פקודות לניהול שיחות, מודלים, ומצב חשיבה.
- הגבלה למספרי טלפון מורשים בלבד.
- שמירת היסטוריית שיחות ב-SQLite.

## פקודות בוט

- `/new` — פתיחת שיחה חדשה
- `/list` — רשימת השיחות האחרונות
- `/switch <מספר>` — מעבר לשיחה אחרת
- `/model` — הצגת המודל הנוכחי
- `/model <שם>` — החלפת מודל
- `/thinking on/off` — הפעלה/כיבוי מצב חשיבה
- `/help` — רשימת פקודות

## משתני סביבה

| משתנה | תיאור |
|-------|-------|
| `GREEN_API_URL` | כתובת ה-API של Green API (למשל `https://7107.api.greenapi.com`) |
| `GREEN_API_INSTANCE_ID` | מספר ה-instance ב-Green API |
| `GREEN_API_TOKEN` | ה-token של ה-instance |
| `KIMI_API_KEY` | מפתח API של Kimi/Moonshot |
| `KIMI_DEFAULT_MODEL` | מודל ברירת מחדל (ברירת מחדל: `kimi-k2`) |
| `ALLOWED_PHONES` | רשימת מספרי טלפון מורשים, מופרדים בפסיקים (ריק = הכל מורשה) |

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
uvicorn main:app --reload
```
