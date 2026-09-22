import json
import logging
import time
import requests

from config import (
    GEMINI_API_KEY, GEMINI_MODEL, USE_GEMINI,
    GEMINI_MIN_INTERVAL, GEMINI_COOLDOWN,
)
from analyzers.macro_analyzer import MacroAnalyzer

logger = logging.getLogger(__name__)

# Keys must match what KhmerFormatter expects from an analysis dict.
_ANALYSIS_KEYS = [
    "what_happened", "why_it_matters", "usd_impact",
    "rate_yield_impact", "xau_pressure", "bias"
]

_SYSTEM_RULES = (
    "អ្នកជាអ្នកវិភាគទីផ្សារមាស (XAUUSD) ជំនាញ។ ចូរវិភាគព័ត៌មានសេដ្ឋកិច្ច/ភូមិសាស្ត្រនយោបាយ "
    "និងផលប៉ះពាល់របស់វាលើតម្លៃមាស។ សរសេរជាភាសាខ្មែរសាមញ្ញ ងាយយល់ ប៉ុន្តែត្រឹមត្រូវតាមគោលការណ៍ម៉ាក្រូ។ "
    "កុំអះអាងថាទាយទីផ្សារបាន 100% — ប្រើពាក្យប្រយ័ត្នប្រយែងដូចជា 'អាច' 'មានសម្ពាធ' 'ទំនោរ'។ "
    "xau_pressure ត្រូវចាប់ផ្តើមដោយ 🟢 (Bullish) ឬ 🔴 (Bearish) ឬ 🟡 (Mixed)។ "
    "bias ត្រូវជា 🟢 Bullish ឬ 🔴 Bearish ឬ 🟡 Mixed / Unclear ។"
)


def _json_schema():
    props = {k: {"type": "string"} for k in _ANALYSIS_KEYS}
    return {
        "type": "OBJECT",
        "properties": props,
        "propertyOrdering": _ANALYSIS_KEYS,
    }


def _extract_text(data: dict) -> str:
    """Concatenates all text parts from a Gemini response.

    Thinking models (gemini-3.x) may return multiple parts; only the text
    parts carry the answer, so join them and ignore any thoughtSignature.
    """
    parts = data["candidates"][0]["content"].get("parts", [])
    return "".join(p.get("text", "") for p in parts if p.get("text"))


