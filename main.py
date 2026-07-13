import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

import config
import database
import green_api
import conversation
import commands
import kimi_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title=config.APP_NAME, version=config.APP_VERSION, lifespan=lifespan)


@app.get("/")
async def root():
    return {"status": "ok", "app": config.APP_NAME, "version": config.APP_VERSION}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return Response(status_code=200)

    parsed = green_api.parse_webhook(data)

    if parsed["type"] != "incomingMessageReceived":
        return Response(status_code=200)

    sender_phone = parsed["sender_phone"]
    text = parsed["text"]

    if not sender_phone or not text:
        return Response(status_code=200)

    if not config.is_phone_allowed(sender_phone):
        print(f"Ignoring message from unauthorized phone: {sender_phone}")
        return Response(status_code=200)

    user = conversation.get_or_create_user(
        sender_phone,
        default_model=config.KIMI_DEFAULT_MODEL,
        default_thinking=config.THINKING_ENABLED_DEFAULT
    )

    conv = conversation.get_active_conversation(
        user_id=user["id"],
        model=user.get("default_model", config.KIMI_DEFAULT_MODEL),
        thinking=bool(user.get("default_thinking", config.THINKING_ENABLED_DEFAULT))
    )

    command_response, is_command = commands.handle_command(text, user, conv)

    if is_command:
        green_api.send_message(sender_phone, command_response)

        if text.strip().lower().startswith("/new"):
            pass
        return Response(status_code=200)

    conversation.add_message(conv["id"], "user", text)

    if conv["title"] == "שיחה חדשה":
        title = kimi_api.generate_title(text)
        conversation.update_conversation_title(conv["id"], title)

    history = conversation.get_messages(conv["id"], limit=config.KIMI_MAX_HISTORY)
    messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]

    reply = kimi_api.get_response(messages, conv["model"], bool(conv["thinking"]))

    conversation.add_message(conv["id"], "assistant", reply)

    green_api.send_message(sender_phone, reply)

    return Response(status_code=200)


@app.post("/set-webhook")
async def set_webhook(request: Request):
    body = await request.json()
    webhook_url = body.get("webhook_url", "")
    if not webhook_url:
        return JSONResponse({"error": "webhook_url is required"}, status_code=400)

    success = green_api.set_webhook(webhook_url)
    return JSONResponse({"success": success})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.PORT)
