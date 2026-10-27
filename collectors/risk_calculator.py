import logging

logger = logging.getLogger(__name__)

class RiskLotCalculator:
    """
    Interactive Trade Risk & Lot Size Calculator in Khmer for XAU/USD (Gold).
    Calculates exact recommended Lot Size based on:
    - Account Balance (ដើមទុនជា USD)
    - Risk Percentage (ភាគរយប្រថុយ % ដូចជា 1%, 2%, etc.)
    - Stop Loss in pips or entry/sl price points
    
    Standard Gold Contract Specs:
    - 1 Standard Lot (1.00) = 100 troy ounces
    - $1 move on Gold price = 10 pips (0.10 per pip) = $10 per standard lot
    - 1 pip move = $0.10 price difference = $1.00 PnL per 1.00 Lot (or $0.10 per 0.10 lot, $0.01 per 0.01 lot)
    - $1.00 change in Gold = 10 pips = $10 per 1.00 Lot
    """
    
    @staticmethod
    def calculate_lot_size(
        balance: float,
        risk_pct: float,
        entry_price: float = None,
        sl_price: float = None,
        sl_points_usd: float = None
    ) -> dict:
        """
        Calculates:
        - risk_amount_usd: Total money risked ($)
        - sl_distance_usd: Price distance in $
        - sl_pips: Price distance in standard Forex pips (1 USD = 10 pips)
        - recommended_lot: Exact calculated lot size
        - safe_lot: Conservative lot rounded down
        - aggressive_lot: Aggressive lot
        - leverage_warning: Warning if lot is too heavy
        """
        if balance <= 0:
            return {"error": "ដើមទុន (Balance) ត្រូវតែធំជាង 0"}
        if risk_pct <= 0:
            return {"error": "ភាគរយ Risk ត្រូវតែធំជាង 0"}

        # Calculate SL distance in USD
        if sl_points_usd is not None and sl_points_usd > 0:
            distance_usd = float(sl_points_usd)
        elif entry_price is not None and sl_price is not None:
            distance_usd = abs(float(entry_price) - float(sl_price))
        else:
            distance_usd = 10.0 # Default $10 SL (100 pips)

        if distance_usd <= 0.01:
            return {"error": "ចម្ងាយ Stop Loss តូចពេក (ត្រូវធំជាង $0.10)"}

        # Risk amount in USD
        risk_amount_usd = balance * (risk_pct / 100.0)

        # Gold math: 1 standard lot = 100 oz.
        # Moving $1.00 on 1.00 lot = $100 profit/loss.
        # Formula: Lot = Risk Amount ($) / (Distance in USD * 100)
        lot_size = risk_amount_usd / (distance_usd * 100.0)
        lot_rounded = round(lot_size, 2)
        if lot_rounded < 0.01:
            lot_rounded = 0.01 # Minimum broker standard lot

        pips = round(distance_usd * 10, 1)

        # Risk level assessment
        if risk_pct <= 1.0:
            style = "🛡️ Conservative (សុវត្ថិភាពខ្ពស់បំផុត)"
        elif risk_pct <= 2.5:
            style = "⚖️ Professional (កម្រិតស្តង់ដារ Trader អាជីព)"
        elif risk_pct <= 5.0:
            style = "⚠️ Moderate Aggressive (ប្រថុយគួរសម)"
        else:
            style = "🚨 Ultra High Risk / Gambling (ប្រថុយខ្ពស់ខ្លាំង!)"

        # Notional position value
        notional_value = lot_rounded * 100.0 * (entry_price or 4360.0)
        effective_leverage = round(notional_value / balance, 1)

        return {
            "balance": balance,
            "risk_pct": risk_pct,
            "risk_amount_usd": round(risk_amount_usd, 2),
            "distance_usd": round(distance_usd, 2),
            "pips": pips,
            "lot_size": lot_rounded,
            "raw_lot": lot_size,
            "style": style,
            "effective_leverage": effective_leverage,
            "entry_price": entry_price,
            "sl_price": sl_price
        }

    @staticmethod
    def parse_user_input(text: str) -> dict:
        """
        Parses flexible user command arguments:
        Examples:
        - /lot 1000 1 10  (Balance=$1000, Risk=1%, SL=$10)
        - /lot 500 2 4365 4355 (Balance=$500, Risk=2%, Entry=4365, SL=4355)
        - /risk 2000 1.5 5 (Balance=$2000, Risk=1.5%, SL=$5)
        """
        import re
        tokens = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", text)
        if not tokens:
            return None

        vals = [float(t) for t in tokens]
        if len(vals) == 1:
            # Just balance provided e.g. /lot 1000 (defaults to 1% risk, $10 SL)
            return {"balance": vals[0], "risk_pct": 1.0, "sl_points_usd": 10.0}
        elif len(vals) == 2:
            # Balance and Risk% e.g. /lot 1000 2
            return {"balance": vals[0], "risk_pct": vals[1], "sl_points_usd": 10.0}
        elif len(vals) == 3:
            # Balance, Risk%, and SL distance in $ e.g. /lot 1000 2 8
            return {"balance": vals[0], "risk_pct": vals[1], "sl_points_usd": vals[2]}
        elif len(vals) >= 4:
            # Balance, Risk%, Entry Price, SL Price e.g. /lot 1000 2 4365 4355
            return {
                "balance": vals[0],
                "risk_pct": vals[1],
                "entry_price": vals[2],
                "sl_price": vals[3],
                "sl_points_usd": abs(vals[2] - vals[3])
            }
        return None
