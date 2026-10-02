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
        Translates and interprets speech / FOMC Statement into instant Khmer intelligence:
        - tone: HAWKISH / DOVISH / NEUTRAL
        - tone_kh: Khmer description without leading emoji
        - key_quotes: Direct quote translation in Khmer
        - gold_pressure: Direct effect on XAU/USD
        - xau_bias: 🟢 Bullish / 🔴 Bearish
        - voice_script: Concise spoken text for Khmer Voice Note
        - speaker: Name of the speaker (Kevin Warsh, Jerome Powell, etc.)
        """
        if not self.is_available() or not speech_text:
            return None

        # Dynamically detect speaker
        speaker = "Fed"
        combined_text = f"{event_title} {speech_text}".lower()
        if "warsh" in combined_text:
            speaker = "Kevin Warsh"
        elif "powell" in combined_text:
            speaker = "Jerome Powell"
        elif "waller" in combined_text:
            speaker = "Christopher Waller"
        elif "bowman" in combined_text:
            speaker = "Michelle Bowman"
        elif "goolsbee" in combined_text:
            speaker = "Austan Goolsbee"
        elif "williams" in combined_text:
            speaker = "John Williams"

        prompt = (
            f"អ្នកគឺជា AI អធិប្បាយ និងបកប្រែផ្ទាល់ការថ្លែងសុន្ទរកថាថ្នាក់ដឹកនាំធនាគារកណ្តាលអាមេរិក Fed ({speaker} Live Speech Interpreter)។\n"
            f"ព្រឹត្តិការណ៍: {event_title}\n"
            f"សុន្ទរកថា/សេចក្តីថ្លែងការណ៍ភាសាអង់គ្លេស៖\n{speech_text}\n\n"
            f"ចូរធ្វើការបកប្រែ និងវិភាគជាភាសាខ្មែរផ្លូវការភ្លាមៗ ដោយត្រឡប់ JSON ដែលមាន Keys ដូចខាងក្រោម៖\n"
            f"- tone: 'DOVISH' ឬ 'HAWKISH' ឬ 'NEUTRAL'\n"
            f"- tone_kh: ពន្យល់អារម្មណ៍សម្លេងជាអក្សរធម្មតា គ្មាន emoji នៅខាងមុខ (ឧ. 'Dovish (ត្រៀមបញ្ចុះការប្រាក់/បន្ធូរបន្ថយ)' ឬ 'Hawkish (រឹតបន្តឹង/ដំឡើងការប្រាក់)' ឬ 'Neutral (ប្រុងប្រយ័ត្ន និងរង់ចាំមើលទិន្នន័យ)')\n"
            f"- key_quotes: សម្រង់សម្តី ឬចំណុចគន្លឹះសំខាន់បំផុតដែល {speaker} បានថ្លែង បកប្រែជាភាសាខ្មែរយ៉ាងរលូន (២-៣ ប្រយោគ)\n"
            f"- gold_pressure: ការពន្យល់ពីផលប៉ះពាល់ផ្ទាល់ និងសម្ពាធលើតម្លៃមាស XAUUSD ដោយផ្អែកលើប្រសាសន៍របស់ {speaker} (២ ប្រយោគ)\n"
            f"- xau_bias: '🟢 Bullish' ឬ '🔴 Bearish' ឬ '🟡 Mixed'\n"
            f"- voice_script: អត្ថបទសង្ខេប ២-៣ ប្រយោគជាភាសាខ្មែរយ៉ាងរលូន ច្បាស់ៗ សម្រាប់អានជាសំឡេង Voice Note ដោយ៖ ១. ចាប់ផ្តើមរៀបរាប់ពីប្រសាសន៍របស់ {speaker} និង ២. នៅចុងបញ្ចប់ ត្រូវតែប្រាប់ពីទិសដៅតម្លៃមាសឱ្យបានច្បាស់លាស់ជានិច្ច ឧទាហរណ៍៖ 'ដូច្នេះ ទិសដៅតម្លៃមាស ត្រូវបានរំពឹងថានឹងងើបឡើងខ្ពស់ Bullish ផ្តល់អាទិភាពលើឱកាស Buy' ឬ 'ដូច្នេះ ទិសដៅតម្លៃមាស ត្រូវបានរំពឹងថានឹងរងសម្ពាធធ្លាក់ចុះ Bearish ផ្តល់អាទិភាពលើឱកាស Sell' ឬ 'ដូច្នេះ ទិសដៅតម្លៃមាស អាចមានការប្រែប្រួលរលកធំៗ Sideway សូមប្រុងប្រយ័ត្ន'។"
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
                timeout=35
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                res_dict = json.loads(text)
                res_dict["speaker"] = speaker

                # Ensure voice script explicitly tells gold market direction
                v_s = res_dict.get("voice_script", "")
                if not any(k in v_s for k in ["ទិសដៅ", "Bullish", "Bearish", "Buy", "Sell"]):
                    b_str = res_dict.get("xau_bias", "").lower()
                    if "bullish" in b_str or res_dict.get("tone") == "DOVISH":
                        v_s += " ដូច្នេះ ទិសដៅតម្លៃមាស ត្រូវបានរំពឹងថានឹងងើបឡើងខ្ពស់ Bullish ផ្តល់អាទិភាពលើឱកាស Buy។"
                    elif "bearish" in b_str or res_dict.get("tone") == "HAWKISH":
                        v_s += " ដូច្នេះ ទិសដៅតម្លៃមាស ត្រូវបានរំពឹងថានឹងរងសម្ពាធធ្លាក់ចុះ Bearish ផ្តល់អាទិភាពលើឱកាស Sell។"
                    else:
                        v_s += " ដូច្នេះ ទិសដៅតម្លៃមាស អាចមានការប្រែប្រួលរលកធំៗ Sideway សូមប្រុងប្រយ័ត្នខ្ពស់។"
                try:
                    from formatters.khmer_formatter import sanitize_khmer_spelling
                    for k in ["key_quotes", "gold_pressure", "tone_kh", "voice_script"]:
                        if k in res_dict and isinstance(res_dict[k], str):
                            res_dict[k] = sanitize_khmer_spelling(res_dict[k])
                except Exception:
                    pass

                return res_dict
            else:
                logger.warning(f"[FomcSpeechInterpreter] Gemini API error: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.warning(f"[FomcSpeechInterpreter] Exception during speech interpretation: {e}")

        # Reliable instant fallback so speech broadcast NEVER fails
        return self._build_fallback_speech_interp(speech_text, event_title, speaker)

    def _build_fallback_speech_interp(self, speech_text: str, event_title: str, speaker: str) -> dict:
        """Rule-based instant fallback when AI is unavailable or network times out."""
        text_lower = f"{event_title} {speech_text}".lower()
        if any(w in text_lower for w in ["cut", "lower rate", "dovish", "ease", "slowdown", "cooling"]):
            tone = "DOVISH"
            tone_kh = "Dovish (ត្រៀមបញ្ចុះការប្រាក់/បន្ធូរបន្ថយ)"
            gold_pressure = f"ជំហរបន្ធូរបន្ថយរបស់លោក {speaker} អាចកាត់បន្ថយសម្ពាធលើរូបិយប័ណ្ណដុល្លារ និងជួយជំរុញឱ្យតម្លៃមាសងើបឡើងខ្ពស់។"
            bias = "🟢 Bullish"
            direction_voice = "ដូច្នេះ ទិសដៅតម្លៃមាស ត្រូវបានរំពឹងថានឹងងើបឡើងខ្ពស់ Bullish ផ្តល់អាទិភាពលើឱកាស Buy។"
        elif any(w in text_lower for w in ["hike", "raise", "hawkish", "higher for longer", "sticky inflation", "persistent"]):
            tone = "HAWKISH"
            tone_kh = "Hawkish (រឹតបន្តឹង/រក្សាការប្រាក់ខ្ពស់)"
            gold_pressure = f"ជំហររឹតបន្តឹងរបស់លោក {speaker} អាចជួយពង្រឹងកម្លាំងប្រាក់ដុល្លារ និងដាក់សម្ពាធទម្លាក់តម្លៃមាសក្នុងរយៈពេលខ្លី។"
            bias = "🔴 Bearish"
            direction_voice = "ដូច្នេះ ទិសដៅតម្លៃមាស ត្រូវបានរំពឹងថានឹងរងសម្ពាធធ្លាក់ចុះ Bearish ផ្តល់អាទិភាពលើឱកាស Sell។"
        else:
            tone = "NEUTRAL"
            tone_kh = "Neutral (ប្រុងប្រយ័ត្ន និងរង់ចាំមើលទិន្នន័យ)"
            gold_pressure = f"ការរក្សាជំហរប្រុងប្រយ័ត្នរបស់លោក {speaker} ធ្វើឱ្យទីផ្សារកាត់បន្ថយការរំពឹងទុកលើការប្រែប្រួលអត្រាការប្រាក់យ៉ាងគំហុក និងរង់ចាំទិន្នន័យជាក់ស្តែង។"
            bias = "🟡 Mixed"
            direction_voice = "ដូច្នេះ ទិសដៅតម្លៃមាស អាចមានការប្រែប្រួលរលកធំៗ និង Sideway សូមរង់ចាំការបំបែកតំបន់គន្លឹះ។"

        quote = f"ធនាគារកណ្តាល Fed បន្តតាមដានយ៉ាងយកចិត្តទុកដាក់លើទិន្នន័យសេដ្ឋកិច្ច និងអតិផរណា ដើម្បីកំណត់ទិសដៅគោលនយោបាយរូបិយវត្ថុដ៏ត្រឹមត្រូវ។"
        voice = f"លោក {speaker} បានថ្លែងបញ្ជាក់ថា ធនាគារកណ្តាល Fed នឹងបន្តតាមដានទិន្នន័យសេដ្ឋកិច្ចយ៉ាងហ្មត់ចត់។ {direction_voice}"

        return {
            "tone": tone,
            "tone_kh": tone_kh,
            "key_quotes": quote,
            "gold_pressure": gold_pressure,
            "xau_bias": bias,
            "voice_script": voice,
            "speaker": speaker
        }


