import os
import re
import io
import logging
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
        ("microsoft", r"\b(microsoft)\b|ម៉ៃក្រូសូហ្វ"),
        ("google", r"\b(google|alphabet)\b|ហ្គូហ្គល"),
        ("intel", r"\b(intel)\b|អ៊ីនធែល"),
        ("amazon", r"\b(amazon|aws)\b|អាម៉ាហ្សូន"),
        ("blackrock", r"\b(blackrock)\b|ប៊្លែករ៉ក់"),
    ]

    LEADER_PATTERNS = [
        ("giorgia_meloni", r"\b(meloni|giorgia meloni)\b|ម៉េឡូនី|មេឡូនី"),
        ("donald_trump", r"\b(trump|donald trump)\b|ត្រាំ|ដូណាល់ ត្រាំ"),
        ("vladimir_putin", r"\b(putin|vladimir putin)\b|ពូទីន|វ្ល៉ាឌីមៀ ពូទីន"),
        ("xi_jinping", r"\b(xi jinping|president xi)\b|ស៊ី ជីនពីង"),
        ("jerome_powell", r"\b(powell|jerome powell)\b|ផៅវែល|ផូវែល"),
        ("kevin_warsh", r"\b(warsh|kevin warsh)\b|វ៉ាស|ខេវិន វ៉ាស"),
        ("elon_musk", r"\b(musk|elon musk)\b|ម៉ាស|អេឡុន ម៉ាស"),
        ("benjamin_netanyahu", r"\b(netanyahu|benjamin netanyahu)\b|ណេតាន់យ៉ាហ៊ូ"),
        ("volodymyr_zelenskyy", r"\b(zelenskyy|zelensky|volodymyr zelenskyy)\b|ហ្សេលេនស្គី"),
        ("emmanuel_macron", r"\b(macron|emmanuel macron)\b|ម៉ាក្រុង"),
        ("keir_starmer", r"\b(starmer|keir starmer)\b|ស្តាម័រ"),
        ("christine_lagarde", r"\b(lagarde|christine lagarde)\b|ឡាការដ៍"),
        ("kazuo_ueda", r"\b(ueda|kazuo ueda)\b|អ៊ូអេដា"),
        ("narendra_modi", r"\b(modi|narendra modi)\b|ម៉ូឌី"),
        ("abdel_fattah_elsisi", r"\b(sisi|el-sisi|abdel fattah)\b|ស៊ីស៊ី|អាប់ដែល ហ្វាតា"),
    ]

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

    IMAGE_COOLDOWN_SECONDS = 14400.0  # 4 hours strict cooldown for ANY static asset
    _RECENT_USED_ASSETS = {}

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

    @classmethod
    def get_available_leader_photo(cls, leader_key: str) -> str:
        """
        Dynamically finds the best, non-repeating leader photo from the gallery.
        If leader has multiple photos (e.g. elon_musk.jpg, elon_musk_2.jpg, ...),
        rotates and selects the least-recently-used one that is NOT on 4-hour cooldown!
        """
        import glob
        pattern = os.path.join(cls.LEADERS_DIR, f"{leader_key}*.jpg")
        candidates = glob.glob(pattern)
        if not candidates:
            return ""

        candidates.sort()

        # Check each photo candidate against individual cooldown
        for c in candidates:
            c_name = os.path.basename(c)
            if not cls.is_asset_on_cooldown(f"photo_{c_name}"):
                return c

        logger.info(f"[StoryImageBuilder] All {len(candidates)} photo variants of '{leader_key}' are currently on 4-hour cooldown.")
        return ""

    @classmethod
    def get_image_for_news(cls, item: dict, analysis: dict = None, default_fetcher=None) -> bytes:
        """
        Main entry point to determine and generate the most accurate image for the news item.
        Enforces strict Anti-Repetition Shield: No static stock asset can repeat within 4 hours!
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
                    direct_hash = hashlib.md5(direct_photo[:1000]).hexdigest()
                    if not cls.is_asset_on_cooldown(f"direct_{direct_hash}"):
                        cls.record_asset_used(f"direct_{direct_hash}")
                        logger.info(f"[StoryImageBuilder] Using verified direct publisher article photo (enhanced for VIP).")
                        return cls.enhance_image_for_vip(direct_photo)
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

        # If ONE leader and ONE brand are involved (e.g. Elon Musk + SpaceX / Tesla), synthesize Split Image!
        # STRICT ZERO REPETITION: Enforce 4-hour cooldown on specific leader photo variant and brand!
        if len(headline_leaders) == 1 and len(detected_brands) >= 1:
            l1, path1, _, _ = headline_leaders[0]
            b1, path2 = detected_brands[0]
            p1_name = os.path.basename(path1)
            if not cls.is_asset_on_cooldown(f"photo_{p1_name}") and not cls.is_asset_on_cooldown(f"brand_{b1}"):
                logger.info(f"[StoryImageBuilder] Synthesizing Leader + Brand Split Image with fresh variant: {p1_name} + {b1}")
                split_bytes = cls.create_split_image(path1, path2)
                if split_bytes:
                    cls.record_asset_used(f"photo_{p1_name}")
                    cls.record_asset_used(f"brand_{b1}")
                    return split_bytes
            else:
                logger.info(f"[StoryImageBuilder] Leader photo '{p1_name}' or Brand '{b1}' on 4h cooldown. Skipping to preserve visual diversity.")

        # Step 5: Single Leader Official Portrait
        # ONLY if the leader is the primary subject in headline and NOT just a casual mention in market/economic news
        if len(headline_leaders) >= 1 and not is_market_index:
            l1, path1, _, _ = headline_leaders[0]
            p1_name = os.path.basename(path1)
            if not cls.is_asset_on_cooldown(f"photo_{p1_name}"):
                logger.info(f"[StoryImageBuilder] Using Single Leader Portrait with fresh variant: {p1_name}")
                try:
                    cls.record_asset_used(f"photo_{p1_name}")
                    with open(path1, "rb") as f:
                        return cls.enhance_image_for_vip(f.read())
                except Exception as e:
                    logger.warning(f"[StoryImageBuilder] Failed reading single leader image {path1}: {e}")
            else:
                logger.info(f"[StoryImageBuilder] Leader portrait variant '{p1_name}' is on 4h cooldown. Skipping to preserve visual variety.")

        # Step 6: Single Country High-Res Flag Canvas (ONLY for single sovereign subject)
        # Note: Dual-Country Flag Split Image synthesis is PERMANENTLY DISABLED per user directive to eliminate mismatched/hybrid flag collages!
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

        # Step 7 & 7.5: Flag Canvases and Macro Topic Stock Photos are PERMANENTLY DISABLED!
        # Strict User Constitutional Directive:
        # "បើគ្មានរូបភាពថ្មីជាក់ស្តែងពីសារព័ត៌មាន (Direct Article Photo) ឬរូបមេដឹកនាំចំៗទេ 
        #  ត្រូវទម្លាក់មកផ្សាយជា MODE B (Clean VIP Text Mode) ស្អាតបាត ១០០% ហាមយករូបដដែលមកបិទភ្ជាប់ជាដាច់ខាត!"
        # This completely guarantees 100% zero image repetition across all news broadcasts.

        # Step 8: Mode B Fallback Guarantee
        # If no authentic direct publisher photo or verified single leader/split asset exists, return None!
        # main.py will automatically broadcast in MODE B (Clean VIP Text Mode), preventing ANY image error or repetition 100%!
        logger.info("[StoryImageBuilder] No authentic direct photo or leader portrait. Falling back to MODE B (VIP Text Mode).")
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

            # If reasonably wide (landscape), fit cleanly to 1200x800
            aspect = w / max(h, 1)
            if 1.2 <= aspect <= 1.95:
                fitted = ImageOps.fit(im, (target_w, target_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.38))
            else:
                # Resize proportionally to fit inside 1200x800 bounds
                im.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
                fitted = im

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
