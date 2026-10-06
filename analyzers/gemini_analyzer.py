import json
import logging
import time
import requests
import base64
import re

from config import (
    GEMINI_API_KEY, GEMINI_MODEL, USE_GEMINI,
    GEMINI_MIN_INTERVAL, GEMINI_COOLDOWN,
)

logger = logging.getLogger(__name__)

# Keys must match what KhmerFormatter expects from an analysis dict.
_ANALYSIS_KEYS = [
    "headline_km", "key_event", "what_happened", "why_it_matters", "impact", "usd_impact",
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
    "- Write in fluent, professional, authoritative Khmer. Strictly keep company names (e.g. Apple, Tesla, NVIDIA, Tether, BlackRock) and people's names (e.g. Donald Trump, Jerome Powell, Elon Musk, Kevin Warsh, Vladimir Putin) in their original English/Latin spelling — DO NOT translate or transliterate them into Khmer.\n"
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
        f"You are an expert financial news editor and Telegram content creator. Your task is to process global macroeconomic and financial news into professional, clean Khmer posts for a Telegram channel.\n\n"
        f"ព័ត៌មានជាក់ស្តែង៖\n"
        f"ចំណងជើង: {title}\nខ្លឹមសារ: {description}\n\n"
        f"STRICT FORMATTING & CONTENT RULES:\n\n"
        f"1. NO ELLIPSIS & NO REDUNDANCY:\n"
        f"   - NEVER truncate sentences or titles with '...'. Always complete the sentence.\n"
        f"   - The headline and the summary text MUST NOT repeat each other. The headline is the core hook; the body provides additional context and depth.\n\n"
        f"2. SENTIMENT & SYMBOLS (STRICTLY ONE DOMINANT DIRECTION):\n"
        f"   - Choose EXACTLY ONE impact direction per news item: EITHER 🔹 for positive/bullish impact OR 🔸 for negative/bearish impact or risk factors.\n"
        f"   - NEVER include both 🔹 and 🔸 together in the same post! Strictly output only 1 single line for impact.\n"
        f"   - Do not use generic templates for market impact. Tailor the analysis directly to the asset mentioned (e.g., Gold/XAUUSD, USD, Tech stocks, Oil, or Inflation).\n"
        f"   - GEOPOLITICS, WAR, CONFLICT, MILITARY, AND STRAIT DISRUPTIONS: STRICTLY NEGATIVE/MARKET RISK (🔸 ហានិភ័យទីផ្សារ or 🔸 ផលអវិជ្ជមាន/ហានិភ័យ). NEVER mark war, military advances, or strait blockades as positive (🔹 ផលវិជ្ជមាន) even if gold goes up. Gold rising from war is a MARKET RISK, not a positive event!\n\n"
        f"3. NATURAL KHMER TRANSLATION:\n"
        f"   - Translate by context and meaning, not word-by-word (e.g., 'names' -> 'តែងតាំង', 'Big Tech' -> 'ក្រុមហ៊ុនបច្ចេកវិទ្យាយក្ស', 'rate hike' -> 'ការដំឡើងអត្រាការប្រាក់')。\n"
        f"   - Keep foreign company and leader names in original English/Latin spelling (Apple, Microsoft, NVIDIA, Tesla, TSMC, Jerome Powell, Elon Musk, Donald Trump...)。\n"
        f"   - Always leave a clean space between Latin/English words and Khmer words (e.g. 'កងទ័ព Yemen', 'ច្រកសមុទ្រ Bab al-Mandab', 'ក្រុម Houthi', 'តំបន់ Dhubab')។\n"
        f"   - Leave a clean blank line between the Headline, Summary, Impact, and Source.\n\n"
        f"4. POST FORMAT MODES (GENERATE CONTENT COMPATIBLE WITH BOTH):\n"
        f"   - MODE A: PHOTO CAPTION (When an image is attached): Total Word Count strictly between 60 to 90 Khmer words (Under 850 total characters).\n"
        f"   - MODE B: TEXT-ONLY POST (When no image is attached): Total Word Count strictly between 120 to 180 Khmer words across 2 detailed context paragraphs:\n"
        f"     • Paragraph 1: Core event and key developments\n"
        f"     • Paragraph 2: Broader economic background or central bank reaction\n\n"
        f"ត្រឡប់ JSON ដែលមាន fields ដូចតទៅ:\n"
        f"- headline_km: ចំណងជើងព័ត៌មានខ្លីទាន់ហេតុការណ៍ជាភាសាខ្មែរ (ប្រយោគពេញលេញ មានន័យស្តាប់បានត្រឹមត្រូវ ១០០% ហាមដាច់ខាតកុំប្រើ ... ឬ : នៅខាងចុង)\n"
        f"- key_event: ខ្លឹមសាររៀបរាប់ដំណើររឿងស៊ីជម្រៅ (កថាខណ្ឌទី ១៖ ព្រឹត្តិការណ៍ស្នូល និងការវិវត្តចម្បង, កថាខណ្ឌទី ២៖ បរិបទសេដ្ឋកិច្ច ឬប្រតិកម្មធនាគារកណ្តាល) បំបែកដោយបន្ទាត់ទទេ \\n\\n (មិនចម្លងពាក្យដដែលៗពី headline_km)\n"
        f"- what_happened: សេចក្តីសង្ខេបព្រឹត្តិការណ៍ជាភាសាខ្មែរ (១-២ ប្រយោគ)។\n"
        f"- why_it_matters: សារៈសំខាន់ចំពោះសង្គម ឬពិភពលោកជាភាសាខ្មែរ (១-២ ប្រយោគ)។\n"
        f"- impact: បញ្ជាក់ផលប៉ះពាល់ចំទ្រព្យសកម្មយ៉ាងខ្លីច្បាស់លាស់ ត្រឹមតែ ១ បន្ទាត់គត់ ដោយជ្រើសរើសទម្រង់មួយក្នុងចំណោមពីរ (ហាមដាច់ខាតកុំដាក់ទាំងពីរជាន់គ្នា):\n"
        f"  • បើព័ត៌មានវិជ្ជមាន៖ 🔹 ផលវិជ្ជមាន៖ [ការពន្យល់ផលវិជ្ជមានចំទ្រព្យសកម្ម]\n"
        f"  • បើព័ត៌មានអវិជ្ជមាន/ហានិភ័យ៖ 🔸 ហានិភ័យទីផ្សារ៖ [ការពន្យល់ហានិភ័យចំទ្រព្យសកម្ម]\n"
        f"  (ជ្រើសរើសយកតែមួយគត់! ហាមដាច់ខាតកុំដាក់ទាំង 🔹 និង 🔸 ក្នុងសារតែមួយ, ហាមប្រើពាក្យ 'វា' នៅខាងមុខ, និងហាមប្រើវង់ក្រចក ())។\n"
        f"- usd_impact: ផលប៉ះពាល់លើ USD (១ ប្រយោគ ឬដាក់ 'គ្មានផលប៉ះពាល់ផ្ទាល់' បើមិនពាក់ព័ន្ធ)。\n"
        f"- rate_yield_impact: សម្ពាធលើ Bond Yields (១ ប្រយោគ ឬដាក់ 'គ្មានផលប៉ះពាល់ផ្ទាល់' បើមិនពាក់ព័ន្ធ)。\n"
        f"- xau_pressure: 🟢 Bullish ឬ 🔴 Bearish ឬ 🟡 Neutral / គ្មានផលប៉ះពាល់ (១ ប្រយោគ)。\n"
        f"- bias: 🟢 Bullish / 🔴 Bearish / 🟡 Neutral\n"
        f"- is_clear: true (ប្រសិនបើជាព័ត៌មានពិតទាន់ហេតុការណ៍ថ្មីធំ) ឬ false (ប្រសិនបើជារឿងឯកជន ជីវិតផ្ទាល់ខ្លួន ឬកីឡា/កម្សាន្ត)\n"
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
    chg = price_data.get('change', 0)
    chg_pct = price_data.get('change_pct', 0)
    direction = "ធ្លាក់ចុះ (Bearish Drop)" if chg < 0 else "កើនឡើង (Bullish Rise)"
    macro = price_data.get("macro_correlation", {})
    dxy = macro.get("dxy_price", "N/A")
    us10y = macro.get("us10y_yield", "N/A")
    return (
        f"អ្នកគឺជាអ្នកជំនាញវិភាគទីផ្សារហិរញ្ញវត្ថុ និងមាសសកលកម្រិតស្ថាប័ន (Senior Gold Market Analyst)។\n"
        f"ថ្ងៃនេះតម្លៃមាស XAUUSD គឺ ${price_data.get('price_oz', 0):,.2f}/oz មានបម្រែបម្រួល {chg:+,.2f} ({chg_pct:+.2f}%) គឺស្ថិតក្នុងស្ថានភាព {direction}។\n"
        f"ទិន្នន័យម៉ាក្រូ៖ DXY Index = {dxy}, US 10Y Yield = {us10y}%。\n\n"
        f"ចូរសរសេរពន្យល់ពី «មូលហេតុចម្បងដែលធ្វើឱ្យតម្លៃមាស{direction}» ឱ្យមានស្តង់ដាវិជ្ជាជីវៈខ្ពស់ ជាភាសាខ្មែរផ្លូវការ ខ្លី ខ្លឹម ច្បាស់លាស់ (២ ទៅ ៣ ចំណុច bullet points):\n"
        f"• <b>កត្តាម៉ាក្រូសេដ្ឋកិច្ច (Macro Drivers):</b> ឥទ្ធិពលសន្ទស្សន៍ DXY, ទិន្នផលប័ណ្ណបំណុល US 10Y, ឬការរំពឹងទុកអត្រាការប្រាក់ Fed\n"
        f"• <b>ចរន្តសាច់ប្រាក់ស្ថាប័ន (Institutional Flow):</b> ការទាញយកប្រាក់ចំណេញ (Profit Taking) ឬតម្រូវការ Safe-Haven ទិញទ្រព្យសុវត្ថិភាព\n"
        f"• <b>ទស្សនវិស័យទីផ្សារ (Market Outlook):</b> ការវិវត្តបន្តនៃទិសដៅមាស\n\n"
        f"ហាមប្រើ JSON, ហាមសរសេរ meta-data ឬ is_clear។ សរសេរតែខ្លឹមសារ bullet points ជាភាសាខ្មែរផ្លូវការតែប៉ុណ្ណោះ។"
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
        f"- Stop Loss (SL) distance from Entry MUST strictly be 8 to 10 points (maximum 12 points, NEVER exceed 12 points / $12).\n"
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


def signal_validation_prompt(raw_signal: dict, current_price: float, key_levels: dict, macro_data: dict = None, order_book: dict = None) -> str:
    action = raw_signal.get("action", "BUY")
    pattern = raw_signal.get("pattern") or raw_signal.get("action_title") or "Technical Confirmation"
    entry = raw_signal.get("entry", current_price)
    sl = raw_signal.get("sl", current_price - 10 if action == "BUY" else current_price + 10)
    tp1 = raw_signal.get("tp1") or raw_signal.get("tp", current_price + 20 if action == "BUY" else current_price - 20)
    tp2 = raw_signal.get("tp2", current_price + 35 if action == "BUY" else current_price - 35)

    dxy = macro_data.get("dxy_price", "N/A") if macro_data else "N/A"
    us10y = macro_data.get("us10y_yield", "N/A") if macro_data else "N/A"
    bid_pct = order_book.get("bid_dominance_pct", 50) if order_book else 50
    ask_pct = order_book.get("ask_dominance_pct", 50) if order_book else 50

    return (
        f"You are the Lead Institutional Risk Manager and Senior Head Trader specializing in Gold (XAUUSD).\n"
        f"Our algorithmic scanner detected a candidate sniper trade setup. You must perform an IN-DEPTH AUDIT for MAXIMUM ACCURACY.\n"
        f"Our strict fund policy: Maximum 5 position signals per day. Every signal MUST be Grade A+ with high conviction.\n\n"
        f"CANDIDATE SETUP:\n"
        f"- Action: {action}\n"
        f"- Spot Price: ${current_price:,.2f}\n"
        f"- Proposed Entry: ${entry:,.2f}\n"
        f"- Proposed Stop Loss: ${sl:,.2f}\n"
        f"- Proposed TP1: ${tp1:,.2f} | TP2: ${tp2:,.2f}\n"
        f"- Pattern / Technical Trigger: {pattern} ({raw_signal.get('reason', '')})\n"
        f"- Structural Levels: Pivot=${key_levels.get('pivot', current_price):,.2f}, S1=${key_levels.get('s1', current_price-20):,.2f}, R1=${key_levels.get('r1', current_price+20):,.2f}\n"
        f"- Macro Environment: DXY={dxy}, US10Y Yield={us10y}%\n"
        f"- Order Book Depth: Bids {bid_pct}% vs Asks {ask_pct}%\n\n"
        f"AUDITING & VALIDATION MANDATES:\n"
        f"1. QUALITY & ACCURACY FIRST: If price action is in a low-volume sideways chop, choppy noise, or high fakeout risk, REJECT (approved = false).\n"
        f"2. CONFIDENCE THRESHOLD: Confidence score must be at least 85% to approve. If below 85%, REJECT (approved = false).\n"
        f"3. RISK REWARD: Stop Loss distance from Entry MUST strictly be 8 to 10 points (maximum 12 points, NEVER exceed 12 points / $12). TP1 must have minimum 1:2.0 R:R, TP2 1:3.0+ R:R.\n"
        f"4. IF APPROVED: Provide rigorous, institutional analysis in professional, high-authority Khmer.\n\n"
        f"Return JSON strictly adhering to schema:\n"
        f"- approved: boolean (true only if high-accuracy Grade A+ setup, false otherwise)\n"
        f"- rejection_reason: string in Khmer explaining why setup was rejected (if approved is false)\n"
        f"- action: 'BUY' or 'SELL'\n"
        f"- entry: refined entry price number float\n"
        f"- sl: refined structural Stop Loss price number float\n"
        f"- tp1: Take Profit 1 price number float (min 1:2 R:R)\n"
        f"- tp2: Take Profit 2 price number float (min 1:3 R:R)\n"
        f"- rr_ratio: string (e.g. '1:2.2')\n"
        f"- confidence_score: string (e.g. '88%' or '92%')\n"
        f"- ai_analysis: 2-3 sentences in professional Khmer explaining the institutional order flow mechanism and why this trade has high probability\n"
        f"- macro_context: 1 sentence in Khmer on DXY & US Yields correlation\n"
        f"- invalidation_note: 1 sentence in Khmer defining the exact condition that invalidates the trade\n"
        f"- execution_tips: 1-2 practical execution guidelines in Khmer for traders\n"
    )


def normalize_analysis(raw: dict) -> dict:
    try:
        from formatters.khmer_formatter import sanitize_khmer_spelling
    except Exception:
        from khmer_formatter import sanitize_khmer_spelling

    out = {}
    for k in _ANALYSIS_KEYS:
        if k == "is_clear":
            raw_val = raw.get("is_clear")
            if isinstance(raw_val, bool):
                out["is_clear"] = raw_val
            elif isinstance(raw_val, str):
                out["is_clear"] = raw_val.strip().lower() not in ("false", "0", "no")
            else:
                out["is_clear"] = True
            continue
        val = str(raw.get(k, "")).strip()
        val = sanitize_khmer_spelling(val)
        out[k] = val if val else "កំពុងតាមដាន។"
    # Ensure headline_km is never a generic placeholder
    hl = str(out.get("headline_km", "")).strip()
    if not hl or hl == "កំពុងតាមដាន។":
        candidate = str(raw.get("what_happened", "")).strip() or str(raw.get("key_event", "")).strip()
        if candidate and candidate != "កំពុងតាមដាន។":
            first_sent = candidate.split("។")[0].strip()
            out["headline_km"] = sanitize_khmer_spelling(first_sent)
        else:
            out["headline_km"] = ""
    # Ensure no trailing ellipsis, dots, colons, hyphens
    if out.get("headline_km"):
        hl_clean = out["headline_km"]
        hl_clean = re.sub(r'[\s.,;:៖–—_…]+$', '', hl_clean).strip()
        hl_clean = re.sub(r'\.{2,}', '', hl_clean).strip()
        hl_clean = re.sub(r'…+', '', hl_clean).strip()
        out["headline_km"] = re.sub(r'[\s.,;:៖–—_…]+$', '', hl_clean).strip()
    if not raw.get("key_event") or out["key_event"] == "កំពុងតាមដាន។":
        what = str(raw.get("what_happened", "")).strip()
        why = str(raw.get("why_it_matters", "")).strip()
        parts = [p for p in [what, why] if p]
        out["key_event"] = sanitize_khmer_spelling("\n\n".join(parts)) if parts else out.get("what_happened", "កំពុងតាមដាន។")
    # Combat / Attack / War / Drone / Military / Strait Sentiment Safety Net: Strictly Negative / Market Risk
    combat_words = [
        "ដ្រូន", "drone", "វាយប្រហារ", "attack", "សង្គ្រាម", "war", "គ្រាប់បែក", "bomb",
        "ឧទ្ទាម", "rebel", "insurgent", "ប្រដាប់អាវុធ", "armed", "មីស៊ីល", "missile",
        "ជម្លោះ", "conflict", "កងទ័ព", "យោធា", "ទ័ព", "កងកម្លាំង", "military", "army",
        "navy", "troops", "soldiers", "clash", "airstrike", "yemen", "houthi", "mandab",
        "bab al-mandab", "red sea", "strait", "straits", "hormuz", "ច្រកសមុទ្រ", "សមុទ្រក្រហម",
        "យេម៉ែន", "ហូទី"
    ]
    narrative_full = (out.get("key_event", "") + " " + out.get("what_happened", "") + " " + str(raw.get("title", "")) + " " + out.get("headline_km", "")).lower()
    is_combat = any(w in narrative_full for w in combat_words)

    # Guarantee impact line is valid Khmer per user directive
    imp = out.get("impact", "")
    if is_combat:
        is_strait = any(w in narrative_full for w in ["mandab", "bab al-mandab", "red sea", "strait", "straits", "hormuz", "ច្រកសមុទ្រ", "សមុទ្រក្រហម"])
        if is_strait:
            out["impact"] = "🔸 ហានិភ័យទីផ្សារ៖ ភាពតានតឹងនៅច្រកសមុទ្រក្រហមអាចគំរាមកំហែងដល់ផ្លូវដឹកជញ្ជូនថាមពលសកល ដែលអាចរុញច្រានតម្លៃប្រេងឆៅ និងមាសឱ្យកើនឡើង"
        else:
            out["impact"] = "🔸 ហានិភ័យទីផ្សារ៖ បង្កើនភាពតានតឹងផ្នែកភូមិសាស្ត្រនយោបាយ ដែលអាចជំរុញឱ្យតម្រូវការទិញមាស (XAUUSD) ហក់ឡើងខ្ពស់ក្នុងនាមជាទ្រព្យសុវត្ថិភាព"
        out["bias"] = "🔴 Bearish"
    elif not imp or imp == "កំពុងតាមដាន។" or ("វិជ្ជមាន" not in imp and "អវិជ្ជមាន" not in imp and "ហានិភ័យ" not in imp):
        b = str(raw.get("bias", "")).lower()
        if "វិជ្ជមាន" in b or ("bullish" in b and "xau" not in b):
            out["impact"] = "🔹 ផលវិជ្ជមាន៖ ជំរុញសន្ទុះកំណើនទីផ្សារ"
        else:
            out["impact"] = "🔸 ផលអវិជ្ជមាន៖ បង្កើនសម្ពាធលើទីផ្សារ"
    else:
        imp = re.sub(r'[\r\n]+', ' ', imp).strip()
        imp = re.sub(r'^(ផលវិជ្ជមាន|ផលអវិជ្ជមាន|ផលអព្យាក្រឹត)[\s៖:]+', r'\1៖ ', imp)
        out["impact"] = imp

    out["impact"] = sanitize_khmer_spelling(out["impact"])
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
        try:
            from config import GEMINI_KEYS_POOL
            self.api_keys = [k for k in [api_key] if k] if api_key else list(GEMINI_KEYS_POOL)
        except Exception:
            self.api_keys = [api_key] if api_key else [GEMINI_API_KEY]
        if not self.api_keys and GEMINI_API_KEY:
            self.api_keys = [GEMINI_API_KEY]
        self.api_key = self.api_keys[0] if self.api_keys else ""
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
        return bool(USE_GEMINI and (self.api_key or self.api_keys) and self.api_key != "YOUR_GEMINI_API_KEY_HERE")

    def _post(self, payload: dict, max_retries: int = 1) -> dict:
        """POSTs to Gemini with dual-key pool and multi-model fallback on quota/transient errors."""
        self._throttle_wait()
        candidate_models = [self.model, "gemini-flash-lite-latest", "gemini-2.5-flash-lite", "gemini-flash-latest", "gemini-pro-latest"]
        seen = set()
        models_to_try = [m for m in candidate_models if m and not (m in seen or seen.add(m))]

        keys_to_try = self.api_keys if self.api_keys else [self.api_key]
        last_exc = None

        for current_key in keys_to_try:
            for current_model in models_to_try:
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent"
                for attempt in range(max_retries):
                    try:
                        resp = requests.post(
                            endpoint,
                            params={"key": current_key},
                            json=payload,
                            timeout=25,
                        )
                        GeminiAnalyzer._last_request_ts = time.time()
                        if resp.status_code == 429:
                            logger.warning(f"[GeminiAnalyzer] Key ...{current_key[-6:]} hit 429 quota on {current_model}, trying next key/model...")
                            break
                        if resp.status_code in (500, 503):
                            logger.warning(f"[GeminiAnalyzer] Model {current_model} returned {resp.status_code} (attempt {attempt+1}/{max_retries}), retrying...")
                            time.sleep(1.5)
                            continue
                        if resp.status_code == 404:
                            break
                        resp.raise_for_status()
                        return resp.json()
                    except requests.RequestException as e:
                        last_exc = e
                        logger.debug(f"[GeminiAnalyzer] Request error on {current_model}: {e}")
                        time.sleep(1)
        if last_exc:
            self._trip_cooldown(60)
            raise last_exc
        raise RuntimeError("All Gemini candidate models/keys failed or exhausted quota.")

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

    def analyze_and_validate_sniper_signal(
        self,
        raw_signal: dict,
        current_price: float,
        key_levels: dict,
        macro_data: dict = None,
        order_book: dict = None
    ) -> dict:
        """
        AI Chief Risk Officer & Senior Trader Audit:
        Rigorous multi-layer AI evaluation for maximum signal accuracy.
        Blocks noisy/choppy/risky setups (approved=False), or approves Grade A+ setups (approved=True).
        """
        if not self.is_available():
            return None

        prompt = signal_validation_prompt(raw_signal, current_price, key_levels, macro_data, order_book)
        schema = {
            "type": "OBJECT",
            "properties": {
                "approved": {"type": "boolean"},
                "rejection_reason": {"type": "string"},
                "action": {"type": "string"},
                "entry": {"type": "number"},
                "sl": {"type": "number"},
                "tp1": {"type": "number"},
                "tp2": {"type": "number"},
                "rr_ratio": {"type": "string"},
                "confidence_score": {"type": "string"},
                "ai_analysis": {"type": "string"},
                "macro_context": {"type": "string"},
                "invalidation_note": {"type": "string"},
                "execution_tips": {"type": "string"}
            },
            "required": ["approved", "action", "entry", "sl", "tp1", "tp2", "confidence_score"]
        }

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "systemInstruction": {"role": "system", "parts": [{"text": _SYSTEM_RULES}]},
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
                "responseSchema": schema,
                "maxOutputTokens": 2000,
            },
        }

        try:
            data = self._post(payload)
            res = json.loads(_extract_text(data))
            return res
        except Exception as e:
            logger.warning(f"[GeminiAnalyzer] analyze_and_validate_sniper_signal failed: {e}")
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

    def answer_user_query(self, query: str, market_context: dict = None) -> str:
        """
        Interactive AI Gold & Macro Analyst.
        Answers user questions in authoritative, polite, and fluent Khmer with live market telemetry.
        Returns clean HTML formatted string for Telegram.
        """
        if not self.is_available():
            return "⚠️ ប្រព័ន្ធ AI មិនទាន់ត្រូវបានបើកដំណើរការ ឬកំពុងថែទាំ។ សូមសាកល្បងម្តងទៀតនៅពេលក្រោយ។"

        ctx_str = ""
        if market_context:
            oz = market_context.get("price_oz", 0.0)
            chg = market_context.get("change_pct", 0.0)
            piv = market_context.get("pivot", 0.0)
            r1 = market_context.get("r1", 0.0)
            s1 = market_context.get("s1", 0.0)
            dxy = market_context.get("dxy", "N/A")
            us10y = market_context.get("us10y", "N/A")
            news = market_context.get("next_news", "គ្មានព័ត៌មានក្រហមបន្ទាន់")
            ctx_str = (
                f"\n\n📊 [LIVE MARKET CONTEXT]:\n"
                f"• Spot XAU/USD: ${oz:,.2f} ({chg:+.2f}%)\n"
                f"• Key Pivot: ${piv:,.2f} | R1: ${r1:,.2f} | S1: ${s1:,.2f}\n"
                f"• US Dollar Index (DXY): {dxy}\n"
                f"• US 10Y Yield: {us10y}%\n"
                f"• Upcoming News: {news}\n"
            )

        prompt = (
            f"អ្នកគឺជា Master Institutional Gold (XAUUSD) & Macroeconomic AI Analyst សម្រាប់ Cambodian Traders។\n"
            f"Trader បានសួរសំណួរ៖\n"
            f"❓ \"{query}\"\n"
            f"{ctx_str}\n"
            f"ចូរឆ្លើយតបសំណួរនេះជាភាសាខ្មែរផ្លូវការ ពិរោះ មុតស្រួច និងប្រកបដោយវិជ្ជាជីវៈកម្រិតស្ថាប័នធំៗ (Institutional Level)៖\n"
            f"1. ឆ្លើយចំៗទៅកាន់សំណួរ (Direct Actionable Verdict) ថាតើទីផ្សារស្ថិតក្នុងស្ថានភាពណា គួរទិញ លក់ ឬរង់ចាំ។\n"
            f"2. ការវិភាគបច្ចេកទេស និងម៉ាក្រូសេដ្ឋកិច្ច (Technical & Macro Confluence) ដោយភ្ជាប់ជាមួយទិន្នន័យជាក់ស្តែងនៃ XAUUSD, DXY និងតំបន់គន្លឹះ។\n"
            f"3. យុទ្ធសាស្ត្រប្រតិបត្តិការ និងការគ្រប់គ្រងហានិភ័យ (Trading Strategy & Risk Note)៖ កម្រិត Entry / SL / TP បើពាក់ព័ន្ធ និងក្រើនរំលឹកកុំ Overtrade។\n\n"
            f"ទម្រង់ឆ្លើយតប៖ ប្រើប្រាស់ HTML tags សមស្របសម្រាប់ Telegram (<b>, <code>, •, emojis) កុំប្រើ Markdown asterisks (**)។ រៀបចំឱ្យមានរបៀប ងាយស្រួលអានលើទូរស័ព្ទដៃ (Mobile Friendly)។"
        )

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "systemInstruction": {"role": "system", "parts": [{"text": _SYSTEM_RULES}]},
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 2048
            }
        }

        try:
            data = self._post(payload)
            ans = _extract_text(data).strip()
            return ans if ans else "⚠️ មិនអាចទទួលបានចម្លើយពី AI នៅពេលនេះទេ។"
        except Exception as e:
            logger.warning(f"[GeminiAnalyzer] answer_user_query failed: {e}")
            return "⚠️ AI កំពុងមមាញឹក ឬជាប់កូតា (Quota Limit)។ សូមរង់ចាំប្រហែល ១-២ នាទី រួចសាកល្បងម្តងទៀត។"

    def analyze_user_chart_image(self, image_bytes: bytes, caption: str = "", current_price: float = 0.0, key_levels: dict = None, mime_type: str = "image/jpeg") -> dict:
        """
        Multimodal Computer Vision Analysis of user-uploaded TradingView/MT4/MT5 charts.
        Extracts patterns, structure, entry, SL, TP, and comprehensive Khmer guidance.
        """
        if not self.is_available() or not image_bytes:
            return None

        prompt = (
            f"អ្នកគឺជា Master Institutional Technical Analyst និង Chart Pattern Specialist ជំនាញ XAU/USD (Gold)។\n"
            f"Trader បានផ្ញើរូបភាព Chart Candlestick (TradingView / MT4 / MT5) មកឱ្យអ្នកពិនិត្យ។\n"
            f"ចំណងជើង/សំណួរភ្ជាប់មកជាមួយ៖ \"{caption if caption else 'សូមវិភាគ Chart នេះ'}\"\n"
            f"តម្លៃបច្ចុប្បន្នលើទីផ្សារ Spot (បើមាន): ${current_price:,.2f}\n\n"
            f"ចូរពិនិត្យរចនាសម្ព័ន្ធ Chart រូបភាពនេះយ៉ាងល្អិតល្អន់ និងបង្កើតផែនការជួញដូរច្បាស់លាស់។\n"
            f"ត្រឡប់ JSON ដែលមាន Schema ដូចខាងក្រោម៖\n"
            f"- direction: 'BUY' ឬ 'SELL' ឬ 'WAIT'\n"
            f"- setup_title: ចំណងជើងភាសាខ្មែរ (e.g. '🟢 ផែនការទិញឡើងតាម SMC FVG' ឬ '🔴 ផែនការលក់ចុះតាម Liquidity Sweep')\n"
            f"- timeframe: Timeframe ដែលបានឃើញក្នុង Chart (e.g. 'M15', 'H1', 'H4', 'D1')\n"
            f"- pattern_detected: ឈ្មោះ Pattern ជាភាសាអង់គ្លេស\n"
            f"- pattern_kh: ឈ្មោះ Pattern ជាភាសាខ្មែរផ្លូវការ ពិរោះ\n"
            f"- entry_zone: តំបន់តម្លៃចូលផ្សារ (e.g. '$2,682 - $2,685')\n"
            f"- stop_loss: តម្លៃ Stop Loss (e.g. '$2,677')\n"
            f"- take_profit_1: តម្លៃ TP1 (R:R >= 1:1.5)\n"
            f"- take_profit_2: តម្លៃ TP2 (R:R >= 1:2.0)\n"
            f"- rr_ratio: អនុបាត R:R (e.g. '1:2.2')\n"
            f"- confidence_score: ភាគរយទំនុកចិត្ត (e.g. '88%')\n"
            f"- confluence_reasons: Array នៃហេតុផលបញ្ជាក់ 3-4 ចំណុចជាភាសាខ្មែរ\n"
            f"- invalidation_rule: លក្ខខណ្ឌតម្លៃដែលលុបចោល Setup នេះ\n"
            f"- risk_warning: ការក្រើនរំលឹកហានិភ័យជាភាសាខ្មែរ\n"
            f"- detailed_summary_kh: ការសង្ខេបវិភាគ ១-២ កថាខណ្ឌជាភាសាខ្មែរ"
        )

        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        schema = {
            "type": "OBJECT",
            "properties": {
                "direction": {"type": "string"},
                "setup_title": {"type": "string"},
                "timeframe": {"type": "string"},
                "pattern_detected": {"type": "string"},
                "pattern_kh": {"type": "string"},
                "entry_zone": {"type": "string"},
                "stop_loss": {"type": "string"},
                "take_profit_1": {"type": "string"},
                "take_profit_2": {"type": "string"},
                "rr_ratio": {"type": "string"},
                "confidence_score": {"type": "string"},
                "confluence_reasons": {"type": "ARRAY", "items": {"type": "string"}},
                "invalidation_rule": {"type": "string"},
                "risk_warning": {"type": "string"},
                "detailed_summary_kh": {"type": "string"}
            },
            "required": ["direction", "setup_title", "timeframe", "pattern_detected", "pattern_kh", "entry_zone", "stop_loss", "take_profit_1", "take_profit_2", "confidence_score", "confluence_reasons", "risk_warning", "detailed_summary_kh"]
        }

        payload = {
            "contents": [{
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
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
                "maxOutputTokens": 2500
            }
        }

        try:
            data = self._post(payload)
            return json.loads(_extract_text(data))
        except Exception as e:
            logger.warning(f"[GeminiAnalyzer] analyze_user_chart_image failed: {e}")
            return None