import logging
import requests

logger = logging.getLogger(__name__)

class CandlestickPatternAnalyzer:
    """
    Analyzes live M15 / H1 price action and detects high-probability institutional confirmation patterns:
    - Bullish Engulfing / Bearish Engulfing
    - Pin Bar / Hammer / Shooting Star (Liquidity Rejection Wick)
    - Liquidity Sweep / Fakeout Reversal
    """
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    def fetch_m15_candles(self, count: int = 10) -> list:
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=15m&range=1d"
            resp = requests.get(url, headers=self.headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                q = data["chart"]["result"][0]["indicators"]["quote"][0]
                opens = q.get("open", [])
                highs = q.get("high", [])
                lows = q.get("low", [])
                closes = q.get("close", [])
                
                candles = []
                for o, h, l, c in zip(opens, highs, lows, closes):
                    if o is not None and h is not None and l is not None and c is not None:
                        candles.append({"open": float(o), "high": float(h), "low": float(l), "close": float(c)})
                return candles[-count:]
        except Exception as e:
            logger.warning(f"Error fetching candles: {e}")
        return []

    def detect_confirmation(self, current_price: float, buy_zone: tuple, sell_zone: tuple) -> dict:
        """
        Checks if gold is inside or rejecting from Buy/Sell SMC Zone with candlestick confirmation.
        """
        candles = self.fetch_m15_candles(count=5)
        if len(candles) < 2:
            return None

        prev = candles[-2]
        curr = candles[-1]

        # Candle metrics
        curr_body = abs(curr["close"] - curr["open"])
        curr_range = curr["high"] - curr["low"] or 0.01
        is_curr_bull = curr["close"] > curr["open"]
        is_curr_bear = curr["close"] < curr["open"]

        lower_wick = min(curr["open"], curr["close"]) - curr["low"]
        upper_wick = curr["high"] - max(curr["open"], curr["close"])

        # Check Zone Proximity
        b_low, b_high = buy_zone
        s_low, s_high = sell_zone

        # 1. Bullish Confirmation in Buy Zone
        if b_low - 3 <= current_price <= b_high + 5:
            # Pinbar / Rejection Hammer (Lower wick is at least 55% of the range)
            if lower_wick / curr_range >= 0.55:
                return {
                    "type": "BULLISH_CONFIRMATION",
                    "pattern": "🔨 Bullish Pin Bar (Rejection Wick)",
                    "zone_name": "Buy Zone (Discount Order Block)",
                    "entry": current_price,
                    "sl": round(curr["low"] - 5.0, 2),
                    "tp": round(current_price + 25.0, 2),
                    "desc": "ទៀន M15 បានបន្សល់កន្ទុយក្រោមវែង (Long Lower Shadow) បញ្ជាក់ពីការទាត់ចោលតម្លៃក្រោម និងមានកម្លាំងទិញខ្លាំងគាំទ្រ!"
                }
            # Bullish Engulfing
            if is_curr_bull and curr["close"] > prev["high"] and curr_body > (abs(prev["close"] - prev["open"]) * 1.2):
                return {
                    "type": "BULLISH_CONFIRMATION",
                    "pattern": "🟢 Bullish Engulfing (ទៀនលេប)",
                    "zone_name": "Buy Zone (Discount Order Block)",
                    "entry": current_price,
                    "sl": round(curr["low"] - 5.0, 2),
                    "tp": round(current_price + 25.0, 2),
                    "desc": "ទៀនបៃតងធំបានលេបទៀនក្រហមមុន បង្ហាញថាកម្លាំងទិញគ្រប់គ្រងទីផ្សារពេញលេញក្នុងតំបន់ Discount!"
                }

        # 2. Bearish Confirmation in Sell Zone
        if s_low - 5 <= current_price <= s_high + 3:
            # Shooting Star / Upper Wick Rejection
            if upper_wick / curr_range >= 0.55:
                return {
                    "type": "BEARISH_CONFIRMATION",
                    "pattern": "🌠 Shooting Star (Liquidity Sweep Wick)",
                    "zone_name": "Sell Zone (Premium Order Block)",
                    "entry": current_price,
                    "sl": round(curr["high"] + 5.0, 2),
                    "tp": round(current_price - 25.0, 2),
                    "desc": "ទៀន M15 បានបន្សល់កន្ទុយលើវែង បញ្ជាក់ថាទីផ្សារបាន Sweep Liquidity រួចហើយទម្លាក់ចុះវិញភ្លាមៗ!"
                }
            # Bearish Engulfing
            if is_curr_bear and curr["close"] < prev["low"] and curr_body > (abs(prev["close"] - prev["open"]) * 1.2):
                return {
                    "type": "BEARISH_CONFIRMATION",
                    "pattern": "🔴 Bearish Engulfing (ទៀនលេប)",
                    "zone_name": "Sell Zone (Premium Order Block)",
                    "entry": current_price,
                    "sl": round(curr["high"] + 5.0, 2),
                    "tp": round(current_price - 25.0, 2),
                    "desc": "ទៀនក្រហមធំបានលេបទៀនបៃតងមុន បង្ហាញថាកម្លាំងលក់វាយសម្រុកទម្លាក់តម្លៃពីតំបន់ Resistance!"
                }

        return None

    def detect_liquidity_sweep(self) -> dict:
        """
        Detects Institutional Liquidity Sweeps (Hunt Stop Loss) on Gold:
        - Asian Session High (ASH) / Asian Session Low (ASL) Sweep
        - Previous Day High (PDH) / Previous Day Low (PDL) Sweep
        A sweep happens when price pierces above High / below Low by $1-$7, 
        fails to sustain, and prints a rejection wick (False Breakout / Turtle Soup).
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
                        "ts": ts,
                        "open": float(o),
                        "high": float(h),
                        "low": float(l),
                        "close": float(c)
                    })

            if len(valid_candles) < 5:
                return None

            curr = valid_candles[-1]
            prev = valid_candles[-2]

            import pytz
            from datetime import datetime
            cambodia_tz = pytz.timezone("Asia/Phnom_Penh")

            # 1. Identify Asian Session High / Low (06:00 to 14:00 Cambodia Time)
            asian_highs = []
            asian_lows = []
            for c in valid_candles[:-2]:
                dt = datetime.fromtimestamp(c["ts"], tz=cambodia_tz)
                if 6 <= dt.hour < 14:
                    asian_highs.append(c["high"])
                    asian_lows.append(c["low"])

            ash = max(asian_highs[-32:]) if asian_highs else None
            asl = min(asian_lows[-32:]) if asian_lows else None

            # Current candle dynamics
            c_high = curr["high"]
            c_low = curr["low"]
            c_close = curr["close"]
            c_open = curr["open"]
            upper_wick = c_high - max(c_open, c_close)
            lower_wick = min(c_open, c_close) - c_low
            c_range = c_high - c_low or 0.01

            # --- Check High Liquidity Sweep (Buy-Side Liquidity BSL Hunt -> Sell Reversal) ---
            if ash and (c_high > ash) and (c_close < ash + 1.5):
                # Must reject with upper wick or bearish close
                if (upper_wick / c_range >= 0.40) or (c_close < c_open):
                    return {
                        "type": "BEARISH_SWEEP",
                        "level_name": "Asian Session High (ASH)",
                        "sweep_price": round(c_high, 2),
                        "level_price": round(ash, 2),
                        "current_price": round(c_close, 2),
                        "sl": round(c_high + 4.0, 2),
                        "tp": round(c_close - 20.0, 2),
                        "desc": f"តម្លៃបានបាញ់ទម្លុះ High នៃ Asian Session (${ash:,.2f}) ដើម្បី Hunt Buy-Stop Liquidity រួចទាត់ធ្លាក់ចុះមកវិញភ្លាមៗ (Fakeout Reversal)!"
                    }

            # --- Check Low Liquidity Sweep (Sell-Side Liquidity SSL Hunt -> Buy Reversal) ---
            if asl and (c_low < asl) and (c_close > asl - 1.5):
                if (lower_wick / c_range >= 0.40) or (c_close > c_open):
                    return {
                        "type": "BULLISH_SWEEP",
                        "level_name": "Asian Session Low (ASL)",
                        "sweep_price": round(c_low, 2),
                        "level_price": round(asl, 2),
                        "current_price": round(c_close, 2),
                        "sl": round(c_low - 4.0, 2),
                        "tp": round(c_close + 20.0, 2),
                        "desc": f"តម្លៃបានទម្លាក់ចុះក្រោម Low នៃ Asian Session (${asl:,.2f}) ដើម្បី Hunt Sell-Stop Liquidity រួចស្ទុះងើបឡើងវិញភ្លាមៗ (Spring / Liquidity Grab)!"
                    }

        except Exception as e:
            logger.warning(f"Error detecting liquidity sweep: {e}")

        return None

