import httpx
import config


def _base_url() -> str:
    url = config.GREEN_API_URL.rstrip("/")
    return url


def send_message(chat_id: str, message: str) -> bool:
    if not message or not message.strip():
        return False

    url = f"{_base_url()}/waInstance{config.GREEN_API_INSTANCE_ID}/sendMessage/{config.GREEN_API_TOKEN}"

    if not chat_id.endswith("@c.us"):
        chat_id = f"{chat_id}@c.us"

    payload = {
        "chatId": chat_id,
        "message": message
    }

    try:
        response = httpx.post(url, json=payload, timeout=30.0)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending message: {e}")
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
        return response.status_code == 200
    except Exception as e:
        print(f"Error setting webhook: {e}")
        return False


def parse_webhook(data: dict) -> dict:
    result = {
        "type": data.get("typeWebhook", ""),
        "sender_phone": "",
        "sender_name": "",
        "text": "",
        "chat_id": ""
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

    return result
