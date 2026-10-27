import os
import re
import io
import json
import hashlib
import logging
import urllib.parse
import urllib.request
import requests
from PIL import Image, ImageOps

logger = logging.getLogger("StoryImageBuilder")

class StoryImageBuilder:
    """
    Synthesizes and selects authentic, story-accurate images for news broadcasts:
    1. Dual-Leader Split Image (e.g. Meloni + Trump, Trump + Putin, Xi + Trump).
    2. Dual-Country Flag Split Image (e.g. India + Canada, US + China, US + Taiwan).
    3. Single Leader Official Portrait (Trump, Powell, Warsh, Musk, Putin, Xi, Meloni, etc.).
    4. Direct Genuine Article Photo (verified publisher og:image/enclosure, strictly zero logos).
    5. Macro Topic Authentic Ultra-HD Photo (Gold, Oil, Chips, Crypto, Fed, Wall Street, Naval).
    6. Single Country High-Res Flag / Visual.
    """

    LEADERS_DIR = "assets/speakers"
    FLAGS_DIR = "assets/flags"
    BRANDS_DIR = "assets/brands"
    TOPICS_DIR = "assets/topics"

    TOPIC_PATTERNS = [
        ("ai_data_center", r"\b(data center|data centers|cooling|liquid cooling|wastewater|supercomputer|compute|gpu cluster|ai infrastructure)\b|មជ្ឈមណ្ឌលទិន្នន័យ|កម្ដៅម៉ាស៊ីនមេ|ម៉ាស៊ីនមេ"),
        ("gold_bullion", r"\b(gold|gold price|bullion|xauusd|xau|precious metals)\b|(?<![\u1780-\u17D3])មាស(?![\u1780-\u17D3])|ហាងឆេងមាស|តម្លៃមាស|ដុំមាស"),
        ("crude_oil", r"\b(oil|crude|brent|wti|opec|refinery|refineries|petroleum|fuel|gasoline|natural gas|lng|permian basin)\b|ប្រេង|ប្រេងកាត|ប្រេងឆៅ|ឧស្ម័នធម្មជាតិ"),
        ("federal_reserve", r"\b(federal reserve|fed|fomc|interest rate|rate hike|rate cut|monetary policy)\b|ធនាគារកណ្តាលអាមេរិក|អត្រាការប្រាក់"),
        ("wall_street", r"\b(wall street|dow jones|s&p 500|nasdaq|nyse|stock market|equities|stocks rally|stocks plunge)\b|ទីផ្សារភាគហ៊ុន|សន្ទស្សន៍"),
        ("bitcoin_crypto", r"\b(bitcoin|btc|cryptocurrency|crypto|ethereum|eth|stablecoin|tether|usdt)\b|កាក់ឌីជីថល|ប៊ីតខញ"),
        ("geopolitics_naval", r"\b(naval|warship|destroyer|aircraft carrier|strait of hormuz|red sea|bab al-mandab)\b|កងទ័ពជើងទឹក|នាវាចម្បាំង|ច្រកសមុទ្រ"),
    ]

    BRAND_PATTERNS = [
        ("spacex", r"\b(spacex|starlink)\b|ស្ប៉េសអ៊ិច|ស្តាលីង"),
        ("tesla", r"\b(tesla)\b|ថេសឡា"),
        ("nvidia", r"\b(nvidia)\b|អិនវីឌា"),
        ("apple", r"\b(apple|iphone)\b|អាប់ផល"),
        ("openai", r"\b(openai|chatgpt)\b|អូផឹនអេអាយ"),
        ("anthropic", r"\b(anthropic|claude)\b|អានស្រូភិក|អែនស្រូភិក|ក្លូដ"),
        ("xai", r"\b(xai|grok)\b|អ៊ិចអេអាយ|ហ្គ្រក"),
        ("microsoft", r"\b(microsoft)\b|ម៉ៃក្រូសូហ្វ"),
        ("google", r"\b(google|alphabet)\b|ហ្គូហ្គល"),
        ("intel", r"\b(intel)\b|អ៊ីនធែល"),
        ("amd", r"\b(amd)\b|អេអឹមឌី"),
        ("amazon", r"\b(amazon|aws)\b|អាម៉ាហ្សូន"),
        ("blackrock", r"\b(blackrock)\b|ប៊្លែករ៉ក់"),
    ]

    LEADER_PATTERNS = [
        ("giorgia_meloni", r"\b(meloni|giorgia meloni)\b|ម៉េឡូនី|មេឡូនី"),
        ("melania_trump", r"\b(melania|melania trump)\b|មេឡានី|មេឡានា|លោកស្រី\s*ត្រាំ"),
        ("donald_trump", r"(?<!melania\s)(?<!melania\b)(?<!melania\W)\b(?:donald\s+trump|president\s+trump|mr\.\s*trump|trump)\b(?!\s*tower|\s*organization)|(?<!លោកស្រី\s)(?<!លោកស្រី)(?:ដូណាល់\s*ត្រាំ|ប្រធានាធិបតី\s*ត្រាំ|លោក\s*ត្រាំ|\bត្រាំ\b)"),
        ("vladimir_putin", r"\b(putin|vladimir putin)\b|ពូទីន|វ្ល៉ាឌីមៀ ពូទីន"),
        ("xi_jinping", r"\b(xi jinping|president xi)\b|ស៊ី ជីនពីង"),
        ("jerome_powell", r"\b(powell|jerome powell)\b|ផៅវែល|ផូវែល"),
        ("kevin_warsh", r"\b(warsh|kevin warsh)\b|វ៉ាស|ខេវិន វ៉ាស"),
        ("elon_musk", r"\b(musk|elon musk)\b|ម៉ាស|អេឡុន ម៉ាស"),
        ("dario_amodei", r"\b(dario amodei|amodei)\b|ដារីយ៉ូ អាម៉ូដី|អាម៉ូដី|នាយកប្រតិបត្តិ\s*(?:របស់\s*)?anthropic|ceo\s*(?:of\s*)?anthropic"),
        ("benjamin_netanyahu", r"\b(netanyahu|benjamin netanyahu)\b|ណេតាន់យ៉ាហ៊ូ"),
        ("volodymyr_zelenskyy", r"\b(zelenskyy|zelensky|volodymyr zelenskyy)\b|ហ្សេលេនស្គី"),
        ("emmanuel_macron", r"\b(macron|emmanuel macron)\b|ម៉ាក្រុង"),
        ("keir_starmer", r"\b(starmer|keir starmer)\b|ស្តាម័រ"),
        ("christine_lagarde", r"\b(lagarde|christine lagarde)\b|ឡាការដ៍"),
        ("kazuo_ueda", r"\b(ueda|kazuo ueda)\b|អ៊ូអេដា"),
        ("narendra_modi", r"\b(modi|narendra modi)\b|ម៉ូឌី"),
        ("abdel_fattah_elsisi", r"\b(sisi|el-sisi|abdel fattah)\b|ស៊ីស៊ី|អាប់ដែល ហ្វាតា"),
        ("jensen_huang", r"\b(jensen huang|jensen|huang)\b|ជេនសិន|ហួង|នាយកប្រតិបត្តិ\s*(?:របស់\s*)?nvidia|ceo\s*(?:of\s*)?nvidia"),
        ("tim_cook", r"\b(tim cook)\b|ធីម ឃុក|ធីម គុក|នាយកប្រតិបត្តិ\s*(?:របស់\s*)?apple|ceo\s*(?:of\s*)?apple"),
        ("sam_altman", r"\b(sam altman)\b|សាំ អាល់តូម៉ាន់|សេម អាល់តូម៉ាន់|នាយកប្រតិបត្តិ\s*(?:របស់\s*)?openai|ceo\s*(?:of\s*)?openai"),
        ("satya_nadella", r"\b(satya nadella)\b|សាត្យា ណាឌែលឡា|នាយកប្រតិបត្តិ\s*(?:របស់\s*)?microsoft|ceo\s*(?:of\s*)?microsoft"),
        ("ali_khamenei", r"\b(khamenei|ayatollah)\b|ខាមេណី|ខាមេនី|មេដឹកនាំកំពូលអ៊ីរ៉ង់"),
        ("masoud_pezeshkian", r"\b(pezeshkian)\b|ពេហ្សេសគីយ៉ាន|ប្រធានាធិបតីអ៊ីរ៉ង់"),
        ("kim_jong_un", r"\b(kim jong un|kim jong-un|kim jong)\b|គីម ជុងអ៊ុន|គីម ជុង-អ៊ុន"),
        ("mark_zuckerberg", r"\b(mark zuckerberg|zuckerberg)\b|ម៉ាក ហ្សាក់កឺប៊ឺក|ម៉ាក ហ្ស៊ូកឺបឺក|នាយកប្រតិបត្តិ\s*(?:របស់\s*)?meta|ceo\s*(?:of\s*)?meta"),
    ]

    COUNTRY_PRESIDENTS = {
        "us": ["donald_trump"],
        "ru": ["vladimir_putin"],
        "ua": ["volodymyr_zelenskyy"],
        "cn": ["xi_jinping"],
        "il": ["benjamin_netanyahu"],
        "ir": ["ali_khamenei", "masoud_pezeshkian"],
        "kp": ["kim_jong_un"],
        "fr": ["emmanuel_macron"],
        "gb": ["keir_starmer"],
        "it": ["giorgia_meloni"],
        "in": ["narendra_modi"],
        "eg": ["abdel_fattah_elsisi"],
    }


    COUNTRY_PATTERNS = [
        ("us", r"\b(u\.s\.|u\.s|usa|united states|america|american|wall street)\b|អាមេរិក|សហរដ្ឋអាមេរិក"),
        ("ca", r"\b(canada|canadian)\b|កាណាដា"),
        ("in", r"\b(india|indian)\b|ឥណ្ឌា"),
        ("cn", r"\b(china|chinese|beijing)\b|ចិន"),
        ("ru", r"\b(russia|russian|moscow)\b|រុស្ស៊ី|រុស្សី"),
        ("it", r"\b(italy|italian|rome)\b|អ៊ីតាលី"),
        ("gb", r"\b(uk|britain|british|england|london)\b|អង់គ្លេស|ចក្រភពអង់គ្លេស"),
        ("jp", r"\b(japan|japanese|tokyo|yen)\b|ជប៉ុន"),
        ("de", r"\b(germany|german|berlin)\b|អាល្លឺម៉ង់"),
        ("fr", r"\b(france|french|paris)\b|បារាំង"),
        ("il", r"\b(israel|israeli|tel aviv)\b|អ៊ីស្រាអែល"),
        ("ir", r"\b(iran|iranian|tehran)\b|អ៊ីរ៉ង់|អ៊ីរ៉ាន"),
        ("ua", r"\b(ukraine|ukrainian|kyiv)\b|អ៊ុយក្រែន"),
        ("tw", r"\b(taiwan|taiwanese|taipei)\b|តៃវ៉ាន់"),
        ("kp", r"\b(north korea|dprk|pyongyang|kim jong)\b|កូរ៉េខាងជើង"),
        ("kr", r"\b(south korea|seoul)\b|(?<!north\s)(?<!dprk\s)\bkorean?\b|កូរ៉េ(?!\s*ខាងជើង)"),
        ("sg", r"\b(singapore|singaporean)\b|សិង្ហបុរី"),
        ("au", r"\b(australia|australian|sydney)\b|អូស្ត្រាលី"),
        ("ch", r"\b(switzerland|swiss|zurich)\b|ស្វីស"),
        ("sa", r"\b(saudi|saudi arabia|riyadh)\b|អារ៉ាប៊ីសាអ៊ូឌីត"),
        ("ae", r"\b(uae|emirates|dubai|abu dhabi)\b|អេមីរ៉ាត|ឌូបៃ"),
        ("tr", r"\b(turkey|turkish|turkiye|ankara)\b|តួកគី"),
        ("br", r"\b(brazil|brazilian)\b|ប្រេស៊ីល"),
        ("vn", r"\b(vietnam|vietnamese|hanoi)\b|វៀតណាម"),
        ("mx", r"\b(mexico|mexican)\b|ម៉ិកស៊ិក"),
        ("id", r"\b(indonesia|indonesian|jakarta)\b|ឥណ្ឌូនេស៊ី"),
        ("qa", r"\b(qatar|doha)\b|(?:ប្រទេស|រដ្ឋ)?\s*កាតា(?![លក\u1780-\u17D3])"),
        ("eg", r"\b(egypt|egyptian|cairo)\b|អេហ្ស៊ីប"),
        ("ps", r"\b(palestine|palestinian|west bank|ramallah|gaza)\b|ប៉ាឡេស្ទីន|វេសប៊ែង|ហ្កាហ្សា"),
    ]

    IMAGE_COOLDOWN_SECONDS = 2592000.0  # 30 days strict cooldown for ANY visual asset (Strict Zero Repetition)
    _RECENT_USED_ASSETS = {}

    @classmethod
    def is_image_visually_duplicate(cls, img_bytes: bytes) -> bool:
        """Checks if generated or fetched image bytes match any channel broadcast within 30 days."""
        if not img_bytes:
            return False
        try:
            import database
            dh = database.calculate_image_dhash(img_bytes)
            if dh and database.is_image_dhash_duplicate(dh, max_age_seconds=2592000.0, max_hamming_dist=6):
                return True
        except Exception:
            pass
        return False

    @classmethod
    def is_asset_on_cooldown(cls, asset_key: str) -> bool:
        """Checks if a static visual asset was already used in recent broadcasts."""
        import time
        now = time.time()
        last_mem = cls._RECENT_USED_ASSETS.get(asset_key, 0)
        if (now - last_mem) < cls.IMAGE_COOLDOWN_SECONDS:
            return True
        try:
            import database
            db_ts = float(database.get_state(f"img_used_ts_{asset_key}") or "0")
            if (now - db_ts) < cls.IMAGE_COOLDOWN_SECONDS:
                return True
        except Exception:
            pass
        return False

    @classmethod
    def record_asset_used(cls, asset_key: str):
        """Records an asset as used both in memory and persistently in SQLite database."""
        import time
        now = time.time()
        cls._RECENT_USED_ASSETS[asset_key] = now
        try:
            import database
            database.set_state(f"img_used_ts_{asset_key}", str(now))
        except Exception:
            pass

    _FILE_DHASH_CACHE = {}

    @classmethod
    def _get_file_dhash(cls, file_path: str) -> str:
        """Returns cached perceptual dHash for static gallery file with zero disk re-reads."""
        if file_path in cls._FILE_DHASH_CACHE:
            return cls._FILE_DHASH_CACHE[file_path]
        try:
            import database
            with open(file_path, "rb") as f:
                dh = database.calculate_image_dhash(f.read())
            cls._FILE_DHASH_CACHE[file_path] = dh
            return dh
        except Exception:
            return ""

    @classmethod
    def get_available_leader_photo(cls, leader_key: str) -> str:
        """
        Dynamically finds the best, non-repeating leader photo from the gallery.
        If leader has multiple photos (e.g. elon_musk.jpg, elon_musk_2.jpg, ...),
        rotates and selects the least-recently-used one that is NOT on 24-hour cooldown!
        """
        import glob
        pattern = os.path.join(cls.LEADERS_DIR, f"{leader_key}*.jpg")
        candidates = glob.glob(pattern)
        if not candidates:
            return ""

        candidates.sort()

        # Check each photo candidate against individual cooldown and perceptual dHash
        for c in candidates:
            c_name = os.path.basename(c)
            if cls.is_asset_on_cooldown(f"photo_{c_name}"):
                continue
            try:
                import database
                c_hash = cls._get_file_dhash(c)
                if c_hash and database.is_image_dhash_duplicate(c_hash, max_age_seconds=2592000.0, max_hamming_dist=6):
                    continue
            except Exception:
                pass
            return c

        logger.info(f"[StoryImageBuilder] All {len(candidates)} photo variants of '{leader_key}' are currently on 30-day cooldown.")
        return ""

    @classmethod
    def get_available_president_photo_for_country(cls, country_code: str) -> tuple:
        """Finds the best available non-cooldown leader photo for a sovereign country."""
        leaders = cls.COUNTRY_PRESIDENTS.get(country_code, [])
        if isinstance(leaders, str):
            leaders = [leaders]
        for l_slug in leaders:
            p_path = cls.get_available_leader_photo(l_slug)
            if p_path:
                return l_slug, p_path
        return "", ""

    @classmethod
    def get_available_topic_photo(cls, topic_key: str) -> str:
        """
        Dynamically finds the best, non-repeating topic photo from the gallery.
        Rotates through variants (e.g. gold_bullion.jpg, gold_bullion_2.jpg)
        and selects one that is NOT on 30-day cooldown.
        """
        import glob
        pattern = os.path.join(cls.TOPICS_DIR, f"{topic_key}*.jpg")
        candidates = glob.glob(pattern)
        if not candidates:
            return ""

        candidates.sort()
        for c in candidates:
            c_name = os.path.basename(c)
            if cls.is_asset_on_cooldown(f"topic_{c_name}"):
                continue
            try:
                import database
                c_hash = cls._get_file_dhash(c)
                if c_hash and database.is_image_dhash_duplicate(c_hash, max_age_seconds=2592000.0, max_hamming_dist=6):
                    continue
            except Exception:
                pass
            return c
        return ""


    @classmethod
    def get_image_for_news(cls, item: dict, analysis: dict = None, default_fetcher=None) -> bytes:
        """
        Main entry point to determine and generate the most accurate image for the news item.
        Strictly enforces Iron Law #1: Zero image repetition across 30 days!
        If candidate matches any broadcast within 30 days, returns None (forcing MODE B Clean VIP Text Mode).
        """
        candidate = cls._build_image_candidate(item, analysis=analysis, default_fetcher=default_fetcher)
        if not candidate:
            return None
        
        # Universal 30-day Perceptual Duplicate Shield
        if cls.is_image_visually_duplicate(candidate):
            logger.warning("[StoryImageBuilder] Final candidate image matches 30-day channel dHash history. Strictly rejecting candidate -> Fallback to MODE B (Clean VIP Text Mode).")
            return None
            
        return candidate

    @classmethod
    def _build_image_candidate(cls, item: dict, analysis: dict = None, default_fetcher=None) -> bytes:
        """
        Synthesizes or selects the best authentic visual candidate for the news story.
        """
        import hashlib
        title = item.get("title", "")
        desc = item.get("description", "")
        source_name = item.get("source", "")
        headline_km = ""
        key_event = ""
        if isinstance(analysis, dict):
            headline_km = analysis.get("headline_km", "")
            key_event = analysis.get("key_event", "")

        # Strict publisher source stripping to avoid false country matching (e.g. "China Military Online", "Times of India", "France 24")
        clean_desc = desc
        if source_name:
            clean_desc = re.sub(re.escape(source_name), "", clean_desc, flags=re.IGNORECASE)
        # Strip common news agencies from country matching
        news_agencies = [
            r"\bfrance\s*24\b", r"\bfrance24\b", r"\bafp\b", r"\bdeutsche\s*welle\b", r"\bdw\b",
            r"\bchina military online\b", r"\btimes of india\b", r"\bal jazeera\b",
            r"\beuromaidan press\b", r"\bsouth china morning post\b", r"\bkyodo news\b",
            r"\bxinhua\b", r"\btass\b", r"\bsputnik\b", r"\bbbc\b", r"\bcnn\b", r"\bcnbc\b",
            r"\breuters\b", r"\bbloomberg\b", r"\bseeking\s*alpha\b", r"\bthe\s*hill\b",
            r"\bmarketwatch\b", r"\bfinancial\s*times\b", r"\bwsj\b", r"\bwall\s*street\s*journal\b"
        ]
        for ag in news_agencies:
            clean_desc = re.sub(ag, "", clean_desc, flags=re.IGNORECASE)

        comb_text = f"{title} {clean_desc} {headline_km} {key_event}".lower()
        if source_name:
            comb_text = re.sub(re.escape(source_name.lower()), "", comb_text)
        for ag in news_agencies:
            comb_text = re.sub(ag, "", comb_text, flags=re.IGNORECASE)

        headline_text = f"{headline_km} {title}".lower()
        if source_name:
            headline_text = re.sub(re.escape(source_name.lower()), "", headline_text)

        # Step 1: Detect Leaders involved (Rotational multi-variant gallery with per-photo cooldown)
        headline_leaders = []
        for leader_key, pat in cls.LEADER_PATTERNS:
            if re.search(pat, headline_text, re.IGNORECASE):
                img_path = cls.get_available_leader_photo(leader_key)
                if img_path and os.path.exists(img_path):
                    m_km = re.search(pat, headline_km, re.IGNORECASE) if headline_km else None
                    m_head = re.search(pat, headline_text, re.IGNORECASE)
                    pos = m_km.start() if m_km else (m_head.start() if m_head else 99999)
                    headline_leaders.append((leader_key, img_path, pos, bool(m_km)))

        headline_leaders.sort(key=lambda x: x[2])

        # Step 1: Direct Genuine Article Image from Publisher (Fresh, Authentic, Non-Repetitive)
        # Prioritize live press photos from Reuters, Bloomberg, etc., so readers always see fresh visuals and never get bored!
        if default_fetcher:
            try:
                direct_photo = default_fetcher(item)
                if direct_photo:
                    # Quality Gate 1: Byte size check (Must be >= 15KB, reject micro-images/pixels)
                    if len(direct_photo) < 15000:
                        logger.warning(f"[StoryImageBuilder] Direct photo too small ({len(direct_photo)} bytes). Rejecting.")
                        direct_photo = None
                    else:
                        # Quality Gate 2: Dimension & Aspect Ratio verification
                        try:
                            with Image.open(io.BytesIO(direct_photo)) as test_im:
                                w, h = test_im.size
                                aspect = w / max(h, 1)
                                if w < 400 or h < 250:
                                    logger.warning(f"[StoryImageBuilder] Direct photo resolution too low ({w}x{h} < 400x250). Rejecting.")
                                    direct_photo = None
                                elif aspect < 0.5 or aspect > 2.8:
                                    logger.warning(f"[StoryImageBuilder] Direct photo aspect ratio abnormal ({aspect:.2f}). Rejecting.")
                                    direct_photo = None
                        except Exception as e:
                            logger.warning(f"[StoryImageBuilder] Direct photo unreadable or corrupted: {e}. Rejecting.")
                            direct_photo = None

                if direct_photo:
                    try:
                        import database
                        dh = database.calculate_image_dhash(direct_photo)
                        if dh and database.is_image_dhash_duplicate(dh, max_age_seconds=2592000.0, max_hamming_dist=6):
                            logger.warning(f"[StoryImageBuilder] Direct publisher photo matches 30-day channel hash ({dh}). Skipping candidate.")
                            direct_photo = None
                    except Exception:
                        pass
                if direct_photo:
                    direct_hash = hashlib.md5(direct_photo[:1000]).hexdigest()
                    if not cls.is_asset_on_cooldown(f"direct_{direct_hash}"):
                        enhanced = cls.enhance_image_for_vip(direct_photo)
                        if not cls.is_image_visually_duplicate(enhanced):
                            cls.record_asset_used(f"direct_{direct_hash}")
                            logger.info(f"[StoryImageBuilder] Using verified direct publisher article photo (enhanced for VIP).")
                            return enhanced
                        else:
                            logger.warning(f"[StoryImageBuilder] Direct publisher photo is visually duplicate in 30-day channel history. Skipping.")
            except Exception as e:
                logger.debug(f"[StoryImageBuilder] Direct fetcher exception: {e}")

        # Step 2: Market & Macro Topic Guard (Financial/Commodity news should NEVER show politician portraits)
        is_market_index = bool(re.search(r"\b(dow jones|s&p 500|s&p|nasdaq|wall street|stock market|equities|stocks rally|stocks plunge)\b|ទីផ្សារភាគហ៊ុន|សន្ទស្សន៍", headline_text, re.IGNORECASE))
        if is_market_index:
            headline_leaders.clear()  # Strictly prevent politician portraits on stock/index news

        # Step 3: Dual-Leader Split Image Rule: ONLY allowed if BOTH leaders are prominently featured in the HEADLINE!
        if len(headline_leaders) >= 2:
            l1, path1, _, km1 = headline_leaders[0]
            l2, path2, _, km2 = headline_leaders[1]
            if not headline_km or (km1 and km2):
                p1_name = os.path.basename(path1)
                p2_name = os.path.basename(path2)
                if not cls.is_asset_on_cooldown(f"photo_{p1_name}") and not cls.is_asset_on_cooldown(f"photo_{p2_name}"):
                    logger.info(f"[StoryImageBuilder] Synthesizing Dual-Leader Split Image from headline: {p1_name} + {p2_name}")
                    split_bytes = cls.create_split_image(path1, path2)
                    if split_bytes:
                        cls.record_asset_used(f"photo_{p1_name}")
                        cls.record_asset_used(f"photo_{p2_name}")
                        return split_bytes
                else:
                    logger.info(f"[StoryImageBuilder] Dual leaders '{p1_name}' or '{p2_name}' on 4h cooldown. Skipping split image.")

        # Step 4: CEO + Product Dual Split Image Standard (USER MANDATORY DIRECTIVE)
        # When a CEO/Leader and their product/vehicle are featured (e.g. Elon Musk + Roadster/Optimus/Starship),
        # ALWAYS synthesize a clean 50/50 Dual Split Image: Left = CEO, Right = Product/Innovation!
        # STRICT ZERO REPETITION: Enforce 4-hour cooldown on both Leader photo and Product visual!
        PRODUCT_PATTERNS = [
            ("tesla_roadster_spacex", r"\b(roadster|spacex thruster|cold gas thruster|rocket thruster)\b|រ៉ូតស្ទ័រ"),
            ("cybertruck", r"\b(cybertruck)\b|ស៊ីបឺត្រាក់"),
            ("optimus", r"\b(optimus|tesla bot)\b|អុបទិមូស"),
            ("starship", r"\b(starship|super heavy)\b|ស្តាស៊ីប"),
            ("iphone", r"\b(iphone|vision pro)\b|អាយហ្វូន"),
            ("blackwell", r"\b(blackwell|b200|gb200|h100)\b"),
        ]
        if len(headline_leaders) >= 1:
            for prod_key, pat in PRODUCT_PATTERNS:
                if re.search(pat, comb_text, re.IGNORECASE):
                    prod_path = os.path.join(cls.BRANDS_DIR, f"{prod_key}.jpg")
                    if not os.path.exists(prod_path):
                        prod_path = os.path.join(cls.BRANDS_DIR, f"{prod_key}.png")
                    if os.path.exists(prod_path):
                        l1, path1, _, _ = headline_leaders[0]
                        p1_name = os.path.basename(path1)
                        if not cls.is_asset_on_cooldown(f"photo_{p1_name}") and not cls.is_asset_on_cooldown(f"prod_{prod_key}"):
                            logger.info(f"[StoryImageBuilder] Synthesizing CEO + Product Dual Split Image: {p1_name} + {prod_key}")
                            split_bytes = cls.create_split_image(path1, prod_path)
                            if split_bytes:
                                cls.record_asset_used(f"photo_{p1_name}")
                                cls.record_asset_used(f"prod_{prod_key}")
                                return split_bytes
                        else:
                            logger.info(f"[StoryImageBuilder] CEO '{p1_name}' or Product '{prod_key}' on 4h cooldown. Skipping to preserve visual diversity.")

        # Step 4.2: Detect Brands / Tech Giants involved
        detected_brands = []
        for brand_key, pat in cls.BRAND_PATTERNS:
            if re.search(pat, comb_text, re.IGNORECASE):
                b_path = os.path.join(cls.BRANDS_DIR, f"{brand_key}_dark.jpg")
                if not os.path.exists(b_path):
                    b_path = os.path.join(cls.BRANDS_DIR, f"{brand_key}.png")
                if os.path.exists(b_path):
                    detected_brands.append((brand_key, b_path))

        # Detect Target Countries involved
        detected_countries = []
        for c_code, pat in cls.COUNTRY_PATTERNS:
            m = re.search(pat, comb_text, re.IGNORECASE)
            if not m and c_code == "us":
                if re.search(r'\b(US|USA)\b', f"{title} {clean_desc}"):
                    m = True
            if m:
                flag_path = os.path.join(cls.FLAGS_DIR, f"{c_code}.png")
                if os.path.exists(flag_path):
                    m_head = re.search(pat, headline_text, re.IGNORECASE)
                    if not m_head and c_code == "us" and re.search(r'\b(US|USA)\b', title):
                        m_head = True
                    head_pos = m_head.start() if (m_head and hasattr(m_head, 'start')) else (0 if m_head else 99999)
                    detected_countries.append((c_code, flag_path, head_pos))

        detected_countries.sort(key=lambda x: x[2])

        # Step 4.1: Bilateral Conflict / State Clash Dual-President Split Image (USER MANDATORY DIRECTIVE: បើជាជម្លោះប្រទេសនិងប្រទេស ដាក់រូបប្រធានាធិបតីប្រទេសទាំងពីរ)
        # e.g. Russia vs Ukraine -> Left: Vladimir Putin, Right: Volodymyr Zelenskyy
        # e.g. US vs Iran -> Left: Donald Trump, Right: Ali Khamenei
        # e.g. Israel vs Iran -> Left: Benjamin Netanyahu, Right: Ali Khamenei
        # e.g. US vs China -> Left: Donald Trump, Right: Xi Jinping
        is_bilateral_conflict = bool(re.search(
            r"\b(war|conflict|clash|clashes|strike|strikes|attack|missile|missiles|drone|drones|tensions|retaliat|invad|invasion|sanction|sanctions|dispute|standoff|frontline|escalat|defense|military|peace talks|summit|bilateral|ceasefire|threat|warns|warning)\b|សង្គ្រាម|ជម្លោះ|វាយប្រហារ|មីស៊ីល|ដ្រូន|តានតឹង|ទណ្ឌកម្ម|យោធា|ការពារជាតិ|ការប្រឈមមុខ|បាញ់|ប្រយុទ្ធ|ជំនួប|កិច្ចប្រជុំ|ព្រមាន",
            comb_text, re.IGNORECASE
        ))

        # Case 1: Two countries detected in conflict / bilateral relations
        if len(detected_countries) >= 2 and is_bilateral_conflict:
            c1_code = detected_countries[0][0]
            c2_code = detected_countries[1][0]
            l1_slug, p1_path = cls.get_available_president_photo_for_country(c1_code)
            l2_slug, p2_path = cls.get_available_president_photo_for_country(c2_code)
            if l1_slug and l2_slug and l1_slug != l2_slug and p1_path and p2_path:
                p1_name = os.path.basename(p1_path)
                p2_name = os.path.basename(p2_path)
                split_key = f"pres_conflict_{l1_slug}_{l2_slug}"
                if not cls.is_asset_on_cooldown(f"photo_{p1_name}") and not cls.is_asset_on_cooldown(f"photo_{p2_name}") and not cls.is_asset_on_cooldown(split_key):
                    logger.info(f"[StoryImageBuilder] Synthesizing Bilateral Conflict Dual-President Split Image: {l1_slug} (Left) + {l2_slug} (Right)")
                    split_bytes = cls.create_split_image(p1_path, p2_path)
                    if split_bytes:
                        cls.record_asset_used(f"photo_{p1_name}")
                        cls.record_asset_used(f"photo_{p2_name}")
                        cls.record_asset_used(split_key)
                        return split_bytes

        # Case 2: One Leader and One Target Country in conflict (e.g. Trump warns Iran, Putin strikes Ukraine)
        if len(headline_leaders) == 1 and len(detected_countries) >= 1 and is_bilateral_conflict:
            l1, path1, _, _ = headline_leaders[0]
            opposing_countries = [c for c in detected_countries if l1 not in cls.COUNTRY_PRESIDENTS.get(c[0], [])]
            if opposing_countries:
                c_opp = opposing_countries[0][0]
                l2_slug, p2_path = cls.get_available_president_photo_for_country(c_opp)
                if l2_slug and l2_slug != l1 and p2_path:
                    p1_name = os.path.basename(path1)
                    p2_name = os.path.basename(p2_path)
                    split_key = f"leader_conflict_{l1}_{l2_slug}"
                    if not cls.is_asset_on_cooldown(f"photo_{p1_name}") and not cls.is_asset_on_cooldown(f"photo_{p2_name}") and not cls.is_asset_on_cooldown(split_key):
                        logger.info(f"[StoryImageBuilder] Synthesizing Leader vs Opposing President Conflict Split Image: {l1} (Left) + {l2_slug} (Right)")
                        split_bytes = cls.create_split_image(path1, p2_path)
                        if split_bytes:
                            cls.record_asset_used(f"photo_{p1_name}")
                            cls.record_asset_used(f"photo_{p2_name}")
                            cls.record_asset_used(split_key)
                            return split_bytes

        # Step 4.2: CEO/Leader + Target Country Dual Split Image (Story-Accurate Composite)
        # e.g. Jensen Huang + Germany flag, Elon Musk + China flag
        if len(headline_leaders) == 1 and len(detected_countries) >= 1:
            l1, path1, _, _ = headline_leaders[0]
            target_countries = [c for c in detected_countries if c[0] != "us"]
            c1, path_flag, _ = target_countries[0] if target_countries else detected_countries[0]
            p1_name = os.path.basename(path1)
            if not cls.is_asset_on_cooldown(f"photo_{p1_name}") and not cls.is_asset_on_cooldown(f"split_{l1}_{c1}"):
                logger.info(f"[StoryImageBuilder] Synthesizing CEO + Country Split Image: {p1_name} (Left) + {c1} Flag (Right)")
                split_bytes = cls.create_split_image(path1, path_flag)
                if split_bytes:
                    cls.record_asset_used(f"photo_{p1_name}")
                    cls.record_asset_used(f"split_{l1}_{c1}")
                    return split_bytes

        # Step 4.2.1: Company/Brand + Target Country Dual Split Image (Story-Accurate Composite)
        # e.g. NVIDIA Logo + Germany/Japan/India flag
        if len(headline_leaders) == 0 and len(detected_brands) >= 1 and len(detected_countries) >= 1:
            b1, path_brand = detected_brands[0]
            target_countries = [c for c in detected_countries if c[0] != "us"]
            c1, path_flag, _ = target_countries[0] if target_countries else detected_countries[0]
            b1_name = os.path.basename(path_brand)
            if not cls.is_asset_on_cooldown(f"brand_{b1}") and not cls.is_asset_on_cooldown(f"split_{b1}_{c1}"):
                logger.info(f"[StoryImageBuilder] Synthesizing Company + Country Split Image: {b1} (Left) + {c1} Flag (Right)")
                split_bytes = cls.create_split_image(path_brand, path_flag)
                if split_bytes:
                    cls.record_asset_used(f"brand_{b1}")
                    cls.record_asset_used(f"split_{b1}_{c1}")
                    return split_bytes

        # Step 4.3: Leader + Brand Split Image (Story-Accurate Composite)
        # e.g. Elon Musk + SpaceX / Tesla / Anthropic
        if len(headline_leaders) >= 1 and len(detected_brands) >= 1:
            l1, path1, _, _ = headline_leaders[0]
            b1, path2 = detected_brands[0]
            p1_name = os.path.basename(path1)
            b_pat = next((pat for slug, pat in cls.BRAND_PATTERNS if slug == b1), "")
            l_pat = next((pat for slug, pat in cls.LEADER_PATTERNS if slug == l1), "")
            b_m = re.search(b_pat, headline_text, re.IGNORECASE) if b_pat else None
            l_m = re.search(l_pat, headline_text, re.IGNORECASE) if l_pat else None
            b_pos = b_m.start() if b_m else 9999
            l_pos = l_m.start() if l_m else 9999
            left_img, right_img = (path2, path1) if b_pos < l_pos else (path1, path2)
            if not cls.is_asset_on_cooldown(f"photo_{p1_name}") and not cls.is_asset_on_cooldown(f"brand_{b1}"):
                logger.info(f"[StoryImageBuilder] Synthesizing Leader + Brand Split Image: {p1_name} + {b1}")
                split_bytes = cls.create_split_image(left_img, right_img)
                if split_bytes:
                    cls.record_asset_used(f"photo_{p1_name}")
                    cls.record_asset_used(f"brand_{b1}")
                    return split_bytes

        # Step 4.4: Dual-Brand Split Image (Story-Accurate Composite)
        # e.g. Anthropic + OpenAI, Apple + Tesla
        if len(headline_leaders) == 0 and len(detected_brands) >= 2:
            b1, path1 = detected_brands[0]
            b2, path2 = detected_brands[1]
            if not cls.is_asset_on_cooldown(f"brand_{b1}") and not cls.is_asset_on_cooldown(f"brand_{b2}"):
                logger.info(f"[StoryImageBuilder] Synthesizing Dual-Brand Split Image: {b1} + {b2}")
                split_bytes = cls.create_split_image(path1, path2)
                if split_bytes:
                    cls.record_asset_used(f"brand_{b1}")
                    cls.record_asset_used(f"brand_{b2}")
                    return split_bytes

        # Step 5: Single Leader Official Portrait
        # ONLY if the leader is the primary subject in headline and NOT just a casual mention in market/economic news
        if len(headline_leaders) >= 1 and not is_market_index:
            l1, path1, _, _ = headline_leaders[0]
            p1_name = os.path.basename(path1)
            if not cls.is_asset_on_cooldown(f"photo_{p1_name}"):
                try:
                    with open(path1, "rb") as f:
                        leader_cand = cls.enhance_image_for_vip(f.read())
                    if not cls.is_image_visually_duplicate(leader_cand):
                        cls.record_asset_used(f"photo_{p1_name}")
                        logger.info(f"[StoryImageBuilder] Using Single Leader Portrait with fresh variant: {p1_name}")
                        return leader_cand
                    else:
                        logger.warning(f"[StoryImageBuilder] Leader portrait variant '{p1_name}' is visually duplicate in 30-day channel history. Skipping.")
                except Exception as e:
                    logger.warning(f"[StoryImageBuilder] Failed reading single leader image {path1}: {e}")
            else:
                logger.info(f"[StoryImageBuilder] Leader portrait variant '{p1_name}' is on cooldown. Skipping to preserve visual variety.")

        # Step 6: Single Brand VIP Card (for major tech / market corporations)
        if len(headline_leaders) == 0 and len(detected_brands) >= 1:
            b_slug, b_path = detected_brands[0]
            if b_path and os.path.exists(b_path) and not cls.is_asset_on_cooldown(f"brand_{b_slug}"):
                try:
                    with open(b_path, "rb") as f:
                        brand_bytes = cls.enhance_image_for_vip(f.read())
                    if brand_bytes:
                        if not cls.is_image_visually_duplicate(brand_bytes):
                            cls.record_asset_used(f"brand_{b_slug}")
                            logger.info(f"[StoryImageBuilder] Using Single Brand VIP Card for {b_slug.upper()}")
                            return brand_bytes
                        else:
                            logger.warning(f"[StoryImageBuilder] Brand card '{b_slug}' is visually duplicate in 30-day channel history. Skipping.")
                except Exception as e:
                    logger.warning(f"[StoryImageBuilder] Failed reading brand image {b_path}: {e}")

        # Note: Static topic stock photos (bitcoin_crypto, wall_street, crude_oil, etc.)
        # and cheap flag cutouts are strictly BANNED to guarantee zero repetition and maximum visual quality.
        # Fall through to Live Editorial Photo Search or Clean MODE B!

        # Step 7.5: Live Real-Time Editorial Photo Search (Wikipedia Commons High-Res Press Wire)
        live_queries = []
        if headline_leaders:
            l_key = headline_leaders[0][0].replace("_", " ")
            if detected_brands:
                b_name = "Tesla car" if detected_brands[0][0] == "tesla" else detected_brands[0][0]
                live_queries.append(f"{l_key} {b_name}")
            live_queries.append(l_key)
        elif detected_brands:
            b_key = detected_brands[0][0]
            if b_key == "tesla":
                live_queries.append("Tesla, Inc.")
            elif b_key == "spacex":
                live_queries.append("SpaceX Starship")
            elif b_key == "nvidia":
                live_queries.append("Jensen Huang Nvidia")
            elif b_key == "apple":
                live_queries.append("Apple Inc.")
            else:
                live_queries.append(b_key)
        elif detected_countries:
            is_central_bank_story = bool(re.search(r'\b(rate|interest rate|monetary policy|central bank|inflation|cpi|yield|fomc|fed)\b|អត្រាការប្រាក់|ធនាគារកណ្តាល', comb_text, re.IGNORECASE))
            if is_central_bank_story:
                c_code = detected_countries[0][0]
                country_names = {
                    "us": "United States Federal Reserve",
                    "jp": "Bank of Japan",
                    "gb": "Bank of England",
                    "eu": "European Central Bank",
                    "de": "Deutsche Bundesbank",
                    "cn": "People's Bank of China"
                }
                if c_code in country_names:
                    live_queries.append(country_names[c_code])

        for q in live_queries:
            live_img = cls.fetch_live_editorial_photo(q, headline_text=headline_text)
            if live_img:
                try:
                    import database
                    h = database.calculate_image_dhash(live_img)
                    if h and database.is_image_dhash_duplicate(h, max_age_seconds=2592000.0, max_hamming_dist=6):
                        logger.warning(f"[StoryImageBuilder] Live photo for '{q}' matches 30-day channel hash ({h}). Skipping candidate.")
                        continue
                except Exception:
                    pass
                logger.info(f"[StoryImageBuilder] Successfully acquired verified editorial photo for query '{q}'.")
                return live_img

        # Step 8: Mode B Fallback Guarantee
        # If no authentic direct publisher photo or verified single leader/split asset exists, return None!
        # main.py will automatically broadcast in MODE B (Clean VIP Text Mode), preventing ANY image error or repetition 100%!
        logger.info("[StoryImageBuilder] No authentic direct photo or leader portrait. Falling back to MODE B (VIP Text Mode).")
        return None

    @classmethod
    def fetch_live_editorial_photo(cls, query: str, headline_text: str = "") -> bytes:
        """
        Dynamically fetches authentic, high-resolution editorial press images 
        from Wikimedia Commons / Wikipedia API in real time.
        Enforces strict validation: ZERO logos, ZERO seals/emblems, ZERO SVG renders, ZERO historical Nikola Tesla,
        and ZERO gold bars for non-gold stories.
        Enforces strict 4-hour cooldown per image hash to guarantee zero repetition!
        """
        if not query or len(query.strip()) < 3:
            return None
        try:
            encoded = urllib.parse.quote(query.strip())
            url = f"https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch={encoded}&gsrlimit=6&prop=pageimages&pithumbsize=1200&format=json"
            req = urllib.request.Request(url, headers={"User-Agent": "VIPNewsAssistant/2.0 (contact: info@telegram.org)"})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})

            FORBIDDEN_KEYWORDS = [
                ".svg", "svg.png", "seal", "coat_of_arms", "insignia", "emblem", "logo", "symbol",
                "roundel", "diagram", "chart", "graph", "map", "circa_", "nikola tesla",
                "great seal", "flag_of", "presidential seal", "badge"
            ]

            headline_is_gold = any(w in headline_text.lower() for w in ["gold", "xau", "xauusd", "bullion", "មាស"])

            for pid, pdata in pages.items():
                p_title = (pdata.get("title") or "").lower()
                thumb = pdata.get("thumbnail", {}).get("source")
                if not thumb:
                    continue

                thumb_low = thumb.lower()
                
                # 1. Reject logos, badges, government seals, emblems, diagrams, and historical Nikola Tesla
                if any(bad in thumb_low or bad in p_title for bad in FORBIDDEN_KEYWORDS):
                    continue

                # 2. Reject gold bars/coins on non-gold stories (IRON LAW #1)
                is_gold_visual = any(gw in thumb_low or gw in p_title for gw in ["gold", "bullion", "coin", "barren"])
                if is_gold_visual and not headline_is_gold:
                    continue

                if "wikipedia/commons" in thumb or "upload.wikimedia" in thumb:
                    img_req = urllib.request.Request(thumb, headers={"User-Agent": "VIPNewsAssistant/2.0"})
                    try:
                        with urllib.request.urlopen(img_req, timeout=3.5) as img_resp:
                            raw_bytes = img_resp.read()
                            if len(raw_bytes) >= 15000:
                                import database
                                dh = database.calculate_image_dhash(raw_bytes)
                                if dh and database.is_image_dhash_duplicate(dh, max_age_seconds=2592000.0, max_hamming_dist=6):
                                    logger.warning(f"[StoryImageBuilder] Live photo candidate for '{query}' matches 30-day channel dHash ({dh}). Skipping.")
                                    continue
                                img_hash = hashlib.md5(raw_bytes[:2000]).hexdigest()
                                if not cls.is_asset_on_cooldown(f"live_{img_hash}"):
                                    with Image.open(io.BytesIO(raw_bytes)) as im:
                                        w, h = im.size
                                        if w >= 400 and h >= 300:
                                            enhanced = cls.enhance_image_for_vip(raw_bytes)
                                            if cls.is_image_visually_duplicate(enhanced):
                                                logger.warning(f"[StoryImageBuilder] Enhanced live photo for '{query}' is visually duplicate in 30-day channel history. Skipping.")
                                                continue
                                            cls.record_asset_used(f"live_{img_hash}")
                                            logger.info(f"[StoryImageBuilder] Live Editorial Photo acquired for '{query}': {pdata.get('title')} ({w}x{h}).")
                                            return enhanced
                                else:
                                    logger.debug(f"[StoryImageBuilder] Live photo candidate for '{query}' is on cooldown. Skipping.")
                    except Exception:
                        pass
        except Exception as e:
            logger.debug(f"[StoryImageBuilder] Live editorial search failed for '{query}': {e}")
        return None

    @classmethod
    def enhance_image_for_vip(cls, img_bytes: bytes, target_w: int = 1200, target_h: int = 800) -> bytes:
        """
        Elevates images to 10/10 VIP editorial quality:
        - LANCZOS fit to optimal widescreen standard.
        - Dynamic range polish: contrast +4%, saturation +5%, sharpness +12%.
        - Output pristine JPEG (quality 95).
        """
        if not img_bytes:
            return None
        try:
            from PIL import ImageEnhance
            im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            w, h = im.size

            # Optimal framing: Eliminate blurred sidebars by fitting landscape to 1200x800 and vertical portraits to 1080x1080 square
            aspect = w / max(h, 1)
            if 1.2 <= aspect <= 1.95:
                fitted = ImageOps.fit(im, (target_w, target_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.38))
            elif aspect < 1.2:
                # Vertical portrait or near-square: fit cleanly to 1080x1080 square centered on face (no blurred sidebars!)
                fitted = ImageOps.fit(im, (1080, 1080), method=Image.Resampling.LANCZOS, centering=(0.5, 0.25))
            else:
                fitted = ImageOps.fit(im, (target_w, target_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

            # Editorial enhancement: crisp sharpness and punchy colors
            fitted = ImageEnhance.Contrast(fitted).enhance(1.04)
            fitted = ImageEnhance.Color(fitted).enhance(1.05)
            fitted = ImageEnhance.Sharpness(fitted).enhance(1.12)

            out_io = io.BytesIO()
            fitted.save(out_io, format="JPEG", quality=95, optimize=True)
            return out_io.getvalue()
        except Exception as e:
            logger.warning(f"Error enhancing image for VIP: {e}")
            return img_bytes

    @classmethod
    def create_split_image(cls, img_path1: str, img_path2: str, width: int = 1200, height: int = 800, divider_width: int = 4, is_flags: bool = False) -> bytes:
        """
        Creates a clean 50/50 side-by-side composite split image matching the user's VIP standard.
        """
        try:
            im1 = Image.open(img_path1).convert("RGB")
            im2 = Image.open(img_path2).convert("RGB")

            half_w = (width - divider_width) // 2

            # For leaders, focus slightly higher (0.35) for optimal face centering.
            # For flags, focus directly in center (0.5, 0.5).
            centering = (0.5, 0.5) if is_flags else (0.5, 0.35)

            part1 = ImageOps.fit(im1, (half_w, height), method=Image.Resampling.LANCZOS, centering=centering)
            part2 = ImageOps.fit(im2, (half_w, height), method=Image.Resampling.LANCZOS, centering=centering)

            # Elegant dark divider
            canvas = Image.new("RGB", (width, height), (18, 18, 20))
            canvas.paste(part1, (0, 0))
            canvas.paste(part2, (half_w + divider_width, 0))

            out_io = io.BytesIO()
            canvas.save(out_io, format="JPEG", quality=95, optimize=True)
            return out_io.getvalue()
        except Exception as e:
            logger.error(f"Error creating split image: {e}")
            return None

    @classmethod
    def create_single_flag_canvas(cls, flag_path: str, width: int = 1200, height: int = 800) -> bytes:
        """
        Presents a single country flag cleanly fitted with subtle elegant background framing.
        """
        try:
            im = Image.open(flag_path).convert("RGB")
            fitted = ImageOps.fit(im, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            out_io = io.BytesIO()
            fitted.save(out_io, format="JPEG", quality=95, optimize=True)
            return out_io.getvalue()
        except Exception as e:
            logger.error(f"Error creating single flag canvas: {e}")
            return None
