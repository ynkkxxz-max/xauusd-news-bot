import json
import logging
import time
import requests
import base64

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
        f"ចូរវិភាគព័ត៌មាននេះឱ្យបានស៊ីជម្រៅ ខ្លីខ្លឹម មុតស្រួច និងត្រឹមត្រូវតាមប្រភេទព័ត៌មានពិតប្រាកដ "
        f"(ឧ. ប្រសិនបើជាព័ត៌មានសេដ្ឋកិច្ច ធនាគារកណ្តាល អតិផរណា កំណើនសេដ្ឋកិច្ច ឬ ADB ត្រូវវិភាគតាមបែបសេដ្ឋកិច្ចពិតប្រាកដ "
        f"ហាមយល់ច្រឡំថាជាសង្គ្រាម ឬភាពតានតឹងភូមិសាស្ត្រនយោបាយជាដាច់ខាត!)។\n\n"
        f"លក្ខខណ្ឌពិសេស៖ សរសេរប្រយោគឱ្យចប់ពេញលេញ ហាមវែងពេកនាំឱ្យដាច់កន្ទុយ (...) ត្រូវកំណត់ប្រវែងដូចខាងក្រោម៖\n"
        f"ត្រឡប់ JSON ដែលមាន fields ដូចតទៅ (ជាភាសាខ្មែរផ្លូវការ ពិរោះ ច្បាស់លាស់):\n"
        f"- what_happened: រៀបរាប់សាច់រឿងពិតជាក់ស្ដែងដែលទើបកើតឡើងឱ្យបានច្បាស់ ត្រឹមតែ ១-២ ប្រយោគពេញលេញ (កុំឱ្យលើសពី ១២០ តួអក្សរ)។\n"
        f"- why_it_matters: ពន្យល់ពីសារៈសំខាន់ និងយន្តការសេដ្ឋកិច្ចចំពោះទីផ្សារ ត្រឹមតែ ១-២ ប្រយោគពេញលេញ (កុំឱ្យលើសពី ១៤០ តួអក្សរ)។\n"
        f"- usd_impact: ផលប៉ះពាល់លើកម្លាំងប្រាក់ដុល្លារ DXY ត្រឹមតែ ១ ប្រយោគខ្លីខ្លឹមពេញលេញ (កុំឱ្យលើសពី ៧០ តួអក្សរ)។\n"
        f"- rate_yield_impact: សម្ពាធលើ US Treasury Yields និងអារម្មណ៍ទីផ្សារ ត្រឹមតែ ១ ប្រយោគខ្លីពេញលេញ (កុំឱ្យលើសពី ៧០ តួអក្សរ)។\n"
        f"- xau_pressure: 🟢 ឬ 🔴 ឬ 🟡 បូកនឹងការពន្យល់សម្ពាធលើមាស (XAUUSD) ត្រឹម ១ ប្រយោគខ្លីពេញលេញលើជួរតែមួយ (កុំឱ្យលើសពី ៨០ តួអក្សរ)។\n"
        f"- bias: 🟢 Bullish / 🔴 Bearish / 🟡 Mixed / Unclear\n"
        f"- is_clear: true (ប្រសិនបើព័ត៌មានមានទម្ងន់ច្បាស់លាស់ មានឥទ្ធិពលជាក់ស្តែងលើមាស) ឬ false (ប្រសិនបើព័ត៌មានស្រពេចស្រពិល មិនទាន់ច្បាស់លាស់ ឬគ្មានឥទ្ធិពលច្បាស់ក្រឡែត)\n"
        f"ហាមឆ្លើយតបជាគំរូដដែលៗ generic! ប្រសិនបើមិនច្បាស់លាស់ ត្រូវដាក់ is_clear = false ដើម្បីកុំផ្ញើចូល Channel Telegram។"
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
        f"ពន្យល់ពីទិសដៅទីផ្សារសកល និងសម្ពាធលើហាងឆេងក្នុងស្រុក។ កុំប្រើ JSON កុំប្រើ emoji ច្រើន។ ហាមសរសេរ is_clear = true/false ឬ meta-data ផ្សេងៗជាដាច់ខាត។ សរសេរតែអត្ថបទសង្ខេបសុទ្ធ។"
    )


