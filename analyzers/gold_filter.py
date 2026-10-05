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

import re

# Comprehensive exclusion filter for Sports, Football, Entertainment, Celebrity, Gossip, and Lifestyle
SPORTS_AND_GOSSIP_PATTERNS = [
    # Football / Soccer / Sports
    r"\b(manchester city|man city|premier league|champions league|football|soccer|fifa|uefa)\b",
    r"\b(la liga|serie a|bundesliga|world cup|olympics|nfl|nba|mlb|nhl|cricket|tennis|golf)\b",
    r"\b(tournament|referee|striker|goalkeeper|player|transfer fee|stadium|coach|ballon d'or|pinto)\b",
    r"\b(athletics|athlete|racing|f1|formula 1|grand prix|super bowl)\b",
    
    # Celebrity / Gossip / Romance / Personal Drama / Private Life / Non-Institutional Individual Affairs
    r"\b(dating|romance|relationship|divorce|girlfriend|boyfriend|breakup|ended relationship|split)\b",
    r"\b(affair|marriage|wedding|personal life|personal affairs|gossip|scandal|celebrity|hollywood|actor|actress|pop star)\b",
    r"\b(family feud|personal dispute|family drama|personal wealth|richest person|net worth rank|lottery|personal lawsuit|defamation|libel)\b",
    r"\b(memoir|biography|personal podcast|personal blog|childhood|lifestyle|diet|morning routine|hobby|hobbies|vacation|yacht|mansion|private jet)\b",
    r"\b(personal health|cosmetic surgery|plastic surgery|arrested for dui|speeding|petty theft|shoplifting)\b",
    r"\b(personal apology|personal confession|confesses to|regrets personal|personal reflection|personal matter|private matter)\b",
    
    # Entertainment / Streaming / Food / Lifestyle
    r"\b(netflix|movie|movies|film|films|cinema|box office|tv series|trailer|album|concert)\b",
    r"\b(french food|recipe|cuisine|restaurant|satire|parody|comedy|funny|horoscope)\b",
]

