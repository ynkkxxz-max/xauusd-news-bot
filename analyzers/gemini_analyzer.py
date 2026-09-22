import json
import logging
import time
import requests

from config import (
    GEMINI_API_KEY, GEMINI_MODEL, USE_GEMINI,
    GEMINI_MIN_INTERVAL, GEMINI_COOLDOWN,
)

logger = logging.getLogger(__name__)

# Keys must match what KhmerFormatter expects from an analysis dict.
_ANALYSIS_KEYS = [
    "what_happened", "why_it_matters", "usd_impact",
    "rate_yield_impact", "xau_pressure", "bias", "is_clear"
]

_SYSTEM_RULES = (
    "អ្នកគឺជាប្រធានអ្នកយុទ្ធសាស្ត្រវិភាគម៉ាក្រូសេដ្ឋកិច្ច និងទីផ្សារមាស (Chief Macro & Gold Strategist) ថ្នាក់ស្ថាប័នកំពូលពិភពលោក។ "
    "ចូរវិភាគព័ត៌មានឱ្យបានឆ្លាតវៃ មុតស្រួច និងស៊ីជម្រៅបំផុត ដោយពន្យល់ពីទំនាក់ទំនងស្មុគស្មាញរវាង ភូមិសាស្ត្រនយោបាយ តម្លៃថាមពល/ប្រេង "
    "អតិផរណា កម្លាំងសន្ទស្សន៍ប្រាក់ដុល្លារ (DXY) អត្រាការប្រាក់ Fed និងទំហំតម្រូវការទ្រព្យសុវត្ថិភាព (Safe-haven) ចំពោះមាស។ "
    "សរសេរជាភាសាខ្មែរផ្លូវការ ពិរោះ រលូន មានអត្ថន័យជ្រាលជ្រៅ និងច្បាស់លាស់បំផុត។ "
    "ហាមកាត់ខ្លី ឬឆ្លើយជាគំរូទូទៅដដែលៗ (generic)។ ត្រូវចាប់យកចំណុចពិសេស និងខ្លឹមសារពិត ១០០%។ "
    "លក្ខខណ្ឌពិសេស៖ ប្រសិនបើព័ត៌មាននោះមិនច្បាស់លាស់ ព័ត៌មានតូចតាច ឬគ្មានផលប៉ះពាល់ជាក់ស្តែងលើទីផ្សារមាស ត្រូវកំណត់ is_clear = false "
    "ដើម្បីកុំឱ្យផ្ញើសាររំខានចូល Channel Telegram ឱ្យសោះ! កំណត់ is_clear = true លុះត្រាតែព័ត៌មាននោះច្បាស់លាស់ មានទម្ងន់ និងប៉ះពាល់ផ្ទាល់ដល់មាស។"
)


def _json_schema():
    props = {k: {"type": "string"} for k in _ANALYSIS_KEYS}
    props["is_clear"] = {"type": "boolean"}
    return {
        "type": "OBJECT",
        "properties": props,
        "propertyOrdering": _ANALYSIS_KEYS,
    }