def smc_setup_prompt(current_price: float, key_levels: dict, macro_data: dict = None, order_book: dict = None) -> str:
    return (
        f"អ្នកគឺជា Senior SMC Institutional Trader ជំនាញ XAU/USD (Gold)។\n"
        f"ទិន្នន័យទីផ្សារបច្ចុប្បន្ន៖\n"
        f"- តម្លៃបច្ចុប្បន្ន (Spot): ${current_price:,.2f}\n"
        f"- Key Levels: Pivot=${key_levels.get('pivot', current_price):,.2f}, "
        f"R1=${key_levels.get('r1', current_price+20):,.2f}, R2=${key_levels.get('r2', current_price+40):,.2f}, "
        f"S1=${key_levels.get('s1', current_price-20):,.2f}, S2=${key_levels.get('s2', current_price-40):,.2f}\n"
        f"- Macro: DXY={macro_data.get('dxy_price') if macro_data else 'N/A'} ({macro_data.get('dxy_pct') if macro_data else 'N/A'}%), "
        f"US10Y={macro_data.get('us10y_yield') if macro_data else 'N/A'}%\n"
        f"- Order Book: Bid={order_book.get('bid_dominance_pct') if order_book else '50'}%, Ask={order_book.get('ask_dominance_pct') if order_book else '50'}%\n\n"
        f"តម្រូវការពិសេស៖ ចូរជ្រើសរើសទិសដៅតែមួយគត់ (ទិសដៅតែមួយដាច់ណាត់ គឺ BUY តែមួយ ឬ SELL តែមួយ) "
        f"ដែលមានប្រូបាប៊ីលីតេឈ្នះខ្ពស់បំផុត (High Probability Win Rate)។ "
        f"ហាមប្រាប់ទាំងពីរទិស (ហាមដាក់ទាំង Buy ទាំង Sell)។\n\n"
        f"ត្រឡប់ JSON ដែលមានទម្រង់ដូចខាងក្រោមជាភាសាខ្មែរផ្លូវការ មុតស្រួច ជំនាញ Technical Analysis:\n"
        f"- direction: 'BUY' ឬ 'SELL'\n"
        f"- setup_title: e.g. '🟢 ផែនការទិញឡើង (BUY SETUP ONLY)' ឬ '🔴 ផែនការលក់ចុះ (SELL SETUP ONLY)'\n"
        f"- entry: តម្លៃ Entry (number float ឬ range e.g. 4330.00)\n"
        f"- entry_zone: string បញ្ជាក់តំបន់ចូលច្បាស់លាស់ (e.g. '$4,328.00 - $4,332.00')\n"
        f"- sl: តម្លៃ Stop Loss (number float e.g. 4322.00) (ចម្ងាយសមរម្យ $6 - $12)\n"
        f"- tp1: Take Profit 1 (number float, R:R ~ 1:1.5)\n"
        f"- tp2: Take Profit 2 (number float, R:R ~ 1:2.5 or key level)\n"
        f"- rr_ratio: string (e.g. '1:2.2')\n"
        f"- why_this_trade: ពន្យល់ហេតុផល ២-៣ ចំណុចថាហេតុអ្វីគួរ [BUY ឬ SELL] (Confluence: SMC Order Block, Support/Resistance, DXY, Liquidity)\n"
        f"- why_not_opposite: ពន្យល់ហេតុផលច្បាស់ៗ ២ ចំណុចថាហេតុអ្វីដាច់ខាតមិនគួរ [SELL ឬ BUY ផ្ទុយ] នៅត្រង់ចំណុចនេះ (បញ្ចៀស Trap/Fakeout)\n"
        f"- confirmation_note: អនុសាសន៍ខ្លីបញ្ជាក់ទៀន M15 ឬ Session\n"
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
        self.name = "gemini"
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

    def _post(self, payload: dict, max_retries: int = 1) -> dict:
        """POSTs to Gemini with fast-fail retry on transient errors (500/503)."""
        self._throttle_wait()
        last_exc = None
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    self.endpoint,
                    params={"key": self.api_key},
                    json=payload,
                    timeout=8,
                )
                GeminiAnalyzer._last_request_ts = time.time()
                if resp.status_code == 429:
                    self._trip_cooldown()
                    raise RuntimeError(f"HTTP 429: {resp.text[:120]}")
                if resp.status_code in (500, 503):
                    # Fast fail to let fallback analyzers pick it up immediately and pause Gemini for 120s
                    self._trip_cooldown(120)
                    raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:120]}")
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as e:
                last_exc = e
                # Trip a short cooldown on timeouts/connection failures so fallback handles calls
                self._trip_cooldown(60)
                break
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
                res_text = re.sub(r"(?im)^\s*is_clear\s*=\s*(true|false)\s*$", "", res_text)
                res_text = re.sub(r"(?i)\bis_clear\s*=\s*(true|false)\b", "", res_text).strip()
            return res_text or None
        except Exception as e:
            logger.warning(f"[GeminiAnalyzer] summarize_daily_price failed: {e}")
            return None

    def generate_smart_smc_setup(self, current_price: float, key_levels: dict, macro_data: dict = None, order_book: dict = None) -> dict:
        """
        Synthesizes Market Structure, Key Levels, Macro, and Order Flow to pick ONE high-probability
        trading direction (BUY or SELL ONLY) with precise Entry, SL, TP1, TP2, plus dual reasoning:
        - Why to take this trade
        - Why NOT to take the opposite trade
        """
        if not self.is_available():
            return None

        prompt = smc_setup_prompt(current_price, key_levels, macro_data, order_book)

        schema = {
            "type": "OBJECT",
            "properties": {
                "direction": {"type": "string"},
                "setup_title": {"type": "string"},
                "entry": {"type": "number"},
                "entry_zone": {"type": "string"},
                "sl": {"type": "number"},
                "tp1": {"type": "number"},
                "tp2": {"type": "number"},
                "rr_ratio": {"type": "string"},
                "why_this_trade": {"type": "string"},
                "why_not_opposite": {"type": "string"},
                "confirmation_note": {"type": "string"},
            },
            "required": ["direction", "setup_title", "sl", "tp1", "tp2", "why_this_trade", "why_not_opposite"]
        }

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "systemInstruction": {"role": "system", "parts": [{"text": _SYSTEM_RULES}]},
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
                "responseSchema": schema,
                "maxOutputTokens": 2500,
            },
        }

        try:
            data = self._post(payload)
            res = json.loads(_extract_text(data))
            return res
        except Exception as e:
            logger.warning(f"[GeminiAnalyzer] generate_smart_smc_setup failed: {e}")
            return None

    def analyze_chart_image(self, image_bytes: bytes, current_price: float, key_levels: dict = None) -> dict:
        """
        Multimodal Computer Vision Analysis of actual XAU/USD candlestick chart:
        Reads candlestick structures, Order Blocks, Liquidity Sweeps, and chart patterns directly from the image!
        """
        if not self.is_available() or not image_bytes:
            return None

        prompt = (
            f"អ្នកគឺជា Master Institutional Technical Analyst និង Chart Pattern Specialist ជំនាញ XAU/USD (Gold)។\n"
            f"ពិនិត្យរូបភាព Chart Candlestick ជាក់ស្តែងនេះយ៉ាងម៉ត់ចត់ (Spot Price: ${current_price:,.2f})។\n\n"
            f"ចូរធ្វើការវិភាគ Pattern នៃទៀន និងទម្រង់ Smart Money Concepts (SMC) ដោយត្រឡប់ JSON ដែលមាន Keys ដូចតទៅ៖\n"
            f"- detected_pattern: ឈ្មោះ Candlestick Pattern ឬ Chart Pattern ដែលលេចធ្លោបំផុត (e.g. 'Hammer Rejection', 'Bullish Engulfing', 'Fair Value Gap Fill', 'Double Bottom', 'Liquidity Sweep')\n"
            f"- pattern_kh: ឈ្មោះ Pattern ជាភាសាខ្មែរផ្លូវការ ពិរោះ ងាយយល់ (e.g. '🟢 ទៀនទាត់ចោលតម្លៃក្រោម (Bullish Pinbar Rejection)')\n"
            f"- market_structure: រចនាសម្ព័ន្ធទីផ្សារ ('BULLISH_BOS', 'BEARISH_BOS', 'RANGE_CONSOLIDATION', 'CHoCH_REVERSAL')\n"
            f"- key_observation: ការសង្កេតគន្លឹះសំខាន់ ២ ប្រយោគ ពីទម្រង់ទៀនចុងក្រោយ និងតំបន់ Liquidity\n"
            f"- tactical_action: អនុសាសន៍សម្រាប់ Trader ('ទិញឡើងតាមកម្លាំង Rejection', 'រង់ចាំទម្លុះ BSL', 'លក់ចុះតាម Bearish Pressure')\n"
            f"- confidence_score: ភាគរយទំនុកចិត្ត (e.g. '88%')\n"
            f"- bias: '🟢 Bullish' ឬ '🔴 Bearish' ឬ '🟡 Neutral'\n"
        )

        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        schema = {
            "type": "OBJECT",
            "properties": {
                "detected_pattern": {"type": "string"},
                "pattern_kh": {"type": "string"},
                "market_structure": {"type": "string"},
                "key_observation": {"type": "string"},
                "tactical_action": {"type": "string"},
                "confidence_score": {"type": "string"},
                "bias": {"type": "string"}
            },
            "required": ["detected_pattern", "pattern_kh", "market_structure", "key_observation", "tactical_action", "confidence_score", "bias"]
        }

        payload = {
            "contents": [{
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": b64_image
                        }
                    }
                ]
            }],
            "systemInstruction": {"role": "system", "parts": [{"text": _SYSTEM_RULES}]},
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
                "responseSchema": schema,
                "maxOutputTokens": 2000
            }
        }

        try:
            data = self._post(payload)
            return json.loads(_extract_text(data))
        except Exception as e:
            logger.warning(f"[GeminiAnalyzer] analyze_chart_image failed: {e}")
            return None