# Keywords directly relevant to XAUUSD / Gold / USD / Rates / Macroeconomics
GOLD_KEYWORDS = [
    "gold", "xau", "bullion", "yellow metal", "xauusd", "precious metals"
]

USD_KEYWORDS = [
    "dollar", "usd", "dxy", "greenback"
]

# Major Economic, Central Bank, Technology, AI & Geopolitical Macro Drivers
MACRO_KEYWORDS = [
    # Central Banks & Rates
    "fed", "federal reserve", "powell", "warsh", "kevin warsh", "fomc", "interest rate", "rate cut", "rate hike", 
    "fomc statement", "fomc minutes", "fed speech", "monetary policy", "quantitative easing", "ecb", "boe", "boj", "pboc",
    # Major Macro Releases
    "cpi", "core cpi", "nfp", "non-farm", "nonfarm", "unemployment rate", "jobs report",
    "pce", "core pce", "gdp", "ppi", "retail sales", "ism manufacturing", "ism services",
    "treasury", "treasuries", "yield", "yields", "10-year yield", "bond market", "real yield",
    # Big Tech, AI & Global Tech Breakthroughs (Drivers of Yields, Liquidity & Inflation Expectations)
    "artificial intelligence", "ai revolution", "nvidia", "big tech", "semiconductor", 
    "datacenter energy", "tech rally", "liquidity surge", "openai", "chip export controls",
    # Safe Haven, Geopolitics & Global Events
    "china gold", "central bank buying", "safe haven", "safe-haven", "geopolitical",
    "middle east", "iran", "red sea", "taiwan", "russia", "ukraine", "sanctions", "tariff", "trade war"
]

class GoldNewsFilter:
    # High-impact catalysts that MUST trigger immediate alert (Zero-delay bypass)
    IMMEDIATE_CATALYSTS = [
        "fomc", "fed rate", "rate decision", "interest rate", "cpi", "nfp", "non-farm", 
        "nonfarm", "pce", "inflation rises", "inflation falls", "powell speech", "warsh speech", "kevin warsh", "fed chair",
        "emergency cut", "surprise hike", "war escalates", "missile", "attack", "invasion", "nuclear",
        "central bank reserves", "taiwan", "red sea crisis", "geopolitical shock", "strait of hormuz",
        "ai breakthrough", "tech disruption", "liquidity crisis", "market plunge", "gold surges",
        "flash crash", "sharp spike", "tariff hike", "sanctions", "bank failure", "default", "sovereign debt",
        "de-dollarization", "unprecedented move", "emergency meeting", "cyberattack"
    ]

    URGENT_SIGNALS = [
        "breaking", "urgent", "surprise", "emergency", "rate cut", "rate hike",
        "fomc statement", "cpi rises", "cpi falls", "nfp surges", "nfp misses",
        "escalates", "missile", "war", "attack", "sanctions", "china central bank",
        "powell", "warsh", "fed announces", "unprecedented", "crash", "surge", "plunge",
        "sharp drop", "rally", "spike", "plummets", "skyrockets", "tensions rise"
    ]

    @staticmethod
    def is_immediate_alert(title: str, description: str = "") -> bool:
        """Determines whether the news is a high-impact catalyst or market anomaly that must alert IMMEDIATELY."""
        text = f"{title} {description}".lower()
        return any(c in text for c in GoldNewsFilter.IMMEDIATE_CATALYSTS)

    @staticmethod
    def urgency_score(title: str) -> int:
        """Returns higher urgency score for major market catalysts."""
        text = title.lower()
        if any(c in text for c in GoldNewsFilter.IMMEDIATE_CATALYSTS):
            return 2
        return 1 if any(s in text for s in GoldNewsFilter.URGENT_SIGNALS) else 0

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
            
        # Fed or Central Bank direct policy moves or High Impact Catalysts
        if any(c in text for c in GoldNewsFilter.IMMEDIATE_CATALYSTS):
            return True

        if any(kw in text for kw in ["interest rate", "fomc", "federal reserve", "cpi", "nfp", "pce", "yield"]):
            return True

        return False

    @staticmethod
    def is_duplicate_or_similar(new_title: str, existing_titles: list, threshold: float = 0.35) -> bool:
        """
        Semantic Deduplication: Checks if the new news article is covering the same topic/event
        as any article broadcasted recently (e.g. within the last 4 hours) across different RSS feeds.
        Returns True if a similar article was already broadcasted.
        """
        import re

        def _stem(w: str) -> str:
            # Simple, fast suffix stripping for English news
            w = w.lower()
            for suffix in ("ing", "tion", "ions", "ment", "ments", "ies", "es", "ed", "s"):
                if w.endswith(suffix) and len(w) > len(suffix) + 3:
                    return w[:-len(suffix)]
            return w

        def _tokenize(text: str) -> set:
            # Clean punctuation, lower-case, and extract meaningful words (> 2 chars)
            words = re.findall(r"\b[a-zA-Z0-9%]{3,}\b", text.lower())
            stop_words = {
                "news", "says", "said", "today", "market", "markets", "price", "prices",
                "update", "live", "report", "breaking", "after", "amid", "with", "from",
                "over", "more", "into", "their", "will", "than", "some", "what", "could",
                "and", "the", "for"
            }
            return {_stem(w) for w in words if w not in stop_words}

        new_tokens = _tokenize(new_title)
        if not new_tokens:
            return False

        for past_title in existing_titles:
            past_tokens = _tokenize(past_title)
            if not past_tokens:
                continue

            intersection = new_tokens.intersection(past_tokens)
            union = new_tokens.union(past_tokens)
            similarity = len(intersection) / len(union) if union else 0.0

            # If 35%+ of core words match, or 3+ critical subject entities overlap
            if similarity >= threshold or len(intersection) >= 3:
                return True

        return False
