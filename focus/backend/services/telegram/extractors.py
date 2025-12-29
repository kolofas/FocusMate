from typing import Any, Optional, Dict


def extract_text_and_chat_id(
    update: dict[str, Any],
) -> tuple[Optional[str], Optional[int], dict[str, Any]]:
    """
    Достаёт текст и chat_id из апдейта Telegram.
    Поддерживает message/edited_message.
    """
    msg = update.get("message") or update.get("edited_message") or {}
    text = (msg.get("text") or "").strip()

    from_block = msg.get("from") or {}
    meta = {
        "username": from_block.get("username"),
        "first_name": from_block.get("first_name"),
    }

    chat = msg.get("chat") or {}
    chat_id = chat.get("id")

    if not text:
        return None, None, meta
    return text, chat_id, meta


def extract_callback(
    update: Dict[str, Any],
) -> tuple[Optional[str], Optional[int], Optional[str], dict[str, str]]:
    """
    Returns: (data, chat_id, callback_query_id, meta)
    """
    cq = update.get("callback_query")
    if not cq:
        return None, None, None, {}

    data = cq.get("data")
    msg = cq.get("message") or {}
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")

    user = cq.get("from") or {}
    meta = {
        "username": user.get("username"),
        "first_name": user.get("first_name"),
    }

    return data, chat_id, cq.get("id"), meta
