# Keywords directly relevant to XAUUSD / Gold / USD / Rates / Macroeconomics
GOLD_KEYWORDS = [
    "gold", "xau", "bullion", "yellow metal", "xauusd", "precious metals"
]

USD_KEYWORDS = [
    "dollar", "usd", "dxy", "greenback"
]

MACRO_KEYWORDS = [
    "fed", "federal reserve", "powell", "interest rate", "cpi", "inflation", 
    "nfp", "fomc", "treasury", "yield", "rate cut", "rate hike", "quantitative easing",
    "pboc", "china gold", "safe haven", "geopolitical", "middle east", "taiwan"
]

class GoldNewsFilter:
    @staticmethod
    def is_gold_relevant(title: str, description: str = "") -> bool:
        """Determines whether a piece of news directly influences XAUUSD."""
        text = f"{title} {description}".lower()
        
        # Explicit gold mention
        if any(kw in text for kw in GOLD_KEYWORDS):
            return True
        
        # High impact USD/Fed/Macro mention
        has_usd = any(kw in text for kw in USD_KEYWORDS)
        has_macro = any(kw in text for kw in MACRO_KEYWORDS)
        
        if has_usd and has_macro:
            return True
            
        # Fed or Central Bank direct policy moves
        if "interest rate" in text or "fomc" in text or "federal reserve" in text or "rate cut" in text or "rate hike" in text:
            return True

        return False