class GeminiAnalyzer:
    """Natural-language Khmer market analysis via the Gemini REST API.

    Falls back to the rule-based MacroAnalyzer whenever Gemini is disabled,
    unconfigured, or returns an error — so the bot never crashes on AI failure.
    """

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = (api_key or GEMINI_API_KEY).strip()
        self.model = (model or GEMINI_MODEL).strip()
        self.endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        )

    # Throttle state is class-level (process-wide) so every GeminiAnalyzer
    # shares one cooldown and one min-interval clock.
    _last_request_ts = 0.0
    _cooldown_until = 0.0

    def _throttle_wait(self):
        """Enforces the quota cooldown and the minimum spacing between calls.

        Raises immediately if we are inside a 429 cooldown so callers fall back
        to rules without burning another request; otherwise sleeps just enough
        to respect GEMINI_MIN_INTERVAL before the next call.
        """
        now = time.time()
        if now < GeminiAnalyzer._cooldown_until:
            remaining = int(GeminiAnalyzer._cooldown_until - now)
            raise RuntimeError(f"Gemini cooldown active ({remaining}s left) after quota limit")
        gap = now - GeminiAnalyzer._last_request_ts
        if gap < GEMINI_MIN_INTERVAL:
            time.sleep(GEMINI_MIN_INTERVAL - gap)
        GeminiAnalyzer._last_request_ts = time.time()

    def _trip_cooldown(self, seconds: float = None):
        seconds = seconds if seconds is not None else GEMINI_COOLDOWN
        GeminiAnalyzer._cooldown_until = time.time() + seconds
        logger.warning(
            f"[GeminiAnalyzer] quota limit hit — pausing Gemini for {int(seconds)}s, "
            f"using rule-based fallback meanwhile."
        )

    def is_available(self) -> bool:
        return bool(USE_GEMINI and self.api_key and self.api_key != "YOUR_GEMINI_API_KEY_HERE")

    def _post(self, payload: dict, max_retries: int = 4) -> dict:
        """POSTs to Gemini with retry on transient errors (500/503).

        gemini-3.x flash models return 503 under high demand; a short retry
        loop with backoff makes the bot resilient instead of silently
        falling back to rules on a temporary blip.

        HTTP 429 is NOT retried — it means the free-tier quota is exhausted,
        so retrying just wastes requests. Instead we trip a cooldown and let
        the caller fall back to rules until the quota window resets.
        """
        self._throttle_wait()
        last_exc = None
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    self.endpoint,
                    params={"key": self.api_key},
                    json=payload,
                    timeout=40,
                )
                GeminiAnalyzer._last_request_ts = time.time()
                if resp.status_code == 429:
                    self._trip_cooldown()
                    raise RuntimeError(f"HTTP 429: {resp.text[:120]}")
                if resp.status_code in (500, 503):
                    last_exc = RuntimeError(f"HTTP {resp.status_code}: {resp.text[:120]}")
                    time.sleep(1.5 * (attempt + 1))
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as e:
                last_exc = e
                time.sleep(1.5 * (attempt + 1))
        raise last_exc if last_exc else RuntimeError("Gemini call failed")

    def _call(self, prompt: str) -> dict:
        """Sends one prompt to Gemini and returns the parsed JSON object."""
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "systemInstruction": {"role": "system", "parts": [{"text": _SYSTEM_RULES}]},
            "generationConfig": {
                "temperature": 0.3,
                "responseMimeType": "application/json",
                "responseSchema": _json_schema(),
                # gemini-3.x are thinking models: they spend tokens reasoning
                # before answering. A low cap truncates the real output.
                "maxOutputTokens": 4000,
            },
        }
        data = self._post(payload)
        return json.loads(_extract_text(data))

    def _normalize(self, raw: dict) -> dict:
        out = {}
        for k in _ANALYSIS_KEYS:
            val = str(raw.get(k, "")).strip()
            out[k] = val if val else "កំពុងតាមដាន។"
        return out

    def analyze_breaking_news(self, title: str, description: str = "") -> dict:
        if not self.is_available():
            return MacroAnalyzer.analyze_breaking_news(title, description)
        prompt = (
            f"វិភាគព័ត៌មានបន្ទាន់ខាងក្រោម និងផលប៉ះពាល់លើមាស (XAUUSD)៖\n"
            f"ចំណងជើង: {title}\nខ្លឹមសារ: {description}\n\n"
            f"ត្រឡប់ JSON ដែលមាន fields: {', '.join(_ANALYSIS_KEYS)}។\n"
            f"- what_happened: 1-2 ប្រយោគខ្លី (អតិបរមា 110 តួអក្សរ)\n"
            f"- why_it_matters: 2-3 ប្រយោគ ពន្យល់យន្តការ Fed rate expectations, USD, real yields, risk sentiment (អតិបរមា 200 តួអក្សរ)\n"
            f"- usd_impact: 1 ប្រយោគ (អតិបរមា 80 តួអក្សរ)\n"
            f"- rate_yield_impact: 1 ប្រយោគ (អតិបរមា 80 តួអក្សរ)\n"
            f"- xau_pressure: ចាប់ផ្តើមដោយ 🟢/🔴/🟡 បូក 1 ប្រយោគ (អតិបរមា 110 តួអក្សរ)\n"
            f"- bias: 🟢 Bullish / 🔴 Bearish / 🟡 Mixed / Unclear\n"
            f"សរសេរទាំងអស់ជាភាសាខ្មែរ ខ្លី ច្បាស់លាស់ និងងាយយល់ — គោរពដែនកំណត់តួអក្សរខាងលើឱ្យបានម៉ឺងម៉ាត់។"
        )
        try:
            return self._normalize(self._call(prompt))
        except Exception as e:
            logger.warning(f"[GeminiAnalyzer] breaking_news failed, falling back to rules: {e}")
            return MacroAnalyzer.analyze_breaking_news(title, description)

    def analyze_actual_vs_forecast(self, event_name: str, actual: str, forecast: str, previous: str) -> dict:
        if not self.is_available():
            return MacroAnalyzer.analyze_actual_vs_forecast(event_name, actual, forecast, previous)
        prompt = (
            f"ទិន្នន័យសេដ្ឋកិច្ចបានចេញផ្សាយ៖\n"
            f"- ព្រឹត្តិការណ៍: {event_name}\n"
            f"- ជាក់ស្តែង (Actual): {actual}\n"
            f"- ការព្យាករណ៍ (Forecast): {forecast}\n"
            f"- ទិន្នន័យមុន (Previous): {previous}\n\n"
            f"ប្រៀបធៀប Actual vs Forecast ហើយវិភាគផលប៉ះពាល់លើ USD និងមាស។ "
            f"ត្រឡប់ JSON ដែលមាន fields: {', '.join(_ANALYSIS_KEYS)}។"
        )
        try:
            return self._normalize(self._call(prompt))
        except Exception as e:
            logger.warning(f"[GeminiAnalyzer] actual_vs_forecast failed, falling back to rules: {e}")
            return MacroAnalyzer.analyze_actual_vs_forecast(event_name, actual, forecast, previous)

    def summarize_daily_price(self, price_data: dict) -> str:
        """Returns a short 1-2 sentence Khmer market note for the daily price message.

        Returns an empty string if Gemini is unavailable, so the caller can skip it.
        """
        if not self.is_available():
            return ""
        prompt = (
            f"សរសេរសេចក្តីសង្ខេបខ្លី (1-2 ប្រយោគ) ជាភាសាខ្មែរអំពីស្ថានភាពតម្លៃមាសថ្ងៃនេះ៖\n"
            f"- តម្លៃ 1 oz: ${price_data.get('price_oz', 0):,.2f}\n"
            f"- បម្រែបម្រួល: {price_data.get('change', 0):,.2f} ({price_data.get('change_pct', 0):.2f}%)\n"
            f"កុំប្រើ JSON កុំប្រើ emoji ច្រើន។ សរសេរតែអត្ថបទសង្ខេប។"
        )
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "systemInstruction": {"role": "system", "parts": [{"text": _SYSTEM_RULES}]},
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2000},
        }
        try:
            data = self._post(payload)
            return _extract_text(data).strip()
        except Exception as e:
            logger.warning(f"[GeminiAnalyzer] summarize_daily_price failed: {e}")
            return ""