def breaking_prompt(title: str, description: str) -> str:
    return (
        f"អ្នកគឺជាអ្នកជំនាញវិភាគម៉ាក្រូសេដ្ឋកិច្ច និងទីផ្សារមាស (XAUUSD) ថ្នាក់កំពូល។\n"
        f"ព័ត៌មានជាក់ស្តែង៖\n"
        f"ចំណងជើង: {title}\nខ្លឹមសារ: {description}\n\n"
        f"ចូរវិភាគព័ត៌មាននេះឱ្យបានស៊ីជម្រៅ ដោយចាប់យកចំណុចពិសេស សំខាន់ៗ និងខ្លឹមសារស្នូលនៃសាច់រឿងឱ្យបានពេញលេញ ហាមកាត់សាច់រឿងខ្លីពេក "
        f"(ទោះជាការលើកឡើងរបស់មេដឹកនាំដូចជា Trump, ភាពតានតឹងភូមិសាស្ត្រនយោបាយដូចជាអ៊ីរ៉ង់, FOMC/Fed, CPI, NFP, PCE, "
        f"ឬការវិវត្តបច្ចេកវិទ្យា AI ដូចជា Super Intelligence/Nvidia ដែលជះឥទ្ធិពលលើទីផ្សារ)។\n\n"
        f"ត្រឡប់ JSON ដែលមាន fields ដូចតទៅ (ជាភាសាខ្មែរផ្លូវការ ពិរោះ មានខ្លឹមសារពេញលេញ ច្បាស់លាស់):\n"
        f"- what_happened: រៀបរាប់សាច់រឿងពិតជាក់ស្ដែងដែលទើបកើតឡើងឱ្យបានក្បោះក្បាយ ចាប់យកចំណុចពិសេស និងខ្លឹមសារដើមឱ្យបានច្បាស់ មិនកាត់ខ្លីពេក (២-៤ ប្រយោគ)។\n"
        f"- why_it_matters: ពន្យល់ពីសារៈសំខាន់ យន្តការសេដ្ឋកិច្ច និងមូលហេតុដែលព្រឹត្តិការណ៍នេះល្អ ឬអាក្រក់ចំពោះទីផ្សារ (អតិផរណា, អត្រាការប្រាក់ Fed, ទំនោរ Safe-haven ឬការបង្វែរសាច់ប្រាក់ក្នុងទីផ្សារ) (២-៤ ប្រយោគ)។\n"
        f"- usd_impact: ផលប៉ះពាល់លើកម្លាំងប្រាក់ដុល្លារ DXY (ឡើង, ចុះ, ឬ Rangebound រួមទាំងមូលហេតុពិត) (១-២ ប្រយោគ)។\n"
        f"- rate_yield_impact: សម្ពាធលើអត្រាផលប័ត្របំណុលរដ្ឋាភិបាលអាមេរិក (US Treasury Yields) និងអារម្មណ៍វិនិយោគិន Risk Sentiment (១-២ ប្រយោគ)។\n"
        f"- xau_pressure: ចាប់ផ្តើមដោយ 👉 🟢 ឬ 👉 🔴 ឬ 👉 🟡 បូកនឹងការពន្យល់សម្ពាធពិតលើតម្លៃមាស (XAUUSD) ឱ្យចំកាលៈទេសៈ (១-២ ប្រយោគ)។\n"
        f"- bias: 🟢 Bullish / 🔴 Bearish / 🟡 Mixed / Unclear\n"
        f"- is_clear: true (ប្រសិនបើព័ត៌មានមានទម្ងន់ច្បាស់លាស់ មានឥទ្ធិពលជាក់ស្តែងលើមាស) ឬ false (ប្រសិនបើព័ត៌មានស្រពេចស្រពិល មិនទាន់ច្បាស់លាស់ ឬគ្មានឥទ្ធិពលច្បាស់ក្រឡែត)\n"
        f"ហាមឆ្លើយតបជាគំរូដដែលៗ ឬ generic! ប្រសិនបើមិនច្បាស់លាស់ ត្រូវដាក់ is_clear = false ដើម្បីកុំផ្ញើចូល Channel Telegram។"
    )



def actual_prompt(event_name: str, actual: str, forecast: str, previous: str) -> str:
    return (
        f"ទិន្នន័យសេដ្ឋកិច្ចបានចេញផ្សាយ៖\n"
        f"- ព្រឹត្តិការណ៍: {event_name}\n"
        f"- ជាក់ស្តែង (Actual): {actual}\n"
        f"- ការព្យាករណ៍ (Forecast): {forecast}\n"
        f"- ទិន្នន័យមុន (Previous): {previous}\n\n"
        f"ប្រៀបធៀប Actual vs Forecast ហើយវិភាគផលប៉ះពាល់លើ USD និងមាស។ "
        f"ត្រឡប់ JSON ដែលមាន fields: {', '.join(_ANALYSIS_KEYS)}។ "
        f"សរសេរជាភាសាខ្មែរ ខ្លី ច្បាស់លាស់ (what_happened ≤110 តួ, why_it_matters ≤200 តួ, ផ្សេងទៀត ≤80-110 តួ)។"
    )


