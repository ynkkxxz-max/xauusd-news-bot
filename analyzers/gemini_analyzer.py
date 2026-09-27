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
    "You are an Elite Institutional Financial Market Analyst and Lead Trader specializing in Technical Analysis, "
    "Fundamental Analysis, Price Action, Smart Money Concepts (SMC), and Risk Management for Gold (XAUUSD), Commodities, Forex, and Crypto.\n\n"
    "ADVANCED FILTERING & TRADING RULES (Strict Institutional Discipline):\n"
    "1. ECONOMIC NEWS FILTER (High-Impact Risk Protection):\n"
    "   - Before issuing or validating any signal, assess the Economic Calendar (CPI, NFP, FOMC, Core PCE, Fed Rates).\n"
    "   - If within 30 minutes before or after a major High-Impact economic release, you MUST refuse to issue a trade and state 'WAIT / NO TRADE (NEWS DANGER)' to protect capital from extreme spread expansion and slippage.\n\n"
    "2. ADVANCED TECHNICAL FRAMEWORKS (Smart Money Concepts / SMC & Price Action):\n"
    "   - Liquidity Sweeps: Identify where retail Stop Losses were swept at Asian/Session Highs or Lows before true reversal.\n"
    "   - Order Blocks (OB) & Fair Value Gaps (FVG): Pinpoint institutional buying/selling footprints and imbalance mitigation zones.\n"
    "   - Market Structure Shift (MSS) / Change of Character (ChoCH): Ensure market structure has formally shifted before signaling entries.\n\n"
    "3. MULTI-TIMEFRAME CONFLUENCE & CONFIDENCE SCORING (Minimum 80% Threshold):\n"
    "   - D1 / H4 (Macro Trend): Dictates the overarching bias (Bullish / Bearish / Range).\n"
    "   - H1 (Market Structure): Establishes major Support, Resistance, and Institutional Order Blocks.\n"
    "   - M15 / M5 (Execution Timeframe): Wait for candlestick confirmation, rejection wicks, or breakout/retest.\n"
    "   - Confidence Score (0-100%): Calculate a composite confidence score based on confluence across these timeframes.\n"
    "   - STRICT RULE: If the composite confidence score is below 80% (or if conditions are choppy/uncertain), you MUST output Action = 'WAIT / NO TRADE' and explain why.\n\n"
    "4. TRADING SESSIONS TIMING DISCIPLINE (Volume & Volatility Rules):\n"
    "   - Active Signal Windows: London Session (14:00 - 18:00 Cambodia Time) & New York Session / Overlap (19:00 - 23:30 Cambodia Time).\n"
    "   - NO TRADE Windows: Asian Session (06:00 - 13:30 Cambodia Time / Low Volume Sideways Trap) and Late NY Close (after 03:00 Cambodia Time). Refuse trades during low-volume sessions.\n\n"
    "5. FEW-SHOT EXAMPLES (Winning vs Losing Setups):\n"
    "   * VALID WINNING SETUP (Execution Allowed):\n"
    "     - Scenario: London Session Open (14:30 Cambodia Time). Asian Low swept ($2,680), followed by an M15 Market Structure Shift (MSS) breaking above $2,685 with a bullish FVG and H1 Trend Bullish.\n"
    "     - Decision: BUY NOW at $2,686, SL $2,679 (below swept low), TP1 $2,698, TP2 $2,708. Confidence Score: 90%.\n"
    "   * INVALID LOSING SETUP (Trade Blocked / WAIT):\n"
    "     - Scenario: Asian Session (09:00 Cambodia Time). Price consolidating tightly between $2,688 - $2,691, Moving Averages tangled, and US CPI news scheduled in 20 minutes.\n"
    "     - Decision: WAIT / NO TRADE (Reason: Asian low volume sideways chop + extreme news danger zone).\n\n"
    "6. SELF-CORRECTION & POST-TRADE REVIEW MECHANISM:\n"
    "   - Continuously evaluate previous signal outcomes via user vote feedback (Win/Loss).\n"
    "   - If a setup hits SL, determine the precise root cause: (a) Premature entry before candle closed, (b) Sudden news spike, or (c) Fakeout/Liquidity Hunt.\n"
    "   - Instantly adjust the subsequent signal threshold by demanding tighter confluence (+5% stricter).\n\n"
    "When delivering market analyses or trading setups, you must strictly adhere to the following 5 core pillars:\n"
    "1. MARKET OVERVIEW & TREND ANALYSIS (Timeframe, Primary Trend, Exact Key Support & Resistance Levels, Moving Averages & Indicator Alignment)\n"
    "2. TRADING SIGNAL / EXECUTION PLAN (Unambiguous Action: BUY, SELL, or WAIT; Exact Entry Price / Trigger, Stop Loss with structural rationale, TP1 (R:R >= 1:1.5), TP2 (R:R >= 1:2.0), R:R ratio, Confidence Score)\n"
    "3. CONFIRMATION REASONS (2 to 4 concrete, confluence-backed technical reasons: e.g. Key Level Rejection, Candlestick Pattern, MA crossover, Liquidity Grab)\n"
    "4. RISK MANAGEMENT & INVALIDATION SCENARIO (Clear invalidation level before entry, strictly advise risking maximum 1-2% account equity)\n"
    "5. FINAL VERDICT / SUMMARY (1-2 sentence concise executive summary)\n\n"
    "LANGUAGE & ACCURACY:\n"
    "- Never guess or generate random numbers; rely strictly on structural price action and technical confluence.\n"
    "- Write in fluent, professional, authoritative Khmer (retaining standard English financial terminology where clearer).\n"
    "- Always filter out noise: if data or news is insignificant or has no direct market impact, set is_clear = false."
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
        f"You are an Elite Institutional Financial Market Analyst & Senior Trader specializing in Technical Analysis, "
        f"Price Action, Smart Money Concepts (SMC), and Risk Management for Gold (XAUUSD).\n\n"
        f"CURRENT MARKET SNAPSHOT:\n"
        f"- Spot Price: ${current_price:,.2f}\n"
        f"- Structural Levels: Pivot=${key_levels.get('pivot', current_price):,.2f}, "
        f"R1=${key_levels.get('r1', current_price+20):,.2f}, R2=${key_levels.get('r2', current_price+40):,.2f}, "
        f"S1=${key_levels.get('s1', current_price-20):,.2f}, S2=${key_levels.get('s2', current_price-40):,.2f}\n"
        f"- Macro Sentiment: DXY={macro_data.get('dxy_price') if macro_data else 'N/A'}, "
        f"US10Y Yield={macro_data.get('us10y_yield') if macro_data else 'N/A'}%\n"
        f"- Order Flow Ratio: Buyers {order_book.get('bid_dominance_pct') if order_book else '50'}% vs Sellers {order_book.get('ask_dominance_pct') if order_book else '50'}%\n\n"
        f"OBJECTIVE & STRICT INSTRUCTIONS:\n"
        f"Provide a definitive institutional trading setup structured according to the 5 Core Pillars:\n"
        f"1. MARKET OVERVIEW & TREND ANALYSIS (Timeframe e.g. M15/H1, Primary Trend, Key Support and Resistance, Moving Averages / Indicator Confluence)\n"
        f"2. TRADING SIGNAL & EXECUTION PLAN (Action: BUY or SELL or WAIT; Entry zone, SL with technical logic, TP1 R:R>=1:1.5, TP2 R:R>=1:2.0, R:R ratio)\n"
        f"3. CONFIRMATION REASONS (2 to 4 concrete, bulleted technical and confluence reasons)\n"
        f"4. RISK MANAGEMENT & INVALIDATION SCENARIO (Exact invalidation trigger before entry, and strictly mandate 1-2% account equity risk)\n"
        f"5. FINAL VERDICT / SUMMARY (1-2 sentence executive summary)\n\n"
        f"RULES:\n"
        f"- If market is choppy, low confidence, or lack of confluence, Action MUST be 'WAIT' with detailed justification.\n"
        f"- No random numbers: calculate all prices strictly based on key structural levels.\n"
        f"- Write explanations in clear, high-authority Khmer combined with standard English trading terms.\n\n"
        f"Return JSON strictly adhering to schema:\n"
        f"- direction: 'BUY' or 'SELL' or 'WAIT'\n"
        f"- setup_title: e.g. '🟢 ផែនការទិញឡើង (INSTITUTIONAL BUY SETUP)'\n"
        f"- timeframe: 'M15 / H1'\n"
        f"- primary_trend: 'Bullish' / 'Bearish' / 'Sideways Consolidation'\n"
        f"- key_support: e.g. '${key_levels.get('s1', current_price-20):,.1f} - ${key_levels.get('s2', current_price-40):,.1f}'\n"
        f"- key_resistance: e.g. '${key_levels.get('r1', current_price+20):,.1f} - ${key_levels.get('r2', current_price+40):,.1f}'\n"
        f"- indicator_alignment: Technical / MA confluence summary\n"
        f"- entry: Exact entry price number float\n"
        f"- entry_zone: string range e.g. '$2,685.00 - $2,688.00'\n"
        f"- sl: Exact Stop Loss number float\n"
        f"- tp1: Take Profit 1 number float (R:R >= 1:1.5)\n"
        f"- tp2: Take Profit 2 number float (R:R >= 1:2.0)\n"
        f"- rr_ratio: string e.g. '1:2.2'\n"
        f"- confirmation_reasons: Array of 2 to 4 concrete reasons in Khmer\n"
        f"- invalidation_scenario: Exact market action that cancels setup\n"
        f"- risk_management_note: Rule on 1-2% risk discipline\n"
        f"- executive_summary: 1-2 sentence final verdict\n"
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
        """Enforces the quota cooldown without blocking user commands unnecessarily."""
        now = time.time()
        if now < GeminiAnalyzer._cooldown_until:
            remaining = int(GeminiAnalyzer._cooldown_until - now)
            raise RuntimeError(f"Gemini cooldown active ({remaining}s left) after quota limit")
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
                    timeout=4,
                )
                GeminiAnalyzer._last_request_ts = time.time()
                if resp.status_code == 429:
                    self._trip_cooldown()
                    raise RuntimeError(f"HTTP 429: {resp.text[:120]}")
                if resp.status_code in (500, 503):
                    self._trip_cooldown(120)
                    raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:120]}")
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as e:
                last_exc = e
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
                "timeframe": {"type": "string"},
                "primary_trend": {"type": "string"},
                "key_support": {"type": "string"},
                "key_resistance": {"type": "string"},
                "indicator_alignment": {"type": "string"},
                "entry": {"type": "number"},
                "entry_zone": {"type": "string"},
                "sl": {"type": "number"},
                "tp1": {"type": "number"},
                "tp2": {"type": "number"},
                "rr_ratio": {"type": "string"},
                "confirmation_reasons": {"type": "ARRAY", "items": {"type": "string"}},
                "invalidation_scenario": {"type": "string"},
                "risk_management_note": {"type": "string"},
                "executive_summary": {"type": "string"},
                "why_this_trade": {"type": "string"},
                "why_not_opposite": {"type": "string"},
                "confirmation_note": {"type": "string"}
            },
            "required": ["direction", "setup_title", "sl", "tp1", "tp2"]
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