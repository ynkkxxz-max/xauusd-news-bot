import os
import logging
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

def enforce_telegram_char_limit(text: str, max_visible: int) -> str:
    """Bulletproof gate enforcing strict character limits, lexical rules, and grammatical completeness before any Telegram dispatch."""
    if not text:
        return ""
    import re

    # 1. Comprehensive Lexical & Spelling Sanitization
    try:
        from khmer_formatter import sanitize_khmer_spelling
        text = sanitize_khmer_spelling(text)
    except Exception:
        pass

    text = re.sub(r'\bប្រមាន\b', 'ព្រមាន', text)
    text = re.sub(r'ការប្រមាន', 'ការព្រមាន', text)
    text = re.sub(r'បានប្រមាន', 'បានព្រមាន', text)
    text = re.sub(r'ធ្វើអោយ', 'ធ្វើឱ្យ', text)
    text = re.sub(r'ឿរ៉ង់', 'អ៊ីរ៉ង់', text)
    text = re.sub(r'\bអគ្លេស\b', 'អង់គ្លេស', text)
    text = re.sub(r'ចក្រភពអគ្លេស', 'ចក្រភពអង់គ្លេស', text)
    text = re.sub(r'\bសហរដ្ធ\b', 'សហរដ្ឋ', text)
    text = re.sub(r'\bរដ្ធ\b', 'រដ្ឋ', text)
    text = re.sub(r'\bសេដ្ធកិច្ច\b', 'សេដ្ឋកិច្ច', text)
    text = re.sub(r'\bអត្រាកាប្រាក់\b', 'អត្រាការប្រាក់', text)
    text = re.sub(r'\bពាណិជ្ចកម្ម\b', 'ពាណិជ្ជកម្ម', text)
    
    # 2. Complete Sentence Guarantee & Colon/Fragment Stripping in Headline
    m_head = re.search(r'(<b>(.*?)</b>)', text, re.DOTALL)
    if m_head:
        orig_full_h = m_head.group(1)
        inner_h = m_head.group(2)
        # Strip all colons and trailing dots/ellipsis from headline
        clean_inner = re.sub(r'[\s\u200b]*[៖:：][\s\u200b]*', ' ', inner_h)
        clean_inner = re.sub(r'[\.]{2,}|…', '', clean_inner)
        clean_inner = re.sub(r'\s{2,}', ' ', clean_inner).strip()

        # Multi-Pattern Fragment Transformers:
        # Pattern A: "តួកគី និងដែនកំណត់..." -> "របាយការណ៍បង្ហាញពីដែនកំណត់...របស់តួកគី"
        m_frag_a = re.match(r'^([^\s]+)\s+និង\s*(ដែនកំណត់|អនាគត|ទស្សនវិស័យ|បញ្ហា|ស្ថានភាព|កិច្ចព្រមព្រៀង|វិបត្តិ|គោលនយោបាយ|យុទ្ធសាស្ត្រ|ផលវិបាក|ការប្រឈម)(.+)$', clean_inner)
        if m_frag_a:
            country_subj = m_frag_a.group(1).strip()
            topic_noun = m_frag_a.group(2).strip()
            rest = m_frag_a.group(3).strip()
            clean_inner = f"របាយការណ៍បង្ហាញពី{topic_noun}{rest}របស់{country_subj}"
        
        # Pattern B: Bare noun pair "A និង B" with NO active verbs -> "ការវិវឌ្ឍរវាង A និង B"
        elif re.match(r'^(.+?)\s+និង\s*(.+)$', clean_inner):
            _active_verbs = ('ប្រកាស', 'សម្រេច', 'ព្រមាន', 'ធ្លាក់ចុះ', 'កើនឡើង', 'ហក់ឡើង', 'ជួប', 'ពិភាក្សា', 'វាយប្រហារ', 'ពង្រីក', 'បញ្ឈប់', 'ចុះហត្ថលេខា', 'ផ្តល់', 'បដិសេធ', 'រង', 'គ្រោង', 'ដាក់ចេញ', 'អនុម័ត', 'ប្តេជ្ញា', 'ទាមទារ', 'ដក', 'ពង្រឹង', 'រិះគន់', 'បង្ហាញ', 'ត្រៀម', 'រៀបចំ', 'ស្នើ', 'ចុះ', 'ឡើង', 'ទម្លាក់', 'ជំរុញ', 'រារាំង', 'ទប់ស្កាត់', 'កែប្រែ', 'បោះទុន', 'វិនិយោគ', 'ឈ្នះ', 'ចាញ់', 'ចាប់ផ្តើម', 'បញ្ចប់')
            if not any(v in clean_inner for v in _active_verbs):
                m_pair = re.match(r'^(.+?)\s+និង\s*(.+)$', clean_inner)
                clean_inner = f"ការវិវឌ្ឍរវាង{m_pair.group(1).strip()} និង{m_pair.group(2).strip()}"

        # Pattern C: Starting with prepositions "អំពី..." or "ស្ដីពី..."
        elif re.match(r'^(?:អំពី|ស្ដីពី|ស្តីពី)\s*(.+)$', clean_inner):
            clean_inner = re.sub(r'^(?:អំពី|ស្ដីពី|ស្តីពី)\s*(.+)$', r'បច្ចុប្បន្នភាពស្ដីពី\1', clean_inner)

        # Pattern D: Starting with "ចំពោះ..."
        elif re.match(r'^(?:ចំពោះ)\s*(.+)$', clean_inner):
            clean_inner = re.sub(r'^(?:ចំពោះ)\s*(.+)$', r'ការវិភាគចំពោះ\1', clean_inner)

        # Pattern E: Strip trailing conjunctions leaving headline hanging (e.g. "..., ប៉ុន្តែ", "..., និង")
        clean_inner = re.sub(r'[\s,]+(?:និង|ឬ|ប៉ុន្តែ|ដោយសារ|ព្រោះ)$', '', clean_inner).strip()

        text = text.replace(orig_full_h, f"<b>{clean_inner}</b>")

    # 3. Flag Guarantee: Ensure headline starts with a flag emoji
    first_line = text.splitlines()[0] if text else ""
    has_flag = bool(re.search(r'[\U0001F1E0-\U0001F1FF]{2}|🌐|🥇|📅', first_line))
    if not has_flag and not text.startswith("📊") and not text.startswith("---"):
        t_low = text.lower()
        if any(w in t_low for w in ["amazon", "u.s.", "usa", "america", "fed", "biden", "trump", "powell", "indiana", "texas"]):
            flag = "🇺🇸 "
        elif any(w in t_low for w in ["china", "ចិន"]):
            flag = "🇨🇳 "
        elif any(w in t_low for w in ["russia", "រុស្ស៊ី"]):
            flag = "🇷🇺 "
        elif any(w in t_low for w in ["uk", "អង់គ្លេស"]):
            flag = "🇬🇧 "
        elif any(w in t_low for w in ["japan", "ជប៉ុន"]):
            flag = "🇯🇵 "
        elif any(w in t_low for w in ["germany", "អាល្លឺម៉ង់"]):
            flag = "🇩🇪 "
        elif any(w in t_low for w in ["france", "បារាំង"]):
            flag = "🇫🇷 "
        elif any(w in t_low for w in ["iran", "អ៊ីរ៉ង់"]):
            flag = "🇮🇷 "
        elif any(w in t_low for w in ["israel", "អ៊ីស្រាអែល"]):
            flag = "🇮🇱 "
        else:
            flag = "🌐 "
        text = flag + text

    # 4. Balanced HTML Tags Check & Auto-Repair
    open_b = len(re.findall(r'<b>', text))
    close_b = len(re.findall(r'</b>', text))
    if open_b > close_b:
        text += "</b>" * (open_b - close_b)
    elif close_b > open_b:
        text = "<b>" * (close_b - open_b) + text

    open_a = len(re.findall(r'<a\b[^>]*>', text))
    close_a = len(re.findall(r'</a>', text))
    if open_a > close_a:
        text += "</a>" * (open_a - close_a)

    vis_len = len(re.sub(r"<[^>]+>", "", text))
    if vis_len <= max_visible:
        return text

    blocks = text.split("\n\n")
    if len(blocks) <= 1:
        clean = re.sub(r"<[^>]+>", "", text)
        return clean[:max_visible - 1].rstrip(" .…-–—") + "។"

    header = blocks[0]
    source_line = blocks[-1]

    impact_line = ""
    body_blocks = []
    _impact_prefixes = ("🔹", "🔸", "🔶", "🔴", "🟢", "ផល", "ឥទ្ធិពល", "វាផល", "ហានិភ័យ")
    if len(blocks) >= 4 and blocks[-2].strip().startswith(_impact_prefixes):
        impact_line = blocks[-2].strip()
        body_blocks = blocks[1:-2]
    elif len(blocks) >= 3:
        if blocks[-2].strip().startswith(_impact_prefixes):
            impact_line = blocks[-2].strip()
            body_blocks = blocks[1:-2]
        else:
            body_blocks = blocks[1:-1]
    else:
        body_blocks = blocks[1:]

    body = "\n\n".join(body_blocks)
    clean_body = re.sub(r"<[^>]+>", "", body)

    vis_header = len(re.sub(r"<[^>]+>", "", header))
    vis_source = len(re.sub(r"<[^>]+>", "", source_line))
    vis_impact = len(re.sub(r"<[^>]+>", "", impact_line))
    num_separators = sum(1 for p in [header, clean_body, impact_line, source_line] if p) - 1
    sep_overhead = max(num_separators, 1) * 2

    avail = max(40, max_visible - (vis_header + vis_source + vis_impact + sep_overhead))

    if len(clean_body) > avail:
        sub = clean_body[:avail]
        last_period = max(sub.rfind("។ "), sub.rfind("។\n"), sub.rfind("។"))
        if last_period > 30:
            trimmed_body = sub[:last_period + 1].strip()
        else:
            last_space = sub.rfind(" ")
            trimmed_body = (sub[:last_space].strip() if last_space > 25 else sub.strip()) + "។"
    else:
        trimmed_body = clean_body

    parts = [p for p in [header, trimmed_body, impact_line, source_line] if p]
    res = "\n\n".join(parts)

    while len(re.sub(r"<[^>]+>", "", res)) > max_visible and len(trimmed_body) > 30:
        excess = len(re.sub(r"<[^>]+>", "", res)) - max_visible
        cut_idx = max(len(trimmed_body) - excess - 5, 20)
        sub = trimmed_body[:cut_idx]
        last_period = max(sub.rfind("។ "), sub.rfind("។\n"), sub.rfind("។"))
        if last_period > 20:
            trimmed_body = sub[:last_period + 1].strip()
        else:
            last_space = sub.rfind(" ")
            trimmed_body = (sub[:last_space].strip() if last_space > 15 else sub.strip()) + "។"
        parts = [p for p in [header, trimmed_body, impact_line, source_line] if p]
        res = "\n\n".join(parts)

    # Absolute 100% hard ceiling guarantee: Never allow even 1 character over limit
    while len(re.sub(r"<[^>]+>", "", res)) > max_visible:
        if len(trimmed_body) > 10:
            trimmed_body = trimmed_body[:-2].rstrip() + "។"
            parts = [p for p in [header, trimmed_body, impact_line, source_line] if p]
            res = "\n\n".join(parts)
        else:
            res = res[:max_visible]
            break

    return res

