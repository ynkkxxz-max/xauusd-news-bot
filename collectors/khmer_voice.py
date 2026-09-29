import logging
import requests
import urllib.parse
import re

logger = logging.getLogger(__name__)

class KhmerVoiceSynthesizer:
    """
    High-Quality Natural Khmer Voice Generator.
    Converts daily gold price and Fed speeches into authoritative, deep Male audio voice notes (.mp3)
    matching Kevin Warsh / central bank leaders, ready for instant broadcast to Telegram.
    """
    TTS_URL = "https://translate.google.com/translate_tts"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://translate.google.com/"
        }

    @staticmethod
    def humanize_khmer_text(text: str) -> str:
        """
        Replaces English financial words and foreign names with natural Khmer phonetics
        and adds natural breath pauses so the Neural Voice speaks smoothly like a real human broadcaster.
        """
        replacements = [
            (r"\bKevin Warsh\b", "ខេវិន វ៉ាស"),
            (r"\bWarsh\b", "វ៉ាស"),
            (r"\bJerome Powell\b", "ជេរ៉ូម ផៅវែល"),
            (r"\bPowell\b", "ផៅវែល"),
            (r"\bChristopher Waller\b", "គ្រីស្តូហ្វ័រ វ៉លលើ"),
            (r"\bWaller\b", "វ៉លលើ"),
            (r"\bMichelle Bowman\b", "មីសែល បូមែន"),
            (r"\bBowman\b", "បូមែន"),
            (r"\bAustan Goolsbee\b", "អូស្តិន ហ្គូលប៊ី"),
            (r"\bJohn Williams\b", "ចន វីលៀម"),
            (r"\bFederal Reserve\b", "ធនាគារកណ្តាល ហ្វេត"),
            (r"\bFed\b", "ហ្វេត"),
            (r"\bFOMC\b", "អេហ្វអូមស៊ី"),
            (r"\bBullish\b", "ប៊ូលីស"),
            (r"\bBearish\b", "ប៊ែរីស"),
            (r"\bSideway\b", "សាយវ៉េ"),
            (r"\bBuy\b", "ទិញ បាយ"),
            (r"\bSell\b", "លក់ ស៊ែល"),
            (r"\bXAUUSD\b", "មាស"),
            (r"\bUSD\b", "ដុល្លារ"),
            (r"\bCPI\b", "ស៊ីភីអាយ"),
            (r"\bNFP\b", "អិនអេហ្វភី"),
        ]
        res = text
        for pat, repl in replacements:
            res = re.sub(pat, repl, res, flags=re.IGNORECASE)
        # Ensure punctuation has natural breathing spaces
        res = re.sub(r"([។!?])", r"\1 ", res)
        res = re.sub(r"\s+", " ", res).strip()
        return res

    def text_to_speech(self, text: str, voice: str = "male", pitch: str = "+0Hz", rate: str = "+0%", volume: str = "+30%") -> bytes:
        """
        Converts Khmer text into an MP3 audio bytes stream using Microsoft Edge Neural Voice.
        Defaults to an authentic human news anchor voice ('km-KH-PisethNeural', pitch='+0Hz', rate='+0%', volume='+30%')
        with phonetic Khmer transliteration for 100% natural, human-like speech (Zero robotic metallic artifacts).
        Falls back to Google TTS if edge-tts network is unreachable.
        """
        if not text:
            return b""

        # 0. Convert foreign terms to natural Khmer phonetics
        humanized = self.humanize_khmer_text(text)

        # Clean HTML tags and markdown symbols
        clean_text = re.sub(r"<[^>]+>", "", humanized)
        clean_text = re.sub(r"[*#_`•\n]+", " ", clean_text).strip()
        clean_text = re.sub(r"\s+", " ", clean_text)

        # 1. Try Microsoft Edge Neural Male Voice (Natural Human Newscaster Style)
        try:
            voice_name = "km-KH-PisethNeural" if voice == "male" else "km-KH-SreymomNeural"
            audio_bytes = self._synthesize_edge_tts(clean_text, voice=voice_name, pitch=pitch, rate=rate, volume=volume)
            if audio_bytes and len(audio_bytes) > 500:
                return audio_bytes
        except Exception as e:
            logger.warning(f"[KhmerVoiceSynthesizer] Edge TTS male voice failed, using fallback: {e}")

        # 2. Fallback to Google Translate TTS
        return self._synthesize_google_tts(clean_text)

    def _synthesize_edge_tts(self, text: str, voice: str = "km-KH-PisethNeural", pitch: str = "+0Hz", rate: str = "+0%", volume: str = "+30%") -> bytes:
        """Synthesizes high-fidelity neural voice using edge-tts with natural human prosody and crystal-clear articulation."""
        import asyncio
        import edge_tts
        import concurrent.futures

        async def _run():
            comm = edge_tts.Communicate(text, voice=voice, pitch=pitch, rate=rate, volume=volume)
            audio = bytearray()
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    audio.extend(chunk["data"])
            return bytes(audio)

        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    return pool.submit(asyncio.run, _run()).result(timeout=18)
            else:
                return asyncio.run(_run())
        except Exception as e:
            logger.warning(f"[KhmerVoiceSynthesizer] edge-tts error: {e}")
            return b""

    def _synthesize_google_tts(self, clean_text: str) -> bytes:
        """Fallback Google TTS."""
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
                logger.warning(f"[KhmerVoiceSynthesizer] Error in fallback chunk: {e}")

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
        local_market = price_data.get("local_market", {})
        local_sell = local_market.get("damlung_sell", 0.0)
        local_buy = local_market.get("damlung_buy", 0.0)
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
