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

    def send_message(self, text: str, parse_mode: str = "HTML", disable_web_page_preview: bool = True, auto_pin: bool = False) -> dict:
        """Send message directly to Telegram channel/chat. If auto_pin is True, pins the message."""
        if not self.is_configured():
            logger.warning("[TelegramNotifier] Credentials not set. Message output (Simulation):\n" + "="*50 + f"\n{text}\n" + "="*50)
            return {"ok": True, "result": {"message_id": 999999, "simulated": True}}

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        
        try:
            resp = requests.post(url, json=payload, timeout=15)
            data = resp.json()
            if not data.get("ok"):
                logger.error(f"[TelegramNotifier] Error sending message: {data}")
                return data
            
            message_id = data.get("result", {}).get("message_id")
            logger.info(f"[TelegramNotifier] Message sent successfully (ID: {message_id})")

            if auto_pin and message_id:
                self.pin_message(message_id)

            return data
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception while sending message: {e}")
            return {"ok": False, "error": str(e)}

    def send_photo(self, photo_bytes: bytes, caption: str = "", parse_mode: str = "HTML") -> dict:
        """Uploads an image (PNG bytes) to the chat via the sendPhoto API."""
        if not self.is_configured():
            logger.warning(f"[TelegramNotifier] Credentials not set. Simulated photo upload ({len(photo_bytes)} bytes).")
            return {"ok": True, "result": {"message_id": 999998, "simulated": True}}

        url = f"{self.base_url}/sendPhoto"
        files = {"photo": ("chart.png", photo_bytes, "image/png")}
        data = {"chat_id": self.chat_id}
        if caption:
            data["caption"] = caption
            data["parse_mode"] = parse_mode

        try:
            resp = requests.post(url, data=data, files=files, timeout=30)
            result = resp.json()
            if result.get("ok"):
                logger.info(f"[TelegramNotifier] Photo sent (ID: {result.get('result', {}).get('message_id')})")
            else:
                logger.error(f"[TelegramNotifier] Error sending photo: {result}")
            return result
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception while sending photo: {e}")
            return {"ok": False, "error": str(e)}

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
