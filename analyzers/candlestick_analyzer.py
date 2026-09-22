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
