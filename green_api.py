import logging
import httpx
import config

logger = logging.getLogger(__name__)


def _base_url() -> str:
    url = config.GREEN_API_URL.rstrip("/")
    return url


def send_message(chat_id: str, message: str) -> bool:
    if not message or not message.strip():
        logger.warning("Refusing to send empty message")
        return False

    url = f"{_base_url()}/waInstance{config.GREEN_API_INSTANCE_ID}/sendMessage/{config.GREEN_API_TOKEN}"

    if not chat_id.endswith("@c.us"):
        chat_id = f"{chat_id}@c.us"

    payload = {
        "chatId": chat_id,
        "message": message
    }

    logger.info("Sending WhatsApp message to %s", chat_id)
    try:
        response = httpx.post(url, json=payload, timeout=30.0)
        logger.info("Green API send_message status: %s", response.status_code)
        if response.status_code != 200:
            logger.warning("Green API send_message body: %s", response.text)
        return response.status_code == 200
    except Exception as e:
        logger.exception("Error sending message")
        return False


def send_file_by_url(chat_id: str, file_url: str, caption: str = "") -> bool:
    if not file_url:
        logger.warning("Refusing to send empty file URL")
        return False

    url = f"{_base_url()}/waInstance{config.GREEN_API_INSTANCE_ID}/sendFileByUrl/{config.GREEN_API_TOKEN}"

    if not chat_id.endswith("@c.us"):
        chat_id = f"{chat_id}@c.us"

    payload = {
        "chatId": chat_id,
        "urlFile": file_url,
        "fileName": "image.jpg"
    }
    if caption:
        payload["caption"] = caption

    logger.info("Sending WhatsApp file to %s", chat_id)
    try:
        response = httpx.post(url, json=payload, timeout=60.0)
        logger.info("Green API send_file_by_url status: %s", response.status_code)
        if response.status_code != 200:
            logger.warning("Green API send_file_by_url body: %s", response.text)
        return response.status_code == 200
    except Exception as e:
        logger.exception("Error sending file")
        return False


def send_file_by_upload(chat_id: str, file_bytes: bytes, filename: str = "image.jpg", caption: str = "") -> bool:
    if not file_bytes:
        logger.warning("Refusing to send empty file bytes")
        return False

    url = f"{_base_url()}/waInstance{config.GREEN_API_INSTANCE_ID}/sendFileByUpload/{config.GREEN_API_TOKEN}"

    if not chat_id.endswith("@c.us"):
        chat_id = f"{chat_id}@c.us"

    files = {"file": (filename, file_bytes, "image/jpeg")}
    data = {"chatId": chat_id}
    if caption:
        data["caption"] = caption

    logger.info("Sending WhatsApp file upload to %s", chat_id)
    try:
        response = httpx.post(url, data=data, files=files, timeout=120.0)
        logger.info("Green API send_file_by_upload status: %s", response.status_code)
        if response.status_code != 200:
            logger.warning("Green API send_file_by_upload body: %s", response.text)
        return response.status_code == 200
    except Exception as e:
        logger.exception("Error sending file upload")
        return False


def set_webhook(webhook_url: str) -> bool:
    url = f"{_base_url()}/waInstance{config.GREEN_API_INSTANCE_ID}/setSettings/{config.GREEN_API_TOKEN}"

    payload = {
        "webhookUrl": webhook_url,
        "webhookUrlToken": "",
        "delaySendMessagesMilliseconds": 3000,
        "markIncomingMessagesReaded": "no",
        "markIncomingMessagesReadedOnReply": "no",
        "sharedSession": "no",
        "proxy": None,
        "defaultOriginalFilename": None,
        "filenameForOriginalFileOnDownloading": None
    }

    try:
        response = httpx.post(url, json=payload, timeout=30.0)
        logger.info("Green API set_webhook status: %s", response.status_code)
        return response.status_code == 200
    except Exception as e:
        logger.exception("Error setting webhook")
        return False


def parse_webhook(data: dict) -> dict:
    result = {
        "type": data.get("typeWebhook", ""),
        "sender_phone": "",
        "sender_name": "",
        "text": "",
        "chat_id": "",
        "image_url": "",
        "caption": ""
    }

    if result["type"] != "incomingMessageReceived":
        return result

    sender_data = data.get("senderData", {})
    result["chat_id"] = sender_data.get("chatId", "")
    result["sender_phone"] = sender_data.get("sender", "").replace("@c.us", "")
    result["sender_name"] = sender_data.get("senderName", "")

    message_data = data.get("messageData", {})
    type_message = message_data.get("typeMessage", "")

    if type_message == "textMessage":
        text_data = message_data.get("textMessageData", {})
        result["text"] = text_data.get("textMessage", "")
    elif type_message == "extendedTextMessage":
        text_data = message_data.get("extendedTextMessageData", {})
        result["text"] = text_data.get("text", "")
    elif type_message == "imageMessage":
        file_data = message_data.get("fileMessageData", {})
        result["image_url"] = file_data.get("downloadUrl", "")
        result["caption"] = file_data.get("caption", "")
        result["text"] = result["caption"]
    elif type_message in ("audioMessage", "pttMessage", "voiceMessage"):
        file_data = message_data.get("fileMessageData", {})
        result["image_url"] = file_data.get("downloadUrl", "")
        result["caption"] = file_data.get("caption", "")
        result["text"] = "[הודעה קולית]"

    return result
