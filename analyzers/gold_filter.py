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
    "military attack", "escalation", "conflict", "north korea", "dprk", "pyongyang",
    "kim jong un", "kim jong-un", "south korea", "seoul", "xi jinping", "state visit", "summit",
    "nuclear escalation", "icbm", "ballistic missile", "bilateral talks", "dandong",
    # 3. បច្ចេកវិទ្យា (Technology, AI, Frontier Innovation & Aerospace)
    "artificial intelligence", "ai revolution", "nvidia", "big tech", "semiconductor",
    "datacenter energy", "tech rally", "liquidity surge", "openai", "chip export controls",
    "super intelligence", "quantum computing", "cyberattack", "elon musk", "musk", "tesla",
    "spacex", "starship", "roadster", "optimus", "cybertruck", "robotaxi", "falcon heavy",
    "neuralink", "xai", "grok", "cold gas thruster", "rocket thruster", "rocket thrusters",
    "frontier tech", "supercomputing", "autonomous vehicle", "autonomous driving",
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
    # Football / Soccer / Sports / Athletics / Gymnastics / Medals
    r"\b(manchester city|man city|premier league|champions league|football|soccer|fifa|uefa)\b",
    r"\b(la liga|serie a|bundesliga|world cup|olympics|olympic|nfl|nba|mlb|nhl|cricket|tennis|golf)\b",
    r"\b(tournament|referee|striker|goalkeeper|player|transfer fee|stadium|coach|ballon d'or|pinto)\b",
    r"\b(athletics|athlete|racing|f1|formula 1|grand prix|super bowl|swimming|relay)\b",
    r"\b(gymnastics|gymnast|gymnasts|gold medal|silver medal|bronze medal|medalist|medallists?|podium|championships?|world championship)\b",
    
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

# Strict exclusion filter for Regional, Domestic, and Local Retail Gold Jewelry Markets
# (e.g. India, Pakistan, Bangladesh retail gold in Rupees, MCX, per 10 grams, Tola, local Jewellers)
REGIONAL_RETAIL_GOLD_PATTERNS = [
    r"\b(rupee|rupees|rs\.?|\b\d+\s*(?:rs|rupees))\b",
    r"\b(per 10\s*grams?|per 10g|10\s*grams?|10g gold|in 10 grams?)\b",
    r"\b(22k|22-carat|24k gold rate|22k gold rate|gold rate today|gold price today in|gold rate in)\b",
    r"\b(tola|sovereign gold|jewellers?|jewellery|jewelry association|saraf|mcx gold|mcx)\b",
    r"\b(pakistan gold|india gold rate|indian gold price|delhi gold|mumbai gold|kolkata gold|chennai gold|lahore gold|karachi gold)\b",
]

