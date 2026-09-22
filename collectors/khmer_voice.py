import logging
import requests
import urllib.parse
import re

logger = logging.getLogger(__name__)

class KhmerVoiceSynthesizer:
    """
    High-Quality Natural Khmer Voice Generator.
    Converts daily gold price and market wrap-up summaries into clear Khmer audio voice notes (.mp3)
    ready for instant broadcast to Telegram channel as Voice Notes.
    """
    TTS_URL = "https://translate.google.com/translate_tts"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://translate.google.com/"
        }

    def text_to_speech(self, text: str) -> bytes:
        """
        Converts Khmer text into an MP3 audio bytes stream.
        Handles text chunking to respect TTS character limits.
        """
        if not text:
            return b""

        # Clean HTML tags and markdown symbols
        clean_text = re.sub(r"<[^>]+>", "", text)
        clean_text = re.sub(r"[*#_`•\n]+", " ", clean_text).strip()
        clean_text = re.sub(r"\s+", " ", clean_text)

        # Chunk text by sentences or punctuation (max ~150 chars per request)
        chunks = self._chunk_text(clean_text, max_len=130)
        audio_stream = bytearray()

        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            try:
                encoded = urllib.parse.quote(chunk)
                url = f"{self.TTS_URL}?ie=UTF-8&q={encoded}&tl=km&client=tw-ob"
                resp = requests.get(url, headers=self.headers, timeout=12)
                if resp.status_code == 200 and len(resp.content) > 100:
                    audio_stream.extend(resp.content)
            except Exception as e:
                logger.warning(f"[KhmerVoiceSynthesizer] Error synthesizing chunk: {e}")

        return bytes(audio_stream)

    def _chunk_text(self, text: str, max_len: int = 130) -> list:
        """Splits Khmer text into speakable segments."""
        words = text.split(" ")
        chunks = []
        current = ""
        for w in words:
            if len(current) + len(w) + 1 <= max_len:
                current += (" " if current else "") + w
            else:
                if current:
                    chunks.append(current)
                current = w
        if current:
            chunks.append(current)
        return chunks

    def build_morning_voice_script(self, price_data: dict) -> str:
        """Constructs a natural, fluent Khmer spoken script for the 7:00 AM Morning Gold Brief."""
        oz = round(price_data.get("price_oz", 0.0), 2)
        local_sell = price_data.get("local_damlung_sell", 0.0)
        local_buy = price_data.get("local_damlung_buy", 0.0)
        chg = price_data.get("change", 0.0)
        trend = "កើនឡើង" if chg >= 0 else "ធ្លាក់ចុះ"
        chg_abs = abs(round(chg, 2))

        script = (
            f"សូមជម្រាបសួរ នេះជាព័ត៌មានហាងឆេងមាសប្រចាំព្រឹកនេះ។ "
            f"តម្លៃមាសអន្តរជាតិបច្ចុប្បន្ន ស្ថិតនៅប្រមាណ {oz:,.0f} ដុល្លារក្នុងមួយអោន ដែលមានការ {trend} {chg_abs} ដុល្លារ។ "
            f"សម្រាប់ទីផ្សារក្នុងស្រុក មាសគីឡូទិញចូល {local_buy:,.0f} ដុល្លារ និងលក់ចេញ {local_sell:,.0f} ដុល្លារក្នុងមួយដំឡឹង។ "
            f"សូមជូនពរបងប្អូនជួញដូរប្រកបដោយសុវត្ថិភាព និងទទួលបានប្រាក់ចំណេញគ្រប់ៗគ្នា។"
        )
        return script
