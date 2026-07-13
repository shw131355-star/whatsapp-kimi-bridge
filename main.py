import asyncio
import logging
import os
import re
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

import config
import database
import green_api
import conversation
import commands
import kimi_api
import openrouter_api
import image_gen
import voice

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up %s v%s", config.APP_NAME, config.APP_VERSION)
    logger.info("Config: %s", config.safe_config_log())
    database.init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down")


app = FastAPI(title=config.APP_NAME, version=config.APP_VERSION, lifespan=lifespan)


@app.get("/")
async def root():
    return {"status": "ok", "app": config.APP_NAME, "version": config.APP_VERSION}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/test-kimi")
async def test_kimi(request: Request):
    body = await request.json()
    test_message = body.get("message", "Say hello")
    result = kimi_api.test_connection(test_message)
    return JSONResponse(result)


@app.post("/test-openrouter")
async def test_openrouter(request: Request):
    body = await request.json()
    test_message = body.get("message", "Say hello")
    result = openrouter_api.test_connection(test_message)
    return JSONResponse(result)


@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
    except Exception as e:
        logger.warning("Failed to parse webhook JSON: %s", e)
        return Response(status_code=200)

    parsed = green_api.parse_webhook(data)
    logger.info("Webhook received: type=%s sender=%s text=%s image=%s audio=%s",
                parsed["type"], parsed["sender_phone"], parsed["text"], bool(parsed["image_url"]), bool(parsed["audio_url"]))

    if parsed["type"] != "incomingMessageReceived":
        logger.info("Ignoring non-message webhook type: %s", parsed["type"])
        return Response(status_code=200)

    sender_phone = parsed["sender_phone"]
    text = parsed["text"]
    image_url = parsed["image_url"]
    audio_url = parsed["audio_url"]

    if not sender_phone:
        logger.warning("Missing sender_phone in webhook")
        return Response(status_code=200)

    if not text and not image_url and not audio_url:
        logger.warning("No text or image or audio in webhook")
        return Response(status_code=200)

    if not config.is_phone_allowed(sender_phone):
        logger.warning("Ignoring message from unauthorized phone: %s", sender_phone)
        return Response(status_code=200)

    is_girlfriend = config.is_girlfriend_phone(sender_phone)

    asyncio.create_task(_process_webhook(sender_phone, text or "", image_url, audio_url, is_girlfriend))
    return Response(status_code=200)


async def _process_webhook(sender_phone: str, text: str, image_url: str, audio_url: str, is_girlfriend: bool):
    try:
        if is_girlfriend:
            await _handle_girlfriend_message(sender_phone, text, image_url, audio_url)
        else:
            await _handle_kimi_message(sender_phone, text)
    except Exception as e:
        logger.exception("Error handling webhook from %s", sender_phone)
        try:
            green_api.send_message(sender_phone, f"שגיאה בשרת: {str(e)}")
        except Exception as inner:
            logger.error("Failed to send error message: %s", inner)


async def _handle_kimi_message(sender_phone: str, text: str):
    user = conversation.get_or_create_user(
        sender_phone,
        default_model=config.KIMI_DEFAULT_MODEL,
        default_thinking=config.THINKING_ENABLED_DEFAULT
    )
    logger.info("User resolved: id=%s model=%s thinking=%s",
                user["id"], user.get("default_model"), user.get("default_thinking"))

    conv = conversation.get_active_conversation(
        user_id=user["id"],
        model=user.get("default_model", config.KIMI_DEFAULT_MODEL),
        thinking=bool(user.get("default_thinking", config.THINKING_ENABLED_DEFAULT)),
        personality="kimi"
    )
    logger.info("Conversation resolved: id=%s model=%s thinking=%s title=%s personality=%s",
                conv["id"], conv["model"], conv["thinking"], conv.get("title"), conv.get("personality"))

    command_response, is_command = commands.handle_command(text, user, conv)

    if is_command:
        logger.info("Command handled: %s", text.split()[0])
        green_api.send_message(sender_phone, command_response)
        return

    conversation.add_message(conv["id"], "user", text)
    logger.info("User message saved to conversation %s", conv["id"])

    if conv["title"] == "שיחה חדשה":
        title = kimi_api.generate_title(text)
        conversation.update_conversation_title(conv["id"], title)
        logger.info("Generated conversation title: %s", title)

    history = conversation.get_messages(conv["id"], limit=config.KIMI_MAX_HISTORY)
    messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
    logger.info("Calling Kimi API with %d history messages, model=%s", len(messages), conv["model"])

    reply = kimi_api.get_response(messages, conv["model"], bool(conv["thinking"]))
    logger.info("Kimi reply (first 120 chars): %s", reply[:120])

    conversation.add_message(conv["id"], "assistant", reply)
    logger.info("Assistant reply saved to conversation %s", conv["id"])

    sent = green_api.send_message(sender_phone, reply)
    logger.info("Reply sent to %s: success=%s", sender_phone, sent)


