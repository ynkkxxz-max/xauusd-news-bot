import logging
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = (bot_token or TELEGRAM_BOT_TOKEN).strip()
        self.chat_id = (chat_id or TELEGRAM_CHAT_ID).strip()
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id and self.bot_token != "YOUR_TELEGRAM_BOT_TOKEN_HERE")

    def send_message(self, text: str, parse_mode: str = "HTML", disable_web_page_preview: bool = True, auto_pin: bool = False, reply_markup: dict = None, chat_id: str = None) -> dict:
        """Send message directly to Telegram channel/chat. If auto_pin is True, pins the message."""
        if not self.is_configured():
            logger.warning("[TelegramNotifier] Credentials not set. Message output (Simulation):\n" + "="*50 + f"\n{text}\n" + "="*50)
            return {"ok": True, "result": {"message_id": 999999, "simulated": True}}

        target_chat = str(chat_id or self.chat_id)
        url = f"{self.base_url}/sendMessage"
        if parse_mode == "HTML" and text:
            import re
            text = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[a-fA-F0-9]+);)', '&amp;', text)
        payload = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
            "link_preview_options": {"is_disabled": True}
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        try:
            resp = requests.post(url, json=payload, timeout=15)
            data = resp.json()
            if not data.get("ok"):
                logger.error(f"[TelegramNotifier] Error sending message: {data}")
                # Fallback: If Telegram rejected unsupported HTML tags (e.g. <font>, <div> from RSS feeds)
                desc = str(data.get("description", "")).lower()
                if "can't parse entities" in desc or "entity" in desc:
                    logger.info("[TelegramNotifier] Retrying message with sanitized HTML tags...")
                    import re
                    import html
                    # Normalize anchor tags to only keep href (strip target="_blank" and other unsupported attributes)
                    clean_text = re.sub(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>', r'<a href="\1">', text, flags=re.IGNORECASE)
                    # Strip all tags except supported Telegram tags
                    clean_text = re.sub(r'<(?!(?:b|strong|i|em|u|ins|s|strike|del|a|code|pre|blockquote)\b)[^>]+>', '', clean_text)
                    clean_text = re.sub(r'</(?!(?:b|strong|i|em|u|ins|s|strike|del|a|code|pre|blockquote)\b)[^>]+>', '', clean_text)
                    clean_text = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[a-fA-F0-9]+);)', '&amp;', clean_text)
                    payload["text"] = clean_text
                    retry_resp = requests.post(url, json=payload, timeout=15)
                    data = retry_resp.json()
                    if not data.get("ok"):
                        # Ultimate fallback: Plain text without parse_mode (strip ALL HTML tags so raw tags never show)
                        logger.warning("[TelegramNotifier] HTML retry failed, falling back to pure plain text.")
                        payload.pop("parse_mode", None)
                        pure_text = re.sub(r'<[^>]+>', '', text)
                        payload["text"] = html.unescape(pure_text).strip()
                        plain_resp = requests.post(url, json=payload, timeout=15)
                        data = plain_resp.json()

            if not data.get("ok"):
                return data
            
            message_id = data.get("result", {}).get("message_id")
            logger.info(f"[TelegramNotifier] Message sent successfully (ID: {message_id})")

            if auto_pin and message_id:
                self.pin_message(message_id)

            return data
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception while sending message: {e}")
            return {"ok": False, "error": str(e)}

    def send_photo(self, photo_bytes: bytes, caption: str = "", parse_mode: str = "HTML", reply_markup: dict = None, chat_id: str = None) -> dict:
        """Uploads a PNG image to the chat via the sendPhoto API."""
        if not self.is_configured():
            logger.warning(f"[TelegramNotifier] Credentials not set. Simulated photo upload ({len(photo_bytes)} bytes).")
            return {"ok": True, "result": {"message_id": 999998, "simulated": True}}

        target_chat = str(chat_id or self.chat_id)
        url = f"{self.base_url}/sendPhoto"
        files = {"photo": ("calendar.png", photo_bytes, "image/png")}
        data = {"chat_id": target_chat}
        if caption:
            if parse_mode == "HTML":
                import re
                caption = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[a-fA-F0-9]+);)', '&amp;', caption)
            data["caption"] = caption
            data["parse_mode"] = parse_mode
        if reply_markup:
            import json
            data["reply_markup"] = json.dumps(reply_markup)

        try:
            resp = requests.post(url, data=data, files=files, timeout=30)
            result = resp.json()
            if result.get("ok"):
                logger.info(f"[TelegramNotifier] Photo sent (ID: {result.get('result', {}).get('message_id')})")
            else:
                logger.error(f"[TelegramNotifier] Error sending photo: {result}")
                # Fallback: if HTML parsing failed, retry with sanitized HTML preserving supported tags & escaped &
                desc = str(result.get("description", "")).lower()
                if "can't parse entities" in desc or "entity" in desc:
                    import re
                    import html
                    clean_caption = re.sub(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>', r'<a href="\1">', caption, flags=re.IGNORECASE)
                    clean_caption = re.sub(r'<(?!(?:b|strong|i|em|u|ins|s|strike|del|a|code|pre|blockquote)\b)[^>]+>', '', clean_caption)
                    clean_caption = re.sub(r'</(?!(?:b|strong|i|em|u|ins|s|strike|del|a|code|pre|blockquote)\b)[^>]+>', '', clean_caption)
                    clean_caption = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[a-fA-F0-9]+);)', '&amp;', clean_caption)[:1020]
                    data["caption"] = clean_caption
                    files = {"photo": ("calendar.png", photo_bytes, "image/png")}
                    retry_resp = requests.post(url, data=data, files=files, timeout=30)
                    result = retry_resp.json()
                    if result.get("ok"):
                        logger.info(f"[TelegramNotifier] Photo sent on sanitized HTML retry (ID: {result.get('result', {}).get('message_id')})")
                    else:
                        clean_caption = re.sub(r"<[^>]+>", "", caption)[:1020]
                        data["caption"] = html.unescape(clean_caption).strip()
                        data.pop("parse_mode", None)
                        files = {"photo": ("calendar.png", photo_bytes, "image/png")}
                        retry_resp2 = requests.post(url, data=data, files=files, timeout=30)
                        result = retry_resp2.json()
                        if result.get("ok"):
                            logger.info(f"[TelegramNotifier] Photo sent on plain-text fallback (ID: {result.get('result', {}).get('message_id')})")
            return result
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception while sending photo: {e}")
            return {"ok": False, "error": str(e)}

    def edit_message_caption(self, message_id: int, caption: str, parse_mode: str = "HTML", reply_markup: dict = None, chat_id: str = None) -> dict:
        """Edits the caption of an existing photo/document message in the chat/channel."""
        if not self.is_configured():
            logger.info(f"[TelegramNotifier] Simulated edit caption for message ID: {message_id}")
            return {"ok": True, "result": {"message_id": message_id, "simulated": True}}

        target_chat = str(chat_id or self.chat_id)
        url = f"{self.base_url}/editMessageCaption"
        if parse_mode == "HTML" and caption:
            import re
            caption = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[a-fA-F0-9]+);)', '&amp;', caption)
        payload = {
            "chat_id": target_chat,
            "message_id": message_id,
            "caption": caption,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            resp = requests.post(url, json=payload, timeout=15)
            result = resp.json()
            if result.get("ok"):
                logger.info(f"[TelegramNotifier] Caption edited successfully (ID: {message_id})")
            else:
                logger.error(f"[TelegramNotifier] Error editing caption: {result}")
            return result
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception while editing caption: {e}")
            return {"ok": False, "error": str(e)}

    def edit_message_text(self, message_id: int, text: str, parse_mode: str = "HTML", reply_markup: dict = None, chat_id: str = None) -> dict:
        """Edits the text of an existing text message in the chat/channel."""
        if not self.is_configured():
            logger.info(f"[TelegramNotifier] Simulated edit text for message ID: {message_id}")
            return {"ok": True, "result": {"message_id": message_id, "simulated": True}}

        target_chat = str(chat_id or self.chat_id)
        url = f"{self.base_url}/editMessageText"
        payload = {
            "chat_id": target_chat,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
            "link_preview_options": {"is_disabled": True}
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            resp = requests.post(url, json=payload, timeout=15)
            result = resp.json()
            if result.get("ok"):
                logger.info(f"[TelegramNotifier] Message text edited successfully (ID: {message_id})")
            else:
                logger.error(f"[TelegramNotifier] Error editing message text: {result}")
            return result
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception while editing text: {e}")
            return {"ok": False, "error": str(e)}

    def delete_message(self, message_id: int, chat_id: str = None) -> dict:
        """Deletes a message from the Telegram chat/channel."""
        if not self.is_configured():
            logger.info(f"[TelegramNotifier] Simulated delete for message ID: {message_id}")
            return {"ok": True, "result": True}

        target_chat = str(chat_id or self.chat_id)
        url = f"{self.base_url}/deleteMessage"
        payload = {"chat_id": target_chat, "message_id": message_id}
        try:
            resp = requests.post(url, json=payload, timeout=15)
            result = resp.json()
            if result.get("ok"):
                logger.info(f"[TelegramNotifier] Message deleted successfully (ID: {message_id})")
            else:
                logger.error(f"[TelegramNotifier] Error deleting message: {result}")
            return result
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception while deleting message: {e}")
            return {"ok": False, "error": str(e)}

    def send_voice(self, voice_bytes: bytes, caption: str = "", parse_mode: str = "HTML", reply_markup: dict = None, chat_id: str = None) -> dict:
        """Voice notes are permanently disabled per user directive."""
        logger.info("[TelegramNotifier] Voice notes are permanently disabled per user directive. Skipping upload.")
        return {"ok": True, "result": {"message_id": 0, "disabled": True}}

    def pin_message(self, message_id: int, disable_notification: bool = True) -> bool:
        """Auto-pin message in the chat/channel."""
        if not self.is_configured():
            logger.info(f"[TelegramNotifier] Simulated pinning message ID: {message_id}")
            return True

        url = f"{self.base_url}/pinChatMessage"
        payload = {
            "chat_id": self.chat_id,
            "message_id": message_id,
            "disable_notification": disable_notification
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            data = resp.json()
            if data.get("ok"):
                logger.info(f"[TelegramNotifier] Pinned message ID: {message_id}")
                return True
            else:
                logger.error(f"[TelegramNotifier] Failed to pin message: {data}")
                return False
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception pinning message: {e}")
            return False

    def get_updates(self, offset: int = None, timeout: int = 1) -> list:
        """Fetches incoming user messages / commands via getUpdates API."""
        if not self.is_configured():
            return []
        url = f"{self.base_url}/getUpdates"
        params = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        try:
            resp = requests.get(url, params=params, timeout=timeout + 5)
            data = resp.json()
            if data.get("ok"):
                return data.get("result", [])
        except Exception as e:
            logger.debug(f"[TelegramNotifier] getUpdates error: {e}")
        return []

    def answer_callback_query(self, callback_query_id: str, text: str = None, show_alert: bool = False):
        """Acknowledges incoming button clicks via answerCallbackQuery API."""
        if not self.is_configured() or not callback_query_id:
            return
        url = f"{self.base_url}/answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id, "show_alert": show_alert}
        if text:
            payload["text"] = text
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            logger.debug(f"[TelegramNotifier] answerCallbackQuery error: {e}")

    def send_poll(self, question: str, options: list, is_anonymous: bool = False, reply_markup: dict = None, chat_id: str = None) -> dict:
        """Sends an interactive native Telegram Poll directly to the Channel or Chat with optional inline keyboard."""
        if not self.is_configured():
            logger.warning(f"[TelegramNotifier] Credentials not set. Simulated Poll: {question}")
            return {"ok": True, "result": {"message_id": 999990, "simulated": True}}

        target_chat = str(chat_id or self.chat_id)
        url = f"{self.base_url}/sendPoll"
        payload = {
            "chat_id": target_chat,
            "question": question[:300],
            "options": options,
            "is_anonymous": is_anonymous
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            resp = requests.post(url, json=payload, timeout=12)
            data = resp.json()
            if not data.get("ok"):
                logger.error(f"[TelegramNotifier] sendPoll error: {data}")
            else:
                logger.info(f"[TelegramNotifier] Poll sent successfully (ID: {data.get('result', {}).get('message_id')})")
            return data
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception sending poll: {e}")
            return {"ok": False, "error": str(e)}

    def get_file_bytes(self, file_id: str) -> bytes:
        """Downloads a file (e.g. photo) from Telegram servers using getFile API."""
        if not self.is_configured() or not file_id:
            return b""
        try:
            url = f"{self.base_url}/getFile"
            resp = requests.get(url, params={"file_id": file_id}, timeout=10)
            data = resp.json()
            if not data.get("ok"):
                logger.error(f"[TelegramNotifier] getFile error: {data}")
                return b""
            file_path = data.get("result", {}).get("file_path")
            if not file_path:
                return b""
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            f_resp = requests.get(download_url, timeout=25)
            if f_resp.status_code == 200:
                return f_resp.content
            logger.error(f"[TelegramNotifier] Error downloading file bytes: HTTP {f_resp.status_code}")
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception downloading file: {e}")
        return b""

    def is_user_member_of_channel(self, user_id: int, channel_id: str = None) -> bool:
        """Check if user_id is a member/admin/creator of the official channel."""
        if not self.is_configured() or not user_id:
            return True
        target_channel = str(channel_id or self.chat_id)
        url = f"{self.base_url}/getChatMember"
        try:
            resp = requests.get(url, params={"chat_id": target_channel, "user_id": user_id}, timeout=8)
            data = resp.json()
            if data.get("ok"):
                status = data.get("result", {}).get("status", "")
                return status in ("creator", "administrator", "member", "restricted")
            logger.warning(f"[TelegramNotifier] User {user_id} not a member of {target_channel}: {data}")
            return False
        except Exception as e:
            logger.error(f"[TelegramNotifier] Error checking member status: {e}")
            return True # Fail-open on network error to not block legitimate users