# Trivial, Low-Impact, Routine Market Noise, Analyst Ratings, and Minor Tips Filter
TRIVIAL_AND_LOW_IMPACT_PATTERNS = [
    r"\b(price target|analyst rating|analyst upgrades|analyst downgrades|upgrades to buy|downgrades to hold)\b",
    r"\b(top pick|stocks to buy|stocks to watch|stocks to sell|best stock to buy)\b",
    r"\b(retire rich|retirement portfolio|dividend yield of \d|passive income|penny stock|penny stocks)\b",
    r"\b(earnings whisper|q[1-4] earnings preview|earnings call transcript|zacks rank|zacks investment)\b",
    r"\b(unusual volume|options activity|short squeeze|meme stock|day trading)\b",
    r"\b(how to invest|investing tips|beginner guide|cryptocurrency prediction 20\d\d)\b",
    r"\b(morning brief|podcast episode|listen now|webinar|q&a with|interview transcript)\b",
    r"\b(why .+ (?:fell|dropped|rose|jumped) today|here's why|is it time to buy)\b",
    r"\b(daily horoscope|lottery numbers|jackpot)\b",
    # Trivial altcoins, memecoins, presales, airdrops, and low-cap retail tokens (Pillar 8 strict standard)
    r"\b(bitway|memecoin|memecoins|meme coin|meme coins|shiba|shib|pepe|floki|dogecoin|bonk|wif|bome)\b",
    r"\b(airdrop|airdrops|token unlock|presale|ico|ido|meme token|altcoin rally|altcoin season)\b",
    # Vague op-eds, speculative opinion columns, and non-actionable political commentary
    r"\b(opinion\b|editorial\b|column\b|perspective\b|op-ed\b|commentary\b|viewpoint\b)\b",
    r"\b(analysts say|critics say|experts debate|could face|may face|uncertain future|remains unclear)\b",
    r"\b(what to know|five things to know|3 things to know|here's what|here is what)\b",
    # Minor fund shareholdings, 13F filings, and routine minor stock transactions
    r"\b(\d+[,.]?\d*\s*shares in|purchased shares in|acquires shares in|stake in|holdings in|sec filing|form 13f|institutional investors? buy|portfolio update|shares bought|buys \d+[,.]?\d*\s*shares)\b",
    # Local political party polls / elections / voter demographics
    r"\b(election gains|young voters|poll shows|poised for election|local election|party primary|parliamentary debate|local council|local politics)\b",
    # Speculative preview questions and routine chatter
    r"\b(what comes next|what to expect|ahead of the rba|ahead of the boe|ahead of the fed|ahead of the boj|what next for)\b",
    # Routine unannounced visits / meetings without policy announcements
    r"\b(unannounced visit as|ahead of meeting with|meets in unannounced)\b",
    # Isolated domestic crimes, mass shootings, church/funeral attacks, stabbings, robbery (Non-geopolitical)
    r"\b(church shooting|funeral shooting|mosque shooting|temple shooting|school shooting|mass shooting|nightclub shooting|supermarket shooting|bar shooting)\b",
    r"\b(stabbing|stabbings|murder-suicide|homicide investigation|robbery|gang clash|gang violence|drug cartel bust|petty crime|local gunman)\b",
    # Video games, gaming apps, satire games, entertainment culture (Pillar 8 strict rejection)
    r"\b(video game|videogame|satirical game|mobile game|indie game|game developer|cockroach party|gaming studio|esports)\b",
    # Political campaign publicity stunts, election campaign ads, AI campaign videos
    r"\b(campaign stunt|campaign ad|election billboard|parody video|viral video ad|campaign video)\b",
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
        "emergency cut", "surprise hike", "war escalates", "missile", "military attack", "airstrike", "drone strike", "invasion", "nuclear",
        "central bank reserves", "taiwan", "red sea crisis", "geopolitical shock", "strait of hormuz",
        "ai breakthrough", "tech disruption", "liquidity crisis", "market plunge", "gold surges",
        "flash crash", "sharp spike", "tariff hike", "sanctions", "bank failure", "default", "sovereign debt",
        "de-dollarization", "unprecedented move", "emergency meeting", "cyberattack",
        "kim jong un", "north korea", "state visit", "summit talks"
    ]

    URGENT_SIGNALS = [
        "breaking", "urgent", "surprise", "emergency", "rate cut", "rate hike",
        "fomc statement", "cpi rises", "cpi falls", "nfp surges", "nfp misses",
        "escalates", "missile", "war", "military attack", "airstrike", "drone attack", "sanctions", "china central bank",
        "powell", "warsh", "fed announces", "unprecedented", "crash", "surge", "plunge",
        "sharp drop", "rally", "spike", "plummets", "skyrockets", "tensions rise",
        "kim jong un", "north korea", "dprk", "xi jinping", "state visit", "summit"
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
    def is_high_importance(title: str, description: str = "") -> bool:
        """
        Strictly evaluates whether a news event is HIGH IMPORTANCE (ព័ត៌មានដែលសំខាន់ខ្លាំង).
        Only approves Tier-1 market catalysts, geopolitical security shocks, and major central bank/macro moves.
        """
        full_text = f"{title} {description}".lower()

        # Reject trivial patterns early
        for pat in TRIVIAL_AND_LOW_IMPACT_PATTERNS:
            if re.search(pat, full_text):
                return False

        # Reject sports and gossip
        for pat in SPORTS_AND_GOSSIP_PATTERNS:
            if re.search(pat, full_text):
                return False

        # Reject regional local retail gold jewelry markets (India, Pakistan, Rupees, 10 grams, MCX, jewellers)
        for pat in REGIONAL_RETAIL_GOLD_PATTERNS:
            if re.search(pat, full_text):
                return False

        # 1. Immediate Catalysts
        if _matches_any_keyword(full_text, GoldNewsFilter.IMMEDIATE_CATALYSTS):
            return True

        # 2. Urgent Market Signals
        if _matches_any_keyword(full_text, GoldNewsFilter.URGENT_SIGNALS):
            return True

        # 3. Macroeconomic & Central Bank Decisions & Bond Yields (Tier 1)
        macro_core = [
            "cpi", "core cpi", "inflation", "pce", "core pce", "non-farm", "nonfarm", "nfp",
            "gdp", "fomc", "federal reserve", "interest rate", "rate cut", "rate hike",
            "powell", "warsh", "kevin warsh", "ecb", "boj", "boe", "pboc", "bank of japan",
            "bank of england", "european central bank", "treasury yield", "treasury yields",
            "bond yield", "bond yields", "10-year yield", "2-year yield", "yield curve",
            "dollar index", "dxy", "us dollar", "greenback", "rate decision", "holds rates",
            "cuts rates", "hikes rates", "central bank buying", "central bank reserves",
            "unemployment rate", "recession", "debt ceiling", "tariff", "trade war", "sovereign debt"
        ]
        if _matches_any_keyword(full_text, macro_core):
            return True

        # 4. War, Geopolitical Conflict, Peace Talks & Security (Tier 1)
        geo_core = [
            "war", "invasion", "military strike", "missile", "airstrike", "air strike", "drone attack",
            "drone strike", "strait of hormuz", "red sea crisis", "naval blockade", "nuclear threat",
            "ceasefire", "peace deal", "peace talks", "envoy", "ambassador", "diplomatic",
            "sanctions imposed", "sanctions against", "sanctions lifted", "tensions escalate",
            "retaliatory strike", "military offensive", "border clash", "armed clash",
            "troops mobilized", "declares war", "martial law", "hostage", "detains", "detained",
            "freed", "humanitarian", "security council", "defense pact", "ballistic", "warship",
            "north korea", "dprk", "kim jong un", "kim jong-un", "pyongyang", "south korea",
            "state visit", "bilateral summit", "summit talks", "dandong"
        ]
        if _matches_any_keyword(full_text, geo_core):
            return True

        if re.search(r'\b(israel|iran|russia|ukraine|china|taiwan|us|u\.s\.|syria|lebanon|yemen|houthi|gaza|north korea|dprk|south korea|korea)\b', full_text) and re.search(r'\b(strike|attack|bomb|clash|warns|threat|escalat|deploy|intercept|drone|retaliat|freed|talks|crisis|conflict|visit|visits|arrived|arrives|summit|bridge|border|pact|alliance)\b', full_text):
            return True

        # 5. Gold & Precious Metals, Energy & Oil Shocks (Tier 1)
        energy_and_gold_core = [
            "gold", "xau", "bullion", "yellow metal", "gold price", "spot gold", "gold rally",
            "gold surges", "gold plunges", "gold hits", "all-time high", "record high",
            "central bank buying gold", "gold reserves", "silver", "precious metals", "mining",
            "opec", "opec+", "crude oil", "oil supply", "oil price", "oil prices", "brent", "wti",
            "crude", "energy crisis", "crude inventories", "lng export", "gas prices", "pipeline"
        ]
        if _matches_any_keyword(full_text, energy_and_gold_core):
            return True

        # 6. Financial Markets, Wall Street & Earnings (Tier 1)
        markets_core = [
            "wall street", "dow jones", "s&p 500", "nasdaq", "equities", "stock market",
            "market selloff", "stocks plunge", "stocks rally", "market rout", "market crash",
            "earnings beat", "earnings surprise", "ipo", "trillion market cap"
        ]
        if _matches_any_keyword(full_text, markets_core):
            return True

        # 7. Big Tech, AI, Frontier Innovation & Aerospace (Tier 1)
        tech_core = [
            "semiconductor export", "chip export controls", "chip ban", "big tech antitrust",
            "artificial intelligence breakthrough", "ai model launch", "data center investment",
            "starship launch", "roadster unveil", "optimus humanoid", "robotaxi launch",
            "cyberattack disrupts", "cloud outage", "billion investment", "blackwell", "deepseek",
            "asml", "tsmc", "earnings beat", "revenue surge", "tie-up", "partnership", "acquisition"
        ]
        if _matches_any_keyword(full_text, tech_core):
            return True

        if re.search(r'\b(nvidia|apple|tesla|openai|spacex|microsoft|google|anthropic|meta|amazon)\b', full_text) and re.search(r'\b(unveils|launches|invests|bans|regulatory|chips?|antitrust|record revenue|breakthrough|acquisition|earnings|stock jumps|stock surges|beats)\b', full_text):
            return True

        # 8. Major Digital Asset & Crypto Milestones (Tier 1)
        crypto_core = [
            "strategic bitcoin reserve", "spot bitcoin etf", "crypto regulation", "sec approves",
            "sec sues", "crypto crash", "bitcoin surges above", "bitcoin plunges below",
            "stablecoin law", "cbdc", "binance settlement", "crypto liquidation", "mainnet launch",
            "solana", "ethereum"
        ]
        if _matches_any_keyword(full_text, crypto_core):
            return True

        return False

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

        # Gate 0.1: Reject trivial low-impact, analyst ratings, routine earnings previews
        for pat in TRIVIAL_AND_LOW_IMPACT_PATTERNS:
            if re.search(pat, full_text):
                return False

        # Gate 0.2: Reject regional local retail gold jewelry markets (India, Pakistan, Rupees, 10 grams, MCX, jewellers)
        for pat in REGIONAL_RETAIL_GOLD_PATTERNS:
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
            "rial", "geopolitical", "safe haven", "safe-haven", "north korea", "dprk", "pyongyang",
            "kim jong un", "south korea", "seoul", "xi jinping", "state visit", "summit", "dandong",
            "icbm", "nuclear escalation", "bilateral"
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
    @staticmethod
    def get_news_clusters(text: str) -> list:
        """Returns ALL matching macro clusters for a given news story (multi-domain classification)."""
        t = text.lower()
        clusters = []
        # 1. US Jobs / Payrolls / Labor Market
        if any(k in t for k in ["non-farm", "nonfarm", "payroll", "payrolls", "unemployment", "job growth", "jobs report", "hiring", "labor market", "workforce", "ការងារ", "អត្រាគ្មានការងារ", "nfp"]) or ("job" in t and any(w in t for w in ["us", "fed", "report", "cool", "slow", "data", "cut", "rise", "fall", "jump", "stall"])):
            clusters.append("us_jobs")
        # 2. Inflation & CPI
        if any(k in t for k in ["cpi", "inflation", "pce", "producer price", "consumer price", "cost of living", "អតិផរណា"]):
            clusters.append("inflation")
        # 3. Fed & Central Bank Rates
        if any(k in t for k in ["fomc", "powell", "kevin warsh", "rate cut", "rate hike", "interest rate", "basis point", "federal reserve", "អត្រាការប្រាក់", "ធនាគារកណ្តាល"]) or ("fed " in t and any(w in t for w in ["rate", "policy", "pause", "hike", "cut"])):
            clusters.append("fed_rates")
        # 4. Energy & Crude Oil & Gas & Refineries
        if any(k in t for k in ["crude oil", "brent", "wti", "oil price", "oil drop", "oil rise", "diesel", "gasoline", "lng", "fuel", "opec", "refinery", "refineries", "oil infrastructure", "energy target", "energy infrastructure", "shadow fleet", "oil tanker", "tankers", "ប្រេងឆៅ", "ប្រេងកាត", "ថាមពល", "រោងចក្រចម្រាញ់ប្រេង"]):
            clusters.append("energy_oil")
        # 5. Technology & AI & Semiconductors
        if any(k in t for k in ["nvidia", "semiconductor", "chipmaker", "tsmc", "intel", "amd", "blackwell", "artificial intelligence", "data center", "datacenter", "បន្ទះឈីប", "បញ្ញាសិប្បនិម្មិត"]) or ("ai " in t and any(w in t for w in ["chip", "tech", "job", "model", "cloud", "server", "wall street"])):
            clusters.append("tech_ai")
        # 6. Crypto & Digital Assets
        if any(k in t for k in ["bitcoin", "btc", "ethereum", "crypto", "cryptocurrency", "stablecoin", "tether", "binance", "coinbase", "ប៊ីតខយ", "គ្រីបតូ"]):
            clusters.append("crypto_assets")
        # 7. Middle East & Yemen Geopolitics
        if any(k in t for k in ["gaza", "israel", "tel aviv", "lebanon", "beirut", "hezbollah", "houthi", "strait of hormuz", "red sea", "yemen", "yemeni", "sanaa", "bab al-mandab", "syria", "iraq", "iran", "tehran", "damascus", "saudi", "aramco", "riyadh", "west bank", "palestine", "palestinian", "ramallah", "settler", "settlers", "settlement", "settlements", "យេមែន", "យេម៉ែន", "ហូទី", "អ៊ីរ៉ង់", "អ៊ីស្រាអែល", "ហ្កាហ្សា", "លីបង់", "ច្រកសមុទ្រ", "អារ៉ាប៊ីសាអ៊ូឌីត", "ប៉ាឡេស្ទីន", "វេសប៊ែង", "ក្រុមអ្នកតាំងលំនៅ"]):
            clusters.append("middle_east")
        # 8. Russia & Ukraine
        if any(k in t for k in ["russia", "ukraine", "kyiv", "moscow", "kremlin", "zelensky", "putin", "រុស្ស៊ី", "អ៊ុយក្រែន", "ម៉ូស្គូ", "គៀវ"]):
            clusters.append("russia_ukraine")
        # 9. Tariffs & Trade Wars
        if any(k in t for k in ["tariff", "tariffs", "sanction", "sanctions", "trade war", "embargo", "ពន្ធគយ", "ទណ្ឌកម្ម", "សង្គ្រាមពាណិជ្ជកម្ម"]):
            clusters.append("tariffs_trade")
        # 10. Frontier Tech, Tesla & SpaceX Innovation
        if any(k in t for k in ["elon musk", "musk", "tesla", "spacex", "starship", "roadster", "optimus", "cybertruck", "robotaxi", "neuralink", "xai", "grok", "cold gas thruster", "rocket thruster", "falcon heavy", "thruster", "thrusters"]):
            clusters.append("frontier_tech")
        # 11. Korean Peninsula & East Asia Geopolitics
        if any(k in t for k in ["north korea", "dprk", "pyongyang", "kim jong un", "kim jong-un", "south korea", "seoul", "dandong", "កូរ៉េខាងជើង", "គីម ជុងអ៊ុន", "កូរ៉េខាងត្បូង"]):
            clusters.append("korea_east_asia")
        return clusters

    @staticmethod
    def get_news_cluster(text: str) -> str:
        """Returns primary macro cluster for backward compatibility."""
        clusters = GoldNewsFilter.get_news_clusters(text)
        return clusters[0] if clusters else ""

    @staticmethod
    def get_news_entities(text: str) -> list:
        """Extracts key individual leaders, officials, and top corporate entities for Entity Deduplication Shield."""
        t = text.lower()
        entities = []
        entity_map = {
            "kevin warsh": "kevin_warsh", "warsh": "kevin_warsh", "វ៉ាស": "kevin_warsh",
            "jerome powell": "jerome_powell", "powell": "jerome_powell", "ផៅវែល": "jerome_powell",
            "donald trump": "donald_trump", "trump": "donald_trump", "ដូណាល់ ត្រាំ": "donald_trump", "ត្រាំ": "donald_trump",
            "elon musk": "elon_musk", "musk": "elon_musk", "ម៉ាស": "elon_musk",
            "vladimir putin": "vladimir_putin", "putin": "vladimir_putin", "ពូទីន": "vladimir_putin",
            "volodymyr zelensky": "zelenskyy", "zelensky": "zelenskyy", "zelenskyy": "zelenskyy", "ហ្សេលេនស្គី": "zelenskyy",
            "benjamin netanyahu": "netanyahu", "netanyahu": "netanyahu", "ណេតាន់យ៉ាហ៊ូ": "netanyahu",
            "kim jong un": "kim_jong_un", "kim jong-un": "kim_jong_un", "kim jong": "kim_jong_un", "គីម ជុងអ៊ុន": "kim_jong_un",
            "xi jinping": "xi_jinping", "ស៊ី ជីនពីង": "xi_jinping",
            "scott bessent": "scott_bessent", "bessent": "scott_bessent", "បេសសិន": "scott_bessent",
            "christine lagarde": "lagarde", "lagarde": "lagarde", "ឡាហ្កាដ": "lagarde",
            "kazuo ueda": "kazuo_ueda", "ueda": "kazuo_ueda", "អ៊ូអេដា": "kazuo_ueda",
            "narendra modi": "modi", "modi": "modi", "ម៉ូឌី": "modi",
            "giorgia meloni": "meloni", "meloni": "meloni",
            "nvidia": "nvidia", "tsmc": "tsmc", "blackrock": "blackrock",
            "boeing": "boeing", "intel": "intel", "tesla": "tesla", "aramco": "aramco",
            "spacex": "spacex", "starship": "spacex", "roadster": "tesla"
        }
        for kw, ent in entity_map.items():
            if kw in t and ent not in entities:
                entities.append(ent)
        return entities

    @staticmethod
    def is_duplicate_or_similar(new_title: str, existing_titles: list, threshold: float = 0.35) -> bool:
        """
        Semantic Deduplication: Checks if the new news article is covering the EXACT same event
        as any article broadcasted recently across different RSS feeds (e.g. Reuters vs CNBC on same event).
        Strictly prevents repeating stories on the same topic.
        """
        import re

        def _stem(w: str) -> str:
            w = w.lower()
            synonyms = {
                "israeli": "israel", "british": "britain", "russian": "russia",
                "lebanese": "lebanon", "mexican": "mexico", "canadian": "canada",
                "ukrainian": "ukraine", "iranian": "iran", "chinese": "china",
                "japanese": "japan", "american": "america", "yemeni": "yemen",
                "saudi": "saudi",
                "attacks": "strike", "attack": "strike", "strikes": "strike", "bombing": "strike", "bombed": "strike", "hit": "strike", "targeted": "strike", "targeting": "strike",
                "refinery": "oil", "refineries": "oil", "petroleum": "oil", "crude": "oil", "fuel": "oil", "diesel": "oil", "gasoline": "oil", "tanker": "oil", "tankers": "oil",
                "semiconductor": "chip", "semiconductors": "chip", "chips": "chip", "wafer": "chip",
                "warns": "warn", "warning": "warn", "warnings": "warn", "threatens": "warn", "threat": "warn",
                "settlers": "settler", "settlement": "settler", "settlements": "settler",
                "convoys": "convoy", "delegations": "delegation", "diplomats": "delegation", "diplomat": "delegation",
            }
            if w in synonyms:
                return synonyms[w]
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

        KEY_ENTITIES = {
            "yemen", "houthi", "sanaa", "gaza", "hezbollah", "lebanon", "iran", "israel",
            "palestine", "palestinian", "cpi", "nfp", "fomc", "powell", "warsh", "kevin",
            "trump", "donald", "nvidia", "tsmc", "opec", "anthropic", "amodei",
            "spacex", "starlink", "apple", "tesla", "putin", "zelensky", "russia", "ukraine",
            "deepseek", "bitcoin", "tether", "binance", "brent", "hormuz", "oil", "strike", "saudi", "tariff", "dow",
            "settler", "settlers", "convoy", "delegation", "bolivia"
        }

        new_tokens = _tokenize(new_title)
        if not new_tokens:
            return False

        new_entities = new_tokens.intersection(KEY_ENTITIES)

        for past_title in existing_titles:
            past_tokens = _tokenize(past_title)
            if not past_tokens:
                continue

            intersection = new_tokens.intersection(past_tokens)
            union = new_tokens.union(past_tokens)
            similarity = len(intersection) / len(union) if union else 0.0
            min_len = min(len(new_tokens), len(past_tokens))
            overlap_ratio = len(intersection) / min_len if min_len else 0.0

            # 1. Strong Key Entity Overlap (e.g. both articles discuss 'yemen' or 'kevin warsh' or 'ukraine' + 'oil' / 'strike')
            past_entities = past_tokens.intersection(KEY_ENTITIES)
            shared_entities = new_entities.intersection(past_entities)
            if shared_entities and len(intersection) >= 2:
                return True

            # 2. General token overlap across news wires
            if similarity >= 0.35 or (overlap_ratio >= 0.40 and len(intersection) >= 3):
                return True

        return False

    @staticmethod
    def is_khmer_duplicate_or_similar(new_headline_km: str, existing_khmer_headlines: list) -> bool:
        """
        Direct Khmer Headline Deduplication: Checks if the new Khmer headline is repeating
        an event that was already broadcasted in Khmer within the cooldown window.
        """
        if not new_headline_km or not existing_khmer_headlines:
            return False

        import re
        KHMER_TOPIC_WORDS = [
            "យេមែន", "យេម៉ែន", "ហូទី", "អ៊ីរ៉ង់", "អ៊ីស្រាអែល", "ហ្កាហ្សា", "ប៉ាឡេស្ទីន", "វេសប៊ែង", "West Bank", "លីបង់", "រុស្ស៊ី",
            "អ៊ុយក្រែន", "ប្រេងឆៅ", "អតិផរណា", "ការងារ", "អត្រាការប្រាក់", "ពន្ធគយ", "ចិន", "តៃវ៉ាន់",
            "ត្រាំ", "ដូណាល់ ត្រាំ", "ផៅវែល", "វ៉ាស", "Anthropic", "អូលីវ", "បូលីវី", "ឧស្ម័នធម្មជាតិ",
            "ក្រុមអ្នកតាំងលំនៅ", "គណៈប្រតិភូ", "ក្បួនរថយន្ត", "សហភាពអឺរ៉ុប", "បារាំង", "ប៊ែលហ្ស៊ិក",
            "ជម្លោះ", "សង្គ្រាម", "មនុស្សធម៌", "កាត់ផ្តាច់", "ផ្ទុះ", "ប្រដាប់អាវុធ", "ទណ្ឌកម្ម",
            "កងទ័ព", "មីស៊ីល", "ដ្រូន", "វាយប្រហារ", "ធនាគារកណ្តាល", "ទុនបម្រុង", "បន្ទះឈីប",
            "ប៊ីតខយ", "គ្រីបតូ", "វិបត្តិ", "សម្ពាធ", "កើនឡើង", "ធ្លាក់ចុះ", "បាញ់ប្រហារ"
        ]

        # Specific distinct subjects where even 1 shared keyword indicates identical story
        HIGH_SPECIFICITY_KEYWORDS = {
            "ក្រុមអ្នកតាំងលំនៅ", "វេសប៊ែង", "west bank", "បូលីវី", "anthropic", "tsmc", "nvidia", "tether", "ប៊ែលហ្ស៊ិក"
        }

        new_kw = {k for k in KHMER_TOPIC_WORDS if k.lower() in new_headline_km.lower()}
        norm_new = re.sub(r'[\s\W_]+', '', new_headline_km).lower()

        for past_hl in existing_khmer_headlines:
            if not past_hl:
                continue

            past_kw = {k for k in KHMER_TOPIC_WORDS if k.lower() in past_hl.lower()}
            common_kw = new_kw.intersection(past_kw)

            # 1. High-specificity single keyword duplicate match
            if any(kw.lower() in {c.lower() for c in common_kw} for kw in HIGH_SPECIFICITY_KEYWORDS):
                return True

            # 2. Matches >= 2 topic keywords (e.g. យេមែន + ជម្លោះ or មនុស្សធម៌ + យេមែន)
            if len(common_kw) >= 2:
                return True

            # 2. Long identical substring match (>= 15 characters, e.g. "ជម្លោះប្រដាប់អាវុធនៅយេមែន")
            norm_past = re.sub(r'[\s\W_]+', '', past_hl).lower()
            if len(norm_new) >= 20 and len(norm_past) >= 20:
                for i in range(0, min(len(norm_new) - 15, 45), 5):
                    if norm_new[i:i+15] in norm_past:
                        return True

        return False
