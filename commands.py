import conversation
import kimi_api


def handle_command(text: str, user: dict, conv: dict) -> tuple:
    text = text.strip()

    if not text.startswith("/"):
        return None, False

    parts = text.split(maxsplit=1)
    command = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if command == "/help":
        return _help_text(), True

    if command == "/new":
        new_conv = conversation.create_conversation(
            user_id=user["id"],
            model=user.get("default_model", "kimi-k2"),
            thinking=bool(user.get("default_thinking", 0))
        )
        return f"✅ נפתחה שיחה חדשה (#{new_conv['id']}).", True

    if command == "/list":
        convs = conversation.list_conversations(user["id"], limit=10)
        if not convs:
            return "אין שיחות שמורות.", True

        lines = ["📋 השיחות האחרונות שלך:"]
        for c in convs:
            active = " ✅" if c["active"] else ""
            lines.append(f"#{c['id']} — {c['title']}{active}")
        return "\n".join(lines), True

    if command == "/switch":
        if not arg or not arg.isdigit():
            return "⚠️ השתמשו: /switch <מספר שיחה>", True

        conv_id = int(arg)
        switched = conversation.switch_conversation(user["id"], conv_id)
        if switched:
            return f"✅ עברת לשיחה #{switched['id']} — {switched['title']}", True
        return f"❌ לא נמצאה שיחה מספר {conv_id}.", True

    if command == "/model":
        if not arg:
            return f"🤖 המודל הנוכחי: {conv['model']}", True

        conversation.update_conversation_settings(conv["id"], model=arg)
        return f"✅ המודל עודכן ל-{arg}.", True

    if command == "/thinking":
        if arg == "on":
            conversation.update_conversation_settings(conv["id"], thinking=True)
            return "✅ מצב חשיבה מופעל.", True
        elif arg == "off":
            conversation.update_conversation_settings(conv["id"], thinking=False)
            return "✅ מצב חשיבה כבוי.", True
        else:
            status = "מופעל" if conv["thinking"] else "כבוי"
            return f"🧠 מצב חשיבה: {status}. השתמשו: /thinking on או /thinking off", True

    return None, False


def _help_text() -> str:
    return """📋 פקודות זמינות:

/new — פתיחת שיחה חדשה
/list — רשימת השיחות האחרונות
/switch <מספר> — מעבר לשיחה אחרת
/model — הצגת המודל הנוכחי
/model <שם> — החלפת מודל (למשל: /model kimi-k2)
/thinking on/off — הפעלה/כיבוי מצב חשיבה
/help — הצגת הודעה זו

פשוט שלחו הודעה כדי לדבר עם Kimi."""
