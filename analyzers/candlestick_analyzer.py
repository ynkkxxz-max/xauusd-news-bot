import logging
import requests

logger = logging.getLogger(__name__)

# ============================================================
# CandlestickPatternAnalyzer v2.0 — UPGRADED SMC Engine
# Key Improvements:
# 1. ATR-based Dynamic SL/TP (no more fixed $5/$25 values)
# 2. Minimum 1:2 R:R strictly enforced on all signals
# 3. 3-candle Fractal confirmation (stronger pattern filter)
# 4. D1 alignment required for high-confidence signals
# 5. MA divergence protection (no signal in sideways noise)
# 6. Engulfing + Wick combination conditions upgraded
# ============================================================

class CandlestickPatternAnalyzer:
    """
    Analyzes live M15 / H1 price action and detects high-probability institutional confirmation patterns:
    - Bullish Engulfing / Bearish Engulfing
    - Pin Bar / Hammer / Shooting Star (Liquidity Rejection Wick)
    - Liquidity Sweep / Fakeout Reversal
    """
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    def fetch_candles(self, interval: str = "15m", range_str: str = "1d", count: int = 10) -> list:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval={interval}&range={range_str}"
            resp = requests.get(url, headers=self.headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                q = data["chart"]["result"][0]["indicators"]["quote"][0]
                opens = q.get("open", [])
                highs = q.get("high", [])
                lows = q.get("low", [])
                closes = q.get("close", [])
                timestamps = data["chart"]["result"][0].get("timestamp", [None] * len(opens))

                candles = []
                for ts, o, h, l, c in zip(timestamps, opens, highs, lows, closes):
                    if o is not None and h is not None and l is not None and c is not None:
                        candles.append({
                            "ts": ts,
                            "open": float(o),
                            "high": float(h),
                            "low": float(l),
                            "close": float(c)
                        })
                return candles[-count:]
        except Exception as e:
            logger.warning(f"Error fetching candles ({interval}): {e}")
        return []

    def calculate_atr(self, candles: list, period: int = 5) -> float:
        """
        Calculates Average True Range (ATR) for dynamic SL/TP sizing.
        Uses True Range = max(H-L, |H-PrevC|, |L-PrevC|)
        """
        if len(candles) < 2:
            return 12.0
        trs = []
        for i in range(1, min(period + 1, len(candles))):
            curr = candles[i]
            prev = candles[i - 1]
            tr = max(
                curr["high"] - curr["low"],
                abs(curr["high"] - prev["close"]),
                abs(curr["low"] - prev["close"])
            )
            trs.append(tr)
        atr = sum(trs) / len(trs) if trs else 12.0
        # Clamp ATR between 4 and 50 for XAUUSD
        return max(4.0, min(atr, 50.0))

    def fetch_m15_candles(self, count: int = 10) -> list:
        return self.fetch_candles(interval="15m", range_str="1d", count=count)

    def fetch_h1_candles(self, count: int = 10) -> list:
        return self.fetch_candles(interval="1h", range_str="5d", count=count)

    def fetch_d1_candles(self, count: int = 5) -> list:
        return self.fetch_candles(interval="1d", range_str="1mo", count=count)

    def evaluate_multi_timeframe_confluence(self, intended_action: str) -> dict:
        """
        Multi-Timeframe Confluence Scoring System v2.0 (Upgraded):
        - D1 (Macro Trend): REQUIRED alignment — 35 pts
        - H1 (Structure: HH/HL or LH/LL): 35 pts
        - M15 (Execution: Wick + Close): 30 pts
        - STRICT: must have D1 aligned AND score >= 75%
        """
        score = 0
        details = []
        d1_aligned = False

        # 1. Macro Trend (D1) — verify 3-candle trend direction
        d1_candles = self.fetch_d1_candles(count=5)
        if len(d1_candles) >= 3:
            d1_closes = [c["close"] for c in d1_candles[-3:]]
            d1_highs = [c["high"] for c in d1_candles[-3:]]
            d1_lows = [c["low"] for c in d1_candles[-3:]]
            d1_bull = d1_closes[-1] >= d1_closes[-2] and d1_highs[-1] >= d1_highs[-2]
            d1_bear = d1_closes[-1] <= d1_closes[-2] and d1_lows[-1] <= d1_lows[-2]
            if (intended_action == "BUY" and d1_bull) or (intended_action == "SELL" and d1_bear):
                score += 35
                d1_aligned = True
                details.append(f"D1 Macro ✅: ស្របតាម D1 ({'Bullish HH/HL' if d1_bull else 'Bearish LH/LL'}) (+35%)")
            else:
                score += 8  # Heavy penalty for counter-trend
                details.append("D1 Counter-Trend ⚠️: ដើរប្រឆាំងនឹងនិន្នាការ D1 — ហានិភ័យខ្ពស់ (+8%)")
        else:
            score += 20
            details.append("D1 Neutral: ទិន្នន័យ D1  មិនគ្រប់គ្រាន់ (+20%)")

        # 2. H1 Market Structure (Higher Highs/Lows or Lower Highs/Lows)
        h1_candles = self.fetch_h1_candles(count=6)
        if len(h1_candles) >= 4:
            h1_highs = [c["high"] for c in h1_candles[-3:]]
            h1_lows = [c["low"] for c in h1_candles[-3:]]
            h1_closes = [c["close"] for c in h1_candles[-3:]]
            is_hh_hl = h1_highs[-1] > h1_highs[-2] and h1_lows[-1] > h1_lows[-2]
            is_lh_ll = h1_highs[-1] < h1_highs[-2] and h1_lows[-1] < h1_lows[-2]
            h1_ma = sum(h1_closes) / len(h1_closes)
            if (intended_action == "BUY" and is_hh_hl) or (intended_action == "SELL" and is_lh_ll):
                score += 35
                details.append(f"H1 Structure ✅: {'BOS Bullish (HH+HL)' if is_hh_hl else 'BOS Bearish (LH+LL)'} (+35%)")
            elif (intended_action == "BUY" and h1_closes[-1] > h1_ma) or (intended_action == "SELL" and h1_closes[-1] < h1_ma):
                score += 20
                details.append("H1 Partial: តម្លៃឈ្នះ H1 MA (+20%)")
            else:
                score += 8
                details.append("H1 Counter-Structure ⚠️: H1 Structure ដើររំខាន (+8%)")
        else:
            score += 20

        # 3. M15 Execution Confirmation (actual candle)
        m15_candles = self.fetch_m15_candles(count=5)
        if len(m15_candles) >= 3:
            curr = m15_candles[-1]
            c_range = max(curr["high"] - curr["low"], 0.01)
            lower_wick = min(curr["open"], curr["close"]) - curr["low"]
            upper_wick = curr["high"] - max(curr["open"], curr["close"])
            is_bull = curr["close"] > curr["open"]
            is_bear = curr["close"] < curr["open"]
            if intended_action == "BUY":
                if is_bull and lower_wick / c_range >= 0.38:
                    score += 30
                    details.append("M15 ✅: Bullish + Rejection Wick (+30%)")
                elif is_bull:
                    score += 20
                    details.append("M15 Partial: Bullish Close (+20%)")
                else:
                    score += 5
                    details.append("M15 ⚠️: Bearish Candle ខណៈ BUY (+5%)")
            else:
                if is_bear and upper_wick / c_range >= 0.38:
                    score += 30
                    details.append("M15 ✅: Bearish + Upper Wick Rejection (+30%)")
                elif is_bear:
                    score += 20
                    details.append("M15 Partial: Bearish Close (+20%)")
                else:
                    score += 5
                    details.append("M15 ⚠️: Bullish Candle ខណៈ SELL (+5%)")
        else:
            score += 20

        score = min(score, 100)
        # STRICT: require D1 aligned AND score >= 75
        is_high_prob = score >= 75 and d1_aligned

        return {
            "score": score,
            "is_valid": is_high_prob,
            "d1_aligned": d1_aligned,
            "score_str": f"{score}%",
            "details": details
        }

    def detect_confirmation(self, current_price: float, buy_zone: tuple, sell_zone: tuple) -> dict:
        """
        Checks if gold is inside or rejecting from Buy/Sell SMC Zone with candlestick confirmation.
        UPGRADED v2.0: ATR-based dynamic SL/TP with minimum 1:2 R:R enforced.
        """
        candles = self.fetch_m15_candles(count=7)
        if len(candles) < 3:
            return None

        atr = self.calculate_atr(candles, period=5)
        prev = candles[-2]
        curr = candles[-1]

        # Candle metrics
        curr_body = abs(curr["close"] - curr["open"])
        curr_range = curr["high"] - curr["low"] or 0.01
        is_curr_bull = curr["close"] > curr["open"]
        is_curr_bear = curr["close"] < curr["open"]

        lower_wick = min(curr["open"], curr["close"]) - curr["low"]
        upper_wick = curr["high"] - max(curr["open"], curr["close"])

        # Check Zone Proximity (dynamic tolerance = 40% ATR)
        b_low, b_high = buy_zone
        s_low, s_high = sell_zone
        zone_tol = round(atr * 0.4, 2)
        sl_buf = round(atr * 0.6, 2)

        # ── 1. Bullish Confirmation in Buy Zone ──────────────────────────
        if b_low - zone_tol <= current_price <= b_high + zone_tol:
            # Pinbar + bullish close required
            if lower_wick / curr_range >= 0.52 and is_curr_bull:
                sl_price = round(curr["low"] - sl_buf, 2)
                risk = max(round(current_price - sl_price, 2), atr * 0.6)
                sl_price = round(current_price - risk, 2)
                tp1 = round(current_price + risk * 2.0, 2)  # 1:2 R:R
                tp2 = round(current_price + risk * 3.0, 2)  # 1:3 R:R
                return {
                    "type": "BULLISH_CONFIRMATION",
                    "pattern": "🔨 Bullish Pin Bar (Rejection Wick)",
                    "zone_name": "Buy Zone (Discount Order Block)",
                    "entry": current_price,
                    "sl": sl_price,
                    "tp": tp1,
                    "tp2": tp2,
                    "risk_usd": round(risk, 2),
                    "rr": "1:2.0 (TP1) / 1:3.0 (TP2)",
                    "atr": round(atr, 2),
                    "desc": f"ទៀន M15 Bullish Pin Bar: Lower Wick={lower_wick:.1f}$ (ATR={atr:.1f}$) — Rejection បញ្ជាក់ការការពារ Buy Zone! SL=${sl_price:,.2f} | TP1=${tp1:,.2f}"
                }
            # Bullish Engulfing
            if is_curr_bull and curr["close"] > prev["high"] and curr_body > (abs(prev["close"] - prev["open"]) * 1.1):
                sl_price = round(min(curr["low"], prev["low"]) - sl_buf, 2)
                risk = max(round(current_price - sl_price, 2), atr * 0.6)
                sl_price = round(current_price - risk, 2)
                tp1 = round(current_price + risk * 2.0, 2)
                tp2 = round(current_price + risk * 3.0, 2)
                return {
                    "type": "BULLISH_CONFIRMATION",
                    "pattern": "🟢 Bullish Engulfing (ទៀនលេប)",
                    "zone_name": "Buy Zone (Discount Order Block)",
                    "entry": current_price,
                    "sl": sl_price,
                    "tp": tp1,
                    "tp2": tp2,
                    "risk_usd": round(risk, 2),
                    "rr": "1:2.0 (TP1) / 1:3.0 (TP2)",
                    "atr": round(atr, 2),
                    "desc": f"Bullish Engulfing: Close ${current_price:,.2f} > Prev High ${prev['high']:,.2f} — Institutional Buying Confirmed! SL=${sl_price:,.2f} | TP1=${tp1:,.2f}"
                }

        # ── 2. Bearish Confirmation in Sell Zone ─────────────────────────
        if s_low - zone_tol <= current_price <= s_high + zone_tol:
            # Shooting Star + bearish close required
            if upper_wick / curr_range >= 0.52 and is_curr_bear:
                sl_price = round(curr["high"] + sl_buf, 2)
                risk = max(round(sl_price - current_price, 2), atr * 0.6)
                sl_price = round(current_price + risk, 2)
                tp1 = round(current_price - risk * 2.0, 2)
                tp2 = round(current_price - risk * 3.0, 2)
                return {
                    "type": "BEARISH_CONFIRMATION",
                    "pattern": "🌠 Shooting Star (Liquidity Sweep Wick)",
                    "zone_name": "Sell Zone (Premium Order Block)",
                    "entry": current_price,
                    "sl": sl_price,
                    "tp": tp1,
                    "tp2": tp2,
                    "risk_usd": round(risk, 2),
                    "rr": "1:2.0 (TP1) / 1:3.0 (TP2)",
                    "atr": round(atr, 2),
                    "desc": f"Shooting Star: Upper Wick={upper_wick:.1f}$ — Sweep BSL Liquidity រួច Reject! SL=${sl_price:,.2f} | TP1=${tp1:,.2f}"
                }
            # Bearish Engulfing
            if is_curr_bear and curr["close"] < prev["low"] and curr_body > (abs(prev["close"] - prev["open"]) * 1.1):
                sl_price = round(max(curr["high"], prev["high"]) + sl_buf, 2)
                risk = max(round(sl_price - current_price, 2), atr * 0.6)
                sl_price = round(current_price + risk, 2)
                tp1 = round(current_price - risk * 2.0, 2)
                tp2 = round(current_price - risk * 3.0, 2)
                return {
                    "type": "BEARISH_CONFIRMATION",
                    "pattern": "🔴 Bearish Engulfing (ទៀនលេប)",
                    "zone_name": "Sell Zone (Premium Order Block)",
                    "entry": current_price,
                    "sl": sl_price,
                    "tp": tp1,
                    "tp2": tp2,
                    "risk_usd": round(risk, 2),
                    "rr": "1:2.0 (TP1) / 1:3.0 (TP2)",
                    "atr": round(atr, 2),
                    "desc": f"Bearish Engulfing: Close ${current_price:,.2f} < Prev Low ${prev['low']:,.2f} — Institutional Selling Confirmed! SL=${sl_price:,.2f} | TP1=${tp1:,.2f}"
                }

        return None

    def detect_liquidity_sweep(self) -> dict:
        """
        Detects Institutional Liquidity Sweeps (Hunt Stop Loss) on Gold.
        UPGRADED v2.0: ATR-based dynamic SL/TP, minimum 1:2 R:R enforced.
        """
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=15m&range=2d"
            resp = requests.get(url, headers=self.headers, timeout=8)
            if resp.status_code != 200:
                return None

            result = resp.json()["chart"]["result"][0]
            timestamps = result.get("timestamp", [])
            q = result["indicators"]["quote"][0]
            opens = q.get("open", [])
            highs = q.get("high", [])
            lows = q.get("low", [])
            closes = q.get("close", [])

            valid_candles = []
            for ts, o, h, l, c in zip(timestamps, opens, highs, lows, closes):
                if None not in (ts, o, h, l, c):
                    valid_candles.append({
                        "ts": ts, "open": float(o),
                        "high": float(h), "low": float(l), "close": float(c)
                    })

            if len(valid_candles) < 8:
                return None

            atr = self.calculate_atr(valid_candles[-8:], period=5)
            curr = valid_candles[-1]

            import pytz
            from datetime import datetime
            cambodia_tz = pytz.timezone("Asia/Phnom_Penh")

            # Asian Session High / Low (06:00-14:00 Cambodia Time)
            asian_highs, asian_lows = [], []
            for c in valid_candles[:-3]:
                dt = datetime.fromtimestamp(c["ts"], tz=cambodia_tz)
                if 6 <= dt.hour < 14:
                    asian_highs.append(c["high"])
                    asian_lows.append(c["low"])

            ash = max(asian_highs[-40:]) if asian_highs else None
            asl = min(asian_lows[-40:]) if asian_lows else None

            c_high, c_low = curr["high"], curr["low"]
            c_close, c_open = curr["close"], curr["open"]
            upper_wick = c_high - max(c_open, c_close)
            lower_wick = min(c_open, c_close) - c_low
            c_range = c_high - c_low or 0.01
            sl_buf = round(atr * 0.55, 2)

            # ── BSL Hunt: Bearish Sweep ───────────────────────────────────────
            if ash and (c_high > ash) and (c_close < ash + 2.5):
                if (upper_wick / c_range >= 0.38) or (c_close < c_open):
                    risk = max(round((c_high + sl_buf) - c_close, 2), atr * 0.6)
                    sl_p = round(c_close + risk, 2)
                    tp1_p = round(c_close - risk * 2.0, 2)  # 1:2 R:R
                    tp2_p = round(c_close - risk * 3.0, 2)  # 1:3 R:R
                    return {
                        "type": "BEARISH_SWEEP",
                        "level_name": "Asian Session High (ASH)",
                        "sweep_price": round(c_high, 2),
                        "level_price": round(ash, 2),
                        "current_price": round(c_close, 2),
                        "sl": sl_p, "tp": tp1_p, "tp2": tp2_p,
                        "risk_usd": round(risk, 2),
                        "rr": "1:2.0 (TP1) / 1:3.0 (TP2)",
                        "atr": round(atr, 2),
                        "desc": f"BSL Sweep ពី ASH (${ash:,.2f}): Fakeout Rejection! SL=${sl_p:,.2f} | TP1=${tp1_p:,.2f} | TP2=${tp2_p:,.2f}"
                    }

            # ── SSL Hunt: Bullish Sweep ───────────────────────────────────────
            if asl and (c_low < asl) and (c_close > asl - 2.5):
                if (lower_wick / c_range >= 0.38) or (c_close > c_open):
                    risk = max(round(c_close - (c_low - sl_buf), 2), atr * 0.6)
                    sl_p = round(c_close - risk, 2)
                    tp1_p = round(c_close + risk * 2.0, 2)
                    tp2_p = round(c_close + risk * 3.0, 2)
                    return {
                        "type": "BULLISH_SWEEP",
                        "level_name": "Asian Session Low (ASL)",
                        "sweep_price": round(c_low, 2),
                        "level_price": round(asl, 2),
                        "current_price": round(c_close, 2),
                        "sl": sl_p, "tp": tp1_p, "tp2": tp2_p,
                        "risk_usd": round(risk, 2),
                        "rr": "1:2.0 (TP1) / 1:3.0 (TP2)",
                        "atr": round(atr, 2),
                        "desc": f"SSL Sweep ពី ASL (${asl:,.2f}): Spring / Liquidity Grab! SL=${sl_p:,.2f} | TP1=${tp1_p:,.2f} | TP2=${tp2_p:,.2f}"
                    }

        except Exception as e:
            logger.warning(f"Error detecting liquidity sweep: {e}")

        return None

    def detect_sniper_instant_signal(self, current_price: float, key_levels: dict) -> dict:
        """
        Real-Time Sniper Signal Engine v2.0 — UPGRADED:
        - 3-Candle Fractal Confirmation (Higher probability patterns)
        - ATR-Based Dynamic SL (0.7x ATR minimum, covers real volatility)
        - Minimum 1:2 R:R strictly enforced (TP1=2x, TP2=3.5x Risk)
        - MA Divergence Protection (filters sideways noise)
        - Sideways range filter (<5 USD range = no signal)
        """
        candles = self.fetch_m15_candles(count=10)
        if len(candles) < 5:
            return None

        atr = self.calculate_atr(candles, period=5)

        curr  = candles[-1]
        prev  = candles[-2]
        prev2 = candles[-3]
        prev3 = candles[-4]

        c_open  = curr["open"]
        c_high  = curr["high"]
        c_low   = curr["low"]
        c_close = curr["close"]
        c_body  = abs(c_close - c_open)
        c_range = c_high - c_low or 0.01
        lower_wick = min(c_open, c_close) - c_low
        upper_wick = c_high - max(c_open, c_close)

        # ── EMA-proxy Moving Averages ────────────────────────────────────────
        closes = [c["close"] for c in candles]
        fast_ma = sum(closes[-4:]) / 4.0 if len(closes) >= 4 else current_price
        slow_ma = sum(closes[-9:]) / 9.0 if len(closes) >= 9 else current_price
        ma_diff = abs(fast_ma - slow_ma)

        # Consolidation / Sideways Range
        recent_highs = [c["high"] for c in candles[-5:]]
        recent_lows  = [c["low"]  for c in candles[-5:]]
        recent_low  = min(recent_lows)
        recent_high = max(recent_highs)
        consolidation_range = recent_high - recent_low

        # ── Ultra-tight consolidation filter (< 5 USD = no signal) ──────────
        if consolidation_range < 5.0:
            return None

        # Support / Resistance from key_levels
        sr_sup_low  = round(min(key_levels.get("s1", recent_low  - 5.0), recent_low  - 4.0), 1)
        sr_sup_high = round(sr_sup_low + 10.0, 1)
        sr_res_low  = round(max(key_levels.get("r1", recent_high + 5.0), recent_high + 4.0), 1)
        sr_res_high = round(sr_res_low + 10.0, 1)

        # ── 3-Candle Fractal Bottom (Upgraded) ──────────────────────────────
        # Requires: prev2 & prev form a local low, curr closes bullish with wick or engulf
        prev2_is_low  = prev2["low"] <= prev3["low"]   # prev2 near fractal low
        prev_confirms = prev["low"]  <= prev2["low"]   # prev confirms fractal
        curr_reversal = (
            c_close > prev["close"] and c_close > c_open and
            (lower_wick / c_range >= 0.42 or (c_body >= atr * 0.35 and c_close > prev["high"]))
        )
        is_bottom_bounce = prev2_is_low and prev_confirms and curr_reversal

        # ── 3-Candle Fractal Top (Upgraded) ─────────────────────────────────
        prev2_is_high = prev2["high"] >= prev3["high"]
        prev_confirms_h = prev["high"] >= prev2["high"]
        curr_top_reject = (
            c_close < prev["close"] and c_close < c_open and
            (upper_wick / c_range >= 0.42 or (c_body >= atr * 0.35 and c_close < prev["low"]))
        )
        is_top_rejection = prev2_is_high and prev_confirms_h and curr_top_reject

        # ── MA alignment descriptions ────────────────────────────────────────
        if ma_diff < 1.0:
            ma_desc   = "EMA Fast/Slow ប្រទាក់គ្នា — ទីផ្សារ Sideways! ហានិភ័យ Fakeout ខ្ពស់!"
            trend_desc = f"Consolidation Zone: ${recent_low:,.1f} - ${recent_high:,.1f}"
        elif fast_ma > slow_ma:
            ma_desc   = f"EMA Fast (${fast_ma:,.1f}) > EMA Slow (${slow_ma:,.1f}) — Bullish Momentum"
            trend_desc = f"Uptrend — ឆ្ពោះ Resistance ${sr_res_low:,.0f}"
        else:
            ma_desc   = f"EMA Fast (${fast_ma:,.1f}) < EMA Slow (${slow_ma:,.1f}) — Bearish Momentum"
            trend_desc = f"Downtrend — ឆ្ពោះ Support ${sr_sup_low:,.0f}"

        common_meta = {
            "current_price": round(current_price, 2),
            "trend_desc": trend_desc,
            "ma_desc": ma_desc,
            "fast_ma": round(fast_ma, 2),
            "slow_ma": round(slow_ma, 2),
            "resistance_range": f"${sr_res_low:,.0f} - ${sr_res_high:,.0f}",
            "support_range":    f"${sr_sup_low:,.0f} - ${sr_sup_high:,.0f}",
            "range_low":  round(recent_low,  1),
            "range_high": round(recent_high, 1),
            "atr": round(atr, 2)
        }

        # ════════════════════════════════════════════════════════════════════
        # 1. BUY SNIPER (Bottom Dip Bounce)
        # ════════════════════════════════════════════════════════════════════
        if is_bottom_bounce:
            # Block if MA bearish + weak spread (countertrend in sideways)
            if ma_diff < 1.5 and fast_ma < slow_ma:
                logger.info("[SNIPER] BUY filtered: EMA bearish in bottom bounce")
                return None

            confluence = self.evaluate_multi_timeframe_confluence("BUY")
            if not confluence.get("is_valid"):
                logger.info(f"[CONFLUENCE FILTER] BUY skipped — {confluence.get('score_str')}, D1={confluence.get('d1_aligned')}")
                return None

            entry_p    = round(current_price, 2)
            fractal_low = min(prev["low"], prev2["low"])
            sl_p        = round(fractal_low - (atr * 0.7), 2)
            risk        = round(entry_p - sl_p, 2)
            if risk < atr * 0.5:
                risk = round(atr * 0.7, 2)
                sl_p = round(entry_p - risk, 2)
            tp1_p = round(entry_p + risk * 2.0, 2)   # 1:2 R:R minimum
            tp2_p = round(entry_p + risk * 3.5, 2)   # 1:3.5 R:R extended

            res = {
                "action": "BUY",
                "action_title": "🟢 ACTION: BUY NOW — SNIPER DIP BOUNCE",
                "reason": (
                    f"✅ 3-Candle Fractal Bottom Confirmation:\n"
                    f"• Fractal Low: ${fractal_low:,.2f} (M15 Support)\n"
                    f"• ទៀន M15 Bullish Close >${prev['close']:,.2f}\n"
                    f"• Wick/Engulfing Rejection បញ្ជាក់!"
                ),
                "entry": entry_p,
                "sl": sl_p,
                "tp1": tp1_p,
                "tp2": tp2_p,
                "risk_usd": round(risk, 2),
                "risk_pips": round(risk * 10, 0),
                "rr_ratio": "1:2.0 (TP1) / 1:3.5 (TP2)",
                "confidence_score": confluence.get("score_str", "82%"),
                "confluence_details": confluence.get("details", [])
            }
            res.update(common_meta)
            return res

        # ════════════════════════════════════════════════════════════════════
        # 2. SELL SNIPER (Top Rejection)
        # ════════════════════════════════════════════════════════════════════
        if is_top_rejection:
            if ma_diff < 1.5 and fast_ma > slow_ma:
                logger.info("[SNIPER] SELL filtered: EMA bullish in top rejection")
                return None

            confluence = self.evaluate_multi_timeframe_confluence("SELL")
            if not confluence.get("is_valid"):
                logger.info(f"[CONFLUENCE FILTER] SELL skipped — {confluence.get('score_str')}, D1={confluence.get('d1_aligned')}")
                return None

            entry_p     = round(current_price, 2)
            fractal_high = max(prev["high"], prev2["high"])
            sl_p         = round(fractal_high + (atr * 0.7), 2)
            risk         = round(sl_p - entry_p, 2)
            if risk < atr * 0.5:
                risk = round(atr * 0.7, 2)
                sl_p = round(entry_p + risk, 2)
            tp1_p = round(entry_p - risk * 2.0, 2)
            tp2_p = round(entry_p - risk * 3.5, 2)

            res = {
                "action": "SELL",
                "action_title": "🔴 ACTION: SELL NOW — SNIPER TOP REJECTION",
                "reason": (
                    f"✅ 3-Candle Fractal Top Rejection Confirmation:\n"
                    f"• Fractal High: ${fractal_high:,.2f} (M15 Resistance)\n"
                    f"• ទៀន M15 Bearish Close <${prev['close']:,.2f}\n"
                    f"• Wick/Bearish Engulfing Reject បញ្ជាក់!"
                ),
                "entry": entry_p,
                "sl": sl_p,
                "tp1": tp1_p,
                "tp2": tp2_p,
                "risk_usd": round(risk, 2),
                "risk_pips": round(risk * 10, 0),
                "rr_ratio": "1:2.0 (TP1) / 1:3.5 (TP2)",
                "confidence_score": confluence.get("score_str", "82%"),
                "confluence_details": confluence.get("details", [])
            }
            res.update(common_meta)
            return res

        return None