def _is_photo_request_by_keywords(text: str) -> bool:
    keywords = [
        "תמונה", "ביקיני", "בגד ים", "בגדים", "תלבוש", "תראי", "תשלחי",
        "תצלמי", "תחשפי", "תתפשטי", "הראי", "שלחי לי", "תתני לי",
        "אני רוצה לראות", "צילום", "selfie", "סלפי", "תשלחי לי",
        "תחזירי", "מראה", "ויזואלי", "הצגי", "תציגי", "תמונות",
        "תצלום", "תצטלמת", "פוזה", "מצלמה", "אלבום"
    ]
    lowered = text.lower()
    return any(k in lowered for k in keywords)


def _is_photo_request(text: str, recent_context: str = "") -> bool:
    if _is_photo_request_by_keywords(text):
        return True
    return openrouter_api.detect_image_request(text, recent_context)


def _extract_photo_description(text: str) -> str:
    cleaned = re.sub(
        r"\b(תשלחי|שלחי לי|תראי|הראי|תצלמי|תמונה|selfie|סלפי|תחזירי|הצגי|תציגי)\b",
        "", text, flags=re.IGNORECASE
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or "realistic photo of Maya"


async def _handle_girlfriend_message(sender_phone: str, text: str, image_url: str, audio_url: str = ""):
    user = conversation.get_or_create_user(
        sender_phone,
        default_model=config.OPENROUTER_MODEL,
        default_thinking=False
    )
    logger.info("Girlfriend user resolved: id=%s", user["id"])

    conv = conversation.get_active_conversation(
        user_id=user["id"],
        model=config.OPENROUTER_MODEL,
        thinking=False,
        personality="girlfriend"
    )
    logger.info("Girlfriend conversation resolved: id=%s title=%s",
                conv["id"], conv.get("title"))

    if text.startswith("/"):
        command_response, is_command = commands.handle_command(text, user, conv)
        if is_command:
            logger.info("Girlfriend command handled: %s", text.split()[0])
            if command_response.startswith("__SEND_IMAGE__"):
                generated_url = command_response.replace("__SEND_IMAGE__", "")
                img_arg = text.split(maxsplit=1)[1] if len(text.split(maxsplit=1)) > 1 else ""
                try:
                    caption = openrouter_api.generate_image_caption(img_arg, img_arg or "photo of Maya")
                except Exception as e:
                    logger.warning("Failed to generate /img caption: %s", e)
                    caption = "הנה, רק בשבילך 😉"
                success = False
                try:
                    img_response = httpx.get(generated_url, timeout=60.0)
                    img_response.raise_for_status()
                    if len(img_response.content) == 0:
                        raise ValueError("Downloaded image is empty")
                    success = green_api.send_file_by_upload(sender_phone, img_response.content, filename="image.jpg", caption=caption)
                except Exception as e:
                    logger.warning("Image upload failed for /img, falling back to URL: %s", e)
                if not success:
                    success = green_api.send_file_by_url(sender_phone, generated_url, caption)
                if success:
                    logger.info("Sent generated image to %s", sender_phone)
                else:
                    green_api.send_message(sender_phone, "מצטערת, לא הצלחתי לשלוח את התמונה 💕")
            else:
                green_api.send_message(sender_phone, command_response)
            return

    user_text = text
    if audio_url:
        logger.info("Transcribing audio for %s", sender_phone)
        transcribed = await voice.transcribe_audio(audio_url)
        if transcribed:
            user_text = transcribed
            logger.info("Audio transcribed: %s", user_text[:100])
        else:
            user_text = "[שלחתי הודעה קולית שאני לא הצלחתי להבין]"
            logger.warning("Failed to transcribe audio for %s", sender_phone)
    elif image_url and not user_text:
        user_text = "שלחתי לך תמונה"

    conversation.add_message(conv["id"], "user", user_text, image_url=image_url)
    logger.info("Girlfriend user message saved to conversation %s (image=%s audio=%s)", conv["id"], bool(image_url), bool(audio_url))

    # Build recent context for image detection
    recent_messages = conversation.get_messages(conv["id"], limit=6)
    context_lines = [f"{m['role']}: {m['content'][:120]}" for m in recent_messages[:-1]]
    recent_context = "\n".join(context_lines)

    # Natural photo request
    if _is_photo_request(user_text, recent_context) and not image_url and not audio_url:
        logger.info("Detected natural photo request: %s", user_text)
        description = _extract_photo_description(text)
        english_prompt = openrouter_api.generate_image_prompt(description)
        generated_url = image_gen.generate_girlfriend_image_url(english_prompt, seed=123456)

        try:
            caption_reply = openrouter_api.generate_image_caption(user_text, english_prompt)
        except Exception as e:
            logger.warning("Failed to generate caption, using default: %s", e)
            caption_reply = "הנה, רק בשבילך 😉"

        success = False
        try:
            logger.info("Downloading generated image from %s", generated_url)
            img_response = httpx.get(generated_url, timeout=60.0)
            img_response.raise_for_status()
            if len(img_response.content) == 0:
                raise ValueError("Downloaded image is empty")
            success = green_api.send_file_by_upload(sender_phone, img_response.content, filename="image.jpg", caption=caption_reply)
            logger.info("Image upload result for %s: %s", sender_phone, success)
        except Exception as e:
            logger.warning("Image upload failed, falling back to URL: %s", e)

        if not success:
            success = green_api.send_file_by_url(sender_phone, generated_url, caption_reply)
            logger.info("Image URL send result for %s: %s", sender_phone, success)

        if success:
            conversation.add_message(conv["id"], "assistant", f"[תמונה] {caption_reply}")
            logger.info("Sent generated image to %s", sender_phone)
        else:
            green_api.send_message(sender_phone, "מצטערת, נתקלתי בבעיה בשליחת התמונה. בוא ננסה שוב בעוד רגע 💕")
            logger.error("Failed to send generated image to %s", sender_phone)
        return

    if conv["title"] == "שיחה חדשה":
        title = openrouter_api.generate_title(user_text)
        conversation.update_conversation_title(conv["id"], title)
        logger.info("Generated girlfriend conversation title: %s", title)

    history = conversation.get_messages(conv["id"], limit=config.OPENROUTER_MAX_HISTORY)
    messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
    logger.info("Calling OpenRouter girlfriend API with %d history messages", len(messages))

    reply = openrouter_api.get_response(messages, image_url=image_url)
    logger.info("Girlfriend reply (first 120 chars): %s", reply[:120])

    conversation.add_message(conv["id"], "assistant", reply)
    logger.info("Girlfriend reply saved to conversation %s", conv["id"])

    if audio_url:
        try:
            audio_bytes = await voice.text_to_speech(reply)
            sent = green_api.send_file_by_upload(sender_phone, audio_bytes, filename="voice.mp3")
            logger.info("Voice reply sent to %s: success=%s", sender_phone, sent)
        except Exception as e:
            logger.warning("Failed to send voice reply, sending text: %s", e)
            sent = green_api.send_message(sender_phone, reply)
            logger.info("Text reply sent to %s: success=%s", sender_phone, sent)
    else:
        sent = green_api.send_message(sender_phone, reply)
        logger.info("Girlfriend reply sent to %s: success=%s", sender_phone, sent)


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