def _matches_any_keyword(text: str, keywords: list) -> bool:
    """Safe keyword matching: Uses strict word boundaries for short words (<=4 chars) to prevent substring false positives."""
    for kw in keywords:
        if len(kw) <= 4:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                return True
        else:
            if kw in text:
                return True
    return False

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
        return _matches_any_keyword(text, GoldNewsFilter.IMMEDIATE_CATALYSTS)

    @staticmethod
    def urgency_score(title: str) -> int:
        """Returns higher urgency score for major market catalysts."""
        text = title.lower()
        # VIP Immediate Priority Tier: Fed Chair/Governor Speeches (Kevin Warsh, Powell, FOMC)
        if any(w in text for w in ["kevin warsh", "warsh", "powell", "fomc statement", "fed rate decision"]):
            return 3
        if _matches_any_keyword(text, GoldNewsFilter.IMMEDIATE_CATALYSTS):
            return 2
        return 1 if _matches_any_keyword(text, GoldNewsFilter.URGENT_SIGNALS) else 0

    @staticmethod
    def is_gold_relevant(title: str, description: str = "") -> bool:
        """
        Determines whether a piece of news directly or indirectly influences XAUUSD / Financial Markets
        across the 7 Core News Pillars (Geopolitics, Macroeconomics, Fed/Monetary, Energy/Oil, Tech, Policies).
        Strictly rejects Sports, Football, Celebrity, Gossip, Opinion, and Lifestyle news.
        """
        clean_title = (title or "").strip()
        # Strictly reject speculative questions
        if "?" in clean_title:
            return False
        
        t_low = clean_title.lower()
        full_text = f"{title} {description}".lower()

        # Gate 0: Strict rejection of sports, football clubs (e.g. Manchester City), gossip, celebrities
        for pat in SPORTS_AND_GOSSIP_PATTERNS:
            if re.search(pat, full_text):
                return False

        opinion_markers = [
            "opinion:", "opinion |", "analysis:", "analysis |", "op-ed:", "op-ed |",
            "editorial:", "editorial |", "column:", "columnist:", "essay:", "viewpoint:", "perspective:"
        ]
        if any(t_low.startswith(marker) or f" {marker}" in t_low for marker in opinion_markers):
            return False

        text = full_text
        
        # 1. Explicit Gold mention
        if _matches_any_keyword(text, GOLD_KEYWORDS):
            return True

        # 2. Immediate high-impact catalysts (War, FOMC, Emergency, Hormuz, Sanctions)
        if _matches_any_keyword(text, GoldNewsFilter.IMMEDIATE_CATALYSTS):
            return True

        # 3. Geopolitical, War, and Global Conflict (Pillar 2 - safe-haven drivers)
        geopolitical_triggers = [
            "iran", "israel", "middle east", "war", "conflict", "strait of hormuz", "hormuz",
            "red sea", "russia", "ukraine", "taiwan", "missile", "airstrike", "drone attack",
            "military attack", "nuclear threat", "sanctions", "ceasefire", "peace deal", "trump war",
            "rial", "geopolitical", "safe haven", "safe-haven"
        ]
        if _matches_any_keyword(text, geopolitical_triggers):
            return True

        # 4. Energy & Commodities (Pillar 5 - inflation & market driver)
        energy_triggers = [
            "crude oil", "oil price", "oil prices", "brent", "wti", "opec", "energy crisis",
            "gas prices", "petroleum"
        ]
        if _matches_any_keyword(text, energy_triggers):
            return True

        # 5. Monetary Policy & Central Banks (Pillar 4)
        monetary_triggers = [
            "fed", "federal reserve", "powell", "warsh", "kevin warsh", "fomc", "interest rate",
            "rate cut", "rate hike", "ecb", "boe", "boj", "pboc", "central bank", "yield", "yields", "treasury"
        ]
        if _matches_any_keyword(text, monetary_triggers):
            return True

        # 6. Global Economy & Inflation (Pillar 1 & 7)
        macro_triggers = [
            "cpi", "inflation", "gdp", "nfp", "non-farm", "nonfarm", "jobs report", "pce", "ppi",
            "recession", "pmi", "tariff", "trade war", "de-dollarization", "debt ceiling", "sovereign debt"
        ]
        if _matches_any_keyword(text, macro_triggers):
            return True

        # 7. Check across all 7 Core News Pillars (Macro, Geopolitics, Tech/AI, Energy, Social, Laws/Tariffs)
        if _matches_any_keyword(text, MACRO_KEYWORDS):
            return True

        # 8. USD / Currency shocks (Pillar 1)
        if _matches_any_keyword(text, USD_KEYWORDS):
            return True

        # 9. Digital Currency, Bitcoin & Crypto (Digital Assets & Financial Innovation)
        if _matches_any_keyword(text, CRYPTO_KEYWORDS):
            return True

        return False

    @staticmethod
    def get_news_cluster(text: str) -> str:
        """Categorizes news into a high-level macro cluster for semantic cross-feed deduplication."""
        t = text.lower()
        # 1. US Jobs / Payrolls / Labor Market
        if any(k in t for k in ["non-farm", "nonfarm", "payroll", "payrolls", "unemployment", "job growth", "jobs report", "hiring", "labor market", "workforce"]) or ("job" in t and any(w in t for w in ["us", "fed", "report", "cool", "slow", "data", "cut", "rise", "fall", "jump", "stall"])):
            return "us_jobs"
        # 2. Inflation & CPI
        if any(k in t for k in ["cpi", "inflation", "pce", "producer price", "consumer price", "cost of living"]):
            return "inflation"
        # 3. Fed & Central Bank Rates
        if any(k in t for k in ["fomc", "powell", "kevin warsh", "rate cut", "rate hike", "interest rate", "basis point", "federal reserve"]) or ("fed " in t and any(w in t for w in ["rate", "policy", "pause", "hike", "cut"])):
            return "fed_rates"
        # 4. Energy & Crude Oil & Gas
        if any(k in t for k in ["crude oil", "brent", "wti", "oil price", "oil drop", "oil rise", "diesel", "gasoline", "lng", "fuel", "opec"]):
            return "energy_oil"
        # 5. Technology & AI & Semiconductors
        if any(k in t for k in ["nvidia", "semiconductor", "chipmaker", "tsmc", "intel", "amd", "blackwell", "artificial intelligence", "data center", "datacenter"]) or ("ai " in t and any(w in t for w in ["chip", "tech", "job", "model", "cloud", "server", "wall street"])):
            return "tech_ai"
        # 6. Crypto & Digital Assets
        if any(k in t for k in ["bitcoin", "btc", "ethereum", "crypto", "cryptocurrency", "stablecoin", "tether", "binance", "coinbase"]):
            return "crypto_assets"
        # 7. Middle East Geopolitics
        if any(k in t for k in ["gaza", "israel", "tel aviv", "lebanon", "beirut", "hezbollah", "houthi", "strait of hormuz", "red sea"]):
            return "middle_east"
        # 8. Russia & Ukraine
        if any(k in t for k in ["russia", "ukraine", "kyiv", "moscow", "kremlin", "zelensky", "putin"]):
            return "russia_ukraine"
        # 9. Tariffs & Trade Wars
        if any(k in t for k in ["tariff", "tariffs", "sanction", "sanctions", "trade war", "embargo"]):
            return "tariffs_trade"
        return ""

    @staticmethod
    def is_duplicate_or_similar(new_title: str, existing_titles: list, threshold: float = 0.35) -> bool:
        """
        Semantic Deduplication: Checks if the new news article is covering the same topic/event
        as any article broadcasted recently (e.g. within the last 4 hours) across different RSS feeds.
        Returns True if a similar article was already broadcasted.
        """
        import re

        # Fast Macro Cluster Match: If an article from the same specific cluster was already sent recently
        new_cluster = GoldNewsFilter.get_news_cluster(new_title)
        if new_cluster:
            for past_title in existing_titles:
                past_cluster = GoldNewsFilter.get_news_cluster(past_title)
                if new_cluster == past_cluster:
                    return True

        def _stem(w: str) -> str:
            w = w.lower()
            demonyms = {
                "israeli": "israel", "british": "britain", "russian": "russia",
                "lebanese": "lebanon", "mexican": "mexico", "canadian": "canada",
                "ukrainian": "ukraine", "iranian": "iran", "chinese": "china",
                "japanese": "japan", "american": "america"
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

        entities_list = [
            "israel", "lebanon", "russia", "ukraine", "iran", "trump", "biden",
            "opec", "china", "boe", "fed", "england", "us", "usa", "america",
            "japan", "jera", "sec", "nvidia", "intel", "amd", "tesla", "apple"
        ]
        topics_list = [
            "ai", "strike", "tariff", "sanction", "war", "rate", "inflation",
            "blackwell", "chip", "job", "jobs", "payroll", "nfp", "employment",
            "unemployment", "oil", "crude", "brent", "lng", "diesel", "gas",
            "energy", "crypto", "bitcoin", "btc", "hiring", "datacenter"
        ]

        for past_title in existing_titles:
            past_tokens = _tokenize(past_title)
            if not past_tokens:
                continue

            intersection = new_tokens.intersection(past_tokens)
            union = new_tokens.union(past_tokens)
            similarity = len(intersection) / len(union) if union else 0.0
            overlap_ratio = len(intersection) / min(len(new_tokens), len(past_tokens)) if min(len(new_tokens), len(past_tokens)) else 0.0

            # 1. Exact or High token overlap
            if similarity >= 0.45 or (overlap_ratio >= 0.35 and len(intersection) >= 3):
                return True

            # 2. Entity + Topic co-occurrence
            has_common_entity = any(e in intersection for e in entities_list) or ("england" in new_tokens and "england" in past_tokens)
            has_common_topic = any(t in intersection for t in topics_list)
            if has_common_entity and has_common_topic and len(intersection) >= 2:
                return True

        return False
