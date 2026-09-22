import logging
import json
import requests
from config import GEMINI_API_KEY, GEMINI_MODEL, USE_GEMINI

logger = logging.getLogger(__name__)

class FomcSpeechInterpreter:
    """
    ⚡ AI Live Speech & Statement Interpreter for Federal Reserve FOMC & Jerome Powell.
    Captures live Fed statements, press conference remarks, and speech excerpts,
    analyzes tone sentiment (Hawkish / Dovish) using Gemini AI within seconds,
    and produces instant Khmer translation + Voice Audio broadcast scripts.
    """
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model = GEMINI_MODEL
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def is_available(self) -> bool:
        return bool(USE_GEMINI and self.api_key and self.api_key != "YOUR_GEMINI_API_KEY_HERE")

    def interpret_powell_speech(self, speech_text: str, event_title: str = "FOMC Press Conference") -> dict:
        """
        Translates and interprets Powell's speech / FOMC Statement into instant Khmer intelligence:
        - tone: HAWKISH / DOVISH / NEUTRAL
        - tone_kh: Khmer description with emoji
        - key_quotes: Direct quote translation in Khmer
        - gold_pressure: Direct effect on XAU/USD
        - xau_bias: 🟢 Bullish / 🔴 Bearish
        - voice_script: Concise spoken text for Khmer Voice Note
        """
        if not self.is_available() or not speech_text:
            return None

        prompt = (
            f"អ្នកគឺជា AI អធិប្បាយ និងបកប្រែផ្ទាល់ការថ្លែងសុន្ទរកថាប្រធានធនាគារកណ្តាលអាមេរិក Fed (Jerome Powell Live Interpreter)។\n"
            f"ព្រឹត្តិការណ៍: {event_title}\n"
            f"សុន្ទរកថា/សេចក្តីថ្លែងការណ៍ភាសាអង់គ្លេស៖\n{speech_text}\n\n"
            f"ចូរធ្វើការបកប្រែ និងវិភាគជាភាសាខ្មែរផ្លូវការភ្លាមៗ ដោយត្រឡប់ JSON ដែលមាន Keys ដូចខាងក្រោម៖\n"
            f"- tone: 'DOVISH' ឬ 'HAWKISH' ឬ 'NEUTRAL'\n"
            f"- tone_kh: ពន្យល់អារម្មណ៍សម្លេង (ឧ. '🟢 Dovish (ត្រៀមបញ្ចុះការប្រាក់/បន្ធូរបន្ថយ)' ឬ '🔴 Hawkish (រឹតបន្តឹង/ដំឡើងការប្រាក់)')\n"
            f"- key_quotes: សម្រង់សម្តី ឬចំណុចគន្លឹះសំខាន់បំផុតដែល Powell បានថ្លែង បកប្រែជាភាសាខ្មែរយ៉ាងរលូន (២-៣ ប្រយោគ)\n"
            f"- gold_pressure: ការពន្យល់ពីផលប៉ះពាល់ផ្ទាល់ និងសម្ពាធលើតម្លៃមាស XAUUSD (២ ប្រយោគ)\n"
            f"- xau_bias: '🟢 Bullish' ឬ '🔴 Bearish' ឬ '🟡 Mixed'\n"
            f"- voice_script: អត្ថបទសង្ខេបខ្លី ២ ប្រយោគ ជាភាសាខ្មែរសម្រាប់អានជាសំឡេងនិយាយ Voice Note"
        )

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        try:
            resp = requests.post(
                self.endpoint,
                params={"key": self.api_key},
                json=payload,
                timeout=18
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            else:
                logger.warning(f"[FomcSpeechInterpreter] Gemini API error: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.warning(f"[FomcSpeechInterpreter] Exception during speech interpretation: {e}")

        return None