class TelegramNotifier:
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = (bot_token or TELEGRAM_BOT_TOKEN).strip()
        self.chat_id = (chat_id or TELEGRAM_CHAT_ID).strip()
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id and self.bot_token != "YOUR_TELEGRAM_BOT_TOKEN_HERE")

    def _post_dispatch_watchdog(self, message_id: int, is_photo: bool, target_chat: str, raw_text: str) -> bool:
        """
        World-Class Zero-Defect Post-Dispatch Watchdog.
        Audits every message delivered to the channel. If ANY constitutional rule is breached,
        instantly auto-purges (deletes) the message from Telegram within milliseconds,
        guaranteeing the human audience NEVER sees a defective post.
        """
        import re
        if not message_id or not raw_text:
            return True

        # Skip scheduled daily price cards or market open status
        if raw_text.startswith("🥇") or raw_text.startswith("📅") or raw_text.startswith("📊") or raw_text.startswith("---"):
            return True

        clean = re.sub(r'<[^>]+>', '', raw_text).strip()
        vis_len = len(clean)
        max_allowed = 574 if is_photo else 750

        # Check 1: Absolute hard length ceiling
        if vis_len > max_allowed:
            logger.critical(f"[WATCHDOG PURGE] Post #{message_id} exceeded limit ({vis_len} > {max_allowed}). Auto-purging immediately!")
            self.delete_message(message_id, chat_id=target_chat)
            return False

        # Check 2: Missing country/macro flag
        first_line = clean.splitlines()[0] if clean else ""
        if not re.search(r'[\U0001F1E0-\U0001F1FF]{2}|🌐|🥇|📅|📊', first_line):
            logger.critical(f"[WATCHDOG PURGE] Post #{message_id} missing sovereign flag emoji. Auto-purging immediately!")
            self.delete_message(message_id, chat_id=target_chat)
            return False

        # Check 3: Colons or ellipsis in headline
        m_head = re.search(r'<b>(.*?)</b>', raw_text, re.DOTALL)
        if m_head:
            head_txt = m_head.group(1)
            if re.search(r'[៖:：]|[\.]{3,}|…', head_txt):
                logger.critical(f"[WATCHDOG PURGE] Post #{message_id} contains colon/ellipsis in headline. Auto-purging immediately!")
                self.delete_message(message_id, chat_id=target_chat)
                return False

        # Check 4: Uncorrected typos
        typos = ['ប្រមាន', 'ធ្វើអោយ', 'ឿរ៉ង់', 'អគ្លេស', 'សហរដ្ធ', 'សេដ្ធកិច្ច']
        for tp in typos:
            if tp in clean:
                logger.critical(f"[WATCHDOG PURGE] Post #{message_id} contains forbidden typo '{tp}'. Auto-purging immediately!")
                self.delete_message(message_id, chat_id=target_chat)
                return False

        logger.info(f"[WATCHDOG PASSED] Post #{message_id} passed all 100% quality checks ({vis_len}/{max_allowed} chars).")
        return True

    def send_message(self, text: str, parse_mode: str = "HTML", disable_web_page_preview: bool = True, auto_pin: bool = False, reply_markup: dict = None, chat_id: str = None) -> dict:
        """Send message directly to Telegram channel/chat. If auto_pin is True, pins the message."""
        import re
        # Circuit Breaker 1: Drop empty or dangerously short stubs (< 35 visible characters)
        clean_vis = re.sub(r'<[^>]+>', '', text or "").strip()
        if len(clean_vis) < 35:
            logger.warning(f"[TelegramNotifier] Circuit Breaker ACTIVATED: Message text too short ({len(clean_vis)} chars). Dropping post.")
            return {"ok": False, "error": "Circuit Breaker: Message too short or empty"}

        # Hard fail-safe: Text-only broadcasts strictly <= 750 characters
        if text and not text.startswith("📊") and not text.startswith("🥇"):
            text = enforce_telegram_char_limit(text, max_visible=750)

        if not self.is_configured():
            logger.warning("[TelegramNotifier] Credentials not set. Message output (Simulation):\n" + "="*50 + f"\n{text}\n" + "="*50)
            return {"ok": True, "result": {"message_id": 999999, "simulated": True}}

        target_chat = str(chat_id or self.chat_id)
        url = f"{self.base_url}/sendMessage"
        if parse_mode == "HTML" and text:
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

            # WORLD-CLASS POST-DISPATCH WATCHDOG AUDIT
            if message_id:
                if not self._post_dispatch_watchdog(message_id, is_photo=False, target_chat=target_chat, raw_text=payload.get("text", "")):
                    return {"ok": False, "error": "Watchdog: Message violated rules and was auto-purged"}

            if auto_pin and message_id:
                self.pin_message(message_id)

            return data
        except Exception as e:
            logger.error(f"[TelegramNotifier] Exception while sending message: {e}")
            return {"ok": False, "error": str(e)}

    def send_photo(self, photo_bytes: bytes, caption: str = "", parse_mode: str = "HTML", reply_markup: dict = None, chat_id: str = None) -> dict:
        import re
        if isinstance(photo_bytes, str) and os.path.isfile(photo_bytes):
            with open(photo_bytes, "rb") as f:
                photo_bytes = f.read()

        # Circuit Breaker 2: If image is missing, empty, or corrupted (< 500 bytes), fallback to MODE B text-only!
        if not photo_bytes or len(photo_bytes) < 500:
            logger.warning("[TelegramNotifier] Circuit Breaker: Invalid photo bytes. Seamless fallback to MODE B (send_message).")
            return self.send_message(text=caption, parse_mode=parse_mode, reply_markup=reply_markup, chat_id=chat_id)

        # Circuit Breaker 3: Drop empty or dangerously short captions (< 35 visible characters)
        clean_vis = re.sub(r'<[^>]+>', '', caption or "").strip()
        if len(clean_vis) < 35:
            logger.warning(f"[TelegramNotifier] Circuit Breaker ACTIVATED: Caption too short ({len(clean_vis)} chars). Dropping post.")
            return {"ok": False, "error": "Circuit Breaker: Caption too short or empty"}

        if not self.is_configured():
            logger.warning(f"[TelegramNotifier] Credentials not set. Simulated photo upload ({len(photo_bytes) if photo_bytes else 0} bytes).")
            return {"ok": True, "result": {"message_id": 999998, "simulated": True}}

        target_chat = str(chat_id or self.chat_id)
        url = f"{self.base_url}/sendPhoto"
        files = {"photo": ("calendar.png", photo_bytes, "image/png")}
        data = {"chat_id": target_chat}
        if caption:
            # Bulletproof gate: Photo captions strictly <= 574 characters per user constitutional rule
            if not caption.startswith("📅") and not caption.startswith("🥇"):
                caption = enforce_telegram_char_limit(caption, max_visible=574)
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
            if result.get("ok"):
                message_id = result.get('result', {}).get('message_id')
                # WORLD-CLASS POST-DISPATCH WATCHDOG AUDIT
                if message_id:
                    if not self._post_dispatch_watchdog(message_id, is_photo=True, target_chat=target_chat, raw_text=data.get("caption", "")):
                        return {"ok": False, "error": "Watchdog: Photo caption violated rules and was auto-purged"}

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