def summary_prompt(price_data: dict) -> str:
    loc = price_data.get("local_market", {})
    return (
        f"អ្នកគឺជាអ្នកជំនាញវិភាគទីផ្សារមាស។ ចូរសរសេរសេចក្តីសង្ខេបខ្លី (២-៣ ប្រយោគ មិនលើសពី ២០០ តួអក្សរ) ជាភាសាខ្មែរផ្លូវការ ពិរោះ អំពីស្ថានភាពតម្លៃមាសថ្ងៃនេះ៖\n"
        f"- អន្តរជាតិ (XAUUSD): ${price_data.get('price_oz', 0):,.2f}/oz, បម្រែបម្រួល: {price_data.get('change', 0):,.2f} ({price_data.get('change_pct', 0):.2f}%)\n"
        f"- ទីផ្សារកម្ពុជា: មាសគីឡូ ២៤K លក់ ${loc.get('damlung_sell', 0):,.2f}/តម្លឹង (ទិញ ${loc.get('damlung_buy', 0):,.2f})\n"
        f"ពន្យល់ពីទិសដៅទីផ្សារសកល និងសម្ពាធលើហាងឆេងក្នុងស្រុក។ កុំប្រើ JSON កុំប្រើ emoji ច្រើន។ សរសេរតែអត្ថបទសង្ខេបសុទ្ធ។"
    )


def normalize_analysis(raw: dict) -> dict:
    out = {}
    for k in _ANALYSIS_KEYS:
        val = str(raw.get(k, "")).strip()
        out[k] = val if val else "កំពុងតាមដាន។"
    return out


def _extract_text(data: dict) -> str:
    """Concatenates all text parts from a Gemini response.

    Thinking models (gemini-3.x) may return multiple parts; only the text
    parts carry the answer, so join them and ignore any thoughtSignature.
    """
    parts = data["candidates"][0]["content"].get("parts", [])
    return "".join(p.get("text", "") for p in parts if p.get("text"))


class GeminiAnalyzer:
    """Natural-language Khmer market analysis via the Gemini REST API.

    Returns None when Gemini is disabled, unconfigured, or errors out, so the
    AnalyzerChain can try the next provider (and ultimately the rule-based
    MacroAnalyzer) without the bot ever crashing on AI failure.
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

    def _post(self, payload: dict, max_retries: int = 2) -> dict:
        """POSTs to Gemini with fast-fail retry on transient errors (500/503)."""
        self._throttle_wait()
        last_exc = None
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    self.endpoint,
                    params={"key": self.api_key},
                    json=payload,
                    timeout=15,
                )
                GeminiAnalyzer._last_request_ts = time.time()
                if resp.status_code == 429:
                    self._trip_cooldown()
                    raise RuntimeError(f"HTTP 429: {resp.text[:120]}")
                if resp.status_code in (500, 503):
                    last_exc = RuntimeError(f"HTTP {resp.status_code}: {resp.text[:120]}")
                    time.sleep(1.0)
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as e:
                last_exc = e
                time.sleep(1.0)
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
        return normalize_analysis(raw)

    def analyze_breaking_news(self, title: str, description: str = "") -> dict:
        if not self.is_available():
            return None
        try:
            return normalize_analysis(self._call(breaking_prompt(title, description)))
        except Exception as e:
            logger.warning(f"[GeminiAnalyzer] breaking_news failed: {e}")
            return None

    def analyze_actual_vs_forecast(self, event_name: str, actual: str, forecast: str, previous: str) -> dict:
        if not self.is_available():
            return None
        try:
            return normalize_analysis(self._call(actual_prompt(event_name, actual, forecast, previous)))
        except Exception as e:
            logger.warning(f"[GeminiAnalyzer] actual_vs_forecast failed: {e}")
            return None

    def summarize_daily_price(self, price_data: dict) -> str:
        """Returns a short Khmer market note, or None so the chain tries the next provider."""
        if not self.is_available():
            return None
        payload = {
            "contents": [{"role": "user", "parts": [{"text": summary_prompt(price_data)}]}],
            "systemInstruction": {"role": "system", "parts": [{"text": _SYSTEM_RULES}]},
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2000},
        }
        try:
            data = self._post(payload)
            res_text = _extract_text(data).strip()
            if res_text:
                import re
                res_text = re.sub(r"^is_clear\s*=\s*(true|false)\s*", "", res_text, flags=re.IGNORECASE).strip()
            return res_text or None
        except Exception as e:
            logger.warning(f"[GeminiAnalyzer] summarize_daily_price failed: {e}")
            return None