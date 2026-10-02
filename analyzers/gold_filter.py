# Keywords directly relevant to Digital Currency / Crypto / Blockchain / Financial Innovation
CRYPTO_KEYWORDS = [
    "bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency", "cryptocurrencies",
    "digital currency", "digital currencies", "cbdc", "stablecoin", "stablecoins",
    "tether", "usdt", "usdc", "sec crypto", "crypto etf", "spot btc", "spot bitcoin",
    "crypto regulation", "crypto ban", "crypto reserve", "strategic bitcoin reserve",
    "binance", "coinbase", "solana", "digital assets", "tokenization", "tokenized",
    "blockchain", "defi", "crypto market", "crypto crash", "crypto rally", "crypto hack", "halving"
]

# Keywords directly relevant to XAUUSD / Gold / USD / Rates / Macroeconomics
GOLD_KEYWORDS = [
    "gold", "xau", "bullion", "yellow metal", "xauusd", "precious metals"
]

USD_KEYWORDS = [
    "dollar", "usd", "dxy", "greenback"
]

# -------------------------------------------------------------------------
# The 7 Core Pillars of Market News (Defined by System Standards):
# 1. សេដ្ឋកិច្ច (Macroeconomics & Global Economy)
# 2. នយោបាយភូមិសាស្ត្រ (Geopolitics & Security)
# 3. បច្ចេកវិទ្យា (Technology, AI & Semiconductors)
# 4. គោលនយោបាយរូបិយវត្ថុ និងធនាគារកណ្តាល (Monetary Policy & Central Banks)
# 5. បរិស្ថាន និងធនធានធម្មជាតិ (Environment, Energy & Natural Resources)
# 6. កត្តាសង្គម និងប្រជាសាស្ត្រ (Social, Demographics & Labor Markets)
# 7. ច្បាប់ បទប្បញ្ញត្តិ និងគោលនយោបាយរដ្ឋាភិបាល (Laws, Tariffs & Government Policies)
# -------------------------------------------------------------------------
MACRO_KEYWORDS = [
    # 1. សេដ្ឋកិច្ច (Economy)
    "gdp", "cpi", "core cpi", "inflation", "pce", "core pce", "ppi", "retail sales",
    "unemployment rate", "jobs report", "non-farm", "nonfarm", "nfp", "recession",
    "economic growth", "ism manufacturing", "ism services", "pmi", "consumer sentiment",
    "treasury", "treasuries", "yield", "yields", "10-year yield", "bond market", "real yield",
    # 2. នយោបាយភូមិសាស្ត្រ (Geopolitics)
    "geopolitical", "safe haven", "safe-haven", "middle east", "iran", "israel", "red sea",
    "strait of hormuz", "russia", "ukraine", "taiwan", "war", "missile", "airstrike",
    "military attack", "escalation", "conflict",
    # 3. បច្ចេកវិទ្យា (Technology & AI)
    "artificial intelligence", "ai revolution", "nvidia", "big tech", "semiconductor",
    "datacenter energy", "tech rally", "liquidity surge", "openai", "chip export controls",
    "super intelligence", "quantum computing", "cyberattack",
    # 4. គោលនយោបាយរូបិយវត្ថុ និងធនាគារកណ្តាល (Monetary Policy & Central Banks)
    "fed", "federal reserve", "powell", "warsh", "kevin warsh", "fomc", "interest rate",
    "rate cut", "rate hike", "fomc statement", "fomc minutes", "fed speech", "monetary policy",
    "quantitative easing", "quantitative tightening", "qe", "qt", "ecb", "boe", "boj", "pboc",
    "central bank buying", "china gold", "central bank reserves",
    # 5. បរិស្ថាន និងធនធានធម្មជាតិ (Environment & Natural Resources)
    "crude oil", "brent", "wti", "opec", "petroleum", "energy crisis", "natural gas",
    "gold mining", "copper", "critical minerals", "climate disruption", "supply chain bottleneck",
    # 6. កត្តាសង្គម និងប្រជាសាស្ត្រ (Social & Demographics)
    "labor strike", "port strike", "union strike", "wage growth", "wage spiral",
    "demographic shift", "cost of living crisis", "consumer spending squeeze",
    # 7. ច្បាប់ បទប្បញ្ញត្តិ និងគោលនយោបាយរដ្ឋាភិបាល (Laws & Government Policies)
    "tariff", "trade war", "sanctions", "protectionism", "government shutdown",
    "debt ceiling", "fiscal deficit", "treasury issuance", "sovereign debt", "de-dollarization",
    "sec regulation", "crypto regulation", "banking oversight"
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
        # VIP Immediate Priority Tier: Fed Chair/Governor Speeches (Kevin Warsh, Powell, FOMC)
        if any(w in text for w in ["kevin warsh", "warsh", "powell", "fomc statement", "fed rate decision"]):
            return 3
        if any(c in text for c in GoldNewsFilter.IMMEDIATE_CATALYSTS):
            return 2
        return 1 if any(s in text for s in GoldNewsFilter.URGENT_SIGNALS) else 0

    @staticmethod
    def is_gold_relevant(title: str, description: str = "") -> bool:
        """
        Determines whether a piece of news directly or indirectly influences XAUUSD / Financial Markets
        across the 7 Core News Pillars (Geopolitics, Macroeconomics, Fed/Monetary, Energy/Oil, Tech, Policies).
        """
        clean_title = (title or "").strip()
        # Strictly reject speculative questions and opinion pieces (e.g. "Trump the environmentalist? ...")
        if "?" in clean_title:
            return False
        
        t_low = clean_title.lower()
        opinion_markers = [
            "opinion:", "opinion |", "analysis:", "analysis |", "op-ed:", "op-ed |",
            "editorial:", "editorial |", "column:", "columnist:", "essay:", "viewpoint:", "perspective:"
        ]
        if any(t_low.startswith(marker) or f" {marker}" in t_low for marker in opinion_markers):
            return False

        text = f"{title} {description}".lower()
        
        # 1. Explicit Gold mention
        if any(kw in text for kw in GOLD_KEYWORDS):
            return True

        # 2. Immediate high-impact catalysts (War, FOMC, Emergency, Hormuz, Sanctions)
        if any(c in text for c in GoldNewsFilter.IMMEDIATE_CATALYSTS):
            return True

        # 3. Geopolitical, War, and Global Conflict (Pillar 2 - safe-haven drivers)
        geopolitical_triggers = [
            "iran", "israel", "middle east", "war", "conflict", "strait of hormuz", "hormuz",
            "red sea", "russia", "ukraine", "taiwan", "missile", "airstrike", "drone attack",
            "military", "nuclear", "sanctions", "ceasefire", "peace deal", "trump war",
            "rial", "geopolitical", "safe haven", "safe-haven"
        ]
        if any(kw in text for kw in geopolitical_triggers):
            return True

        # 4. Energy & Commodities (Pillar 5 - inflation & market driver)
        energy_triggers = [
            "crude oil", "oil price", "oil prices", "brent", "wti", "opec", "energy crisis",
            "gas prices", "petroleum"
        ]
        if any(kw in text for kw in energy_triggers):
            return True

        # 5. Monetary Policy & Central Banks (Pillar 4)
        monetary_triggers = [
            "fed", "federal reserve", "powell", "warsh", "kevin warsh", "fomc", "interest rate",
            "rate cut", "rate hike", "ecb", "boe", "boj", "pboc", "central bank", "yield", "yields", "treasury"
        ]
        if any(kw in text for kw in monetary_triggers):
            return True

        # 6. Global Economy & Inflation (Pillar 1 & 7)
        macro_triggers = [
            "cpi", "inflation", "gdp", "nfp", "non-farm", "nonfarm", "jobs report", "pce", "ppi",
            "recession", "pmi", "tariff", "trade war", "de-dollarization", "debt ceiling", "sovereign debt"
        ]
        if any(kw in text for kw in macro_triggers):
            return True

        # 7. Check across all 7 Core News Pillars (Macro, Geopolitics, Tech/AI, Energy, Social, Laws/Tariffs)
        if any(kw in text for kw in MACRO_KEYWORDS):
            return True

        # 8. USD / Currency shocks (Pillar 1)
        has_usd = any(kw in text for kw in USD_KEYWORDS)
        if has_usd:
            return True

        # 9. Digital Currency, Bitcoin & Crypto (Digital Assets & Financial Innovation)
        if any(kw in text for kw in CRYPTO_KEYWORDS):
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
            w = w.lower()
            demonyms = {
                "israeli": "israel", "british": "britain", "russian": "russia",
                "lebanese": "lebanon", "mexican": "mexico", "canadian": "canada",
                "ukrainian": "ukraine", "iranian": "iran", "chinese": "china"
            }
            if w in demonyms:
                return demonyms[w]
            if "strike" in w:
                return "strike"
            for suffix in ("ing", "tion", "ions", "ment", "ments", "ies", "es", "ed", "s"):
                if w.endswith(suffix) and len(w) > len(suffix) + 3:
                    return w[:-len(suffix)]
            return w

        def _tokenize(text: str) -> set:
            words = re.findall(r"\b[a-zA-Z0-9%]{2,}\b", text.lower())
            stop_words = {
                "news", "says", "said", "today", "market", "markets", "price", "prices",
                "update", "live", "report", "breaking", "after", "amid", "with", "from",
                "over", "more", "into", "their", "will", "than", "some", "what", "could",
                "and", "the", "for", "boss", "poses", "threat", "fresh", "hit", "regional"
            }
            return {_stem(w) for w in words if w not in stop_words}

        new_tokens = _tokenize(new_title)
        if not new_tokens:
            return False

        entities_list = ["israel", "lebanon", "russia", "ukraine", "iran", "trump", "biden", "opec", "china", "boe", "fed", "england"]
        topics_list = ["ai", "strike", "tariff", "sanction", "war", "rate", "inflation", "blackwell", "chip"]

        for past_title in existing_titles:
            past_tokens = _tokenize(past_title)
            if not past_tokens:
                continue

            intersection = new_tokens.intersection(past_tokens)
            union = new_tokens.union(past_tokens)
            similarity = len(intersection) / len(union) if union else 0.0
            overlap_ratio = len(intersection) / min(len(new_tokens), len(past_tokens)) if min(len(new_tokens), len(past_tokens)) else 0.0

            # 1. Exact or High token overlap
            if similarity >= 0.50 or (overlap_ratio >= 0.40 and len(intersection) >= 3):
                return True

            # 2. Entity + Topic co-occurrence
            has_common_entity = any(e in intersection for e in entities_list) or ("england" in new_tokens and "england" in past_tokens)
            has_common_topic = any(t in intersection for t in topics_list)
            if has_common_entity and has_common_topic and len(intersection) >= 2:
                return True

        return False
