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
    TOPICS_DIR = "assets/topics"
    BRANDS_DIR = "assets/brands"

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
    ]

    COUNTRY_PATTERNS = [
        ("us", r"\b(us|usa|united states|america)\b|អាមេរិក|សហរដ្ឋអាមេរិក"),
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
        ("kr", r"\b(korea|korean|south korea|seoul)\b|កូរ៉េ"),
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
        ("qa", r"\b(qatar|doha)\b|កាតា"),
        ("eg", r"\b(egypt|egyptian|cairo)\b|អេហ្ស៊ីប"),
    ]

    TOPIC_PATTERNS = [
        ("federal_reserve", r"\b(federal reserve|fed\b|fomc|rate cut|rate hike|central bank|eccles building)\b|ធនាគារកណ្តាល|អត្រាការប្រាក់"),
        ("gold_bullion", r"\b(gold|bullion|xauusd|spot gold|gold reserve|gold price)\b|មាស|ហាងឆេងមាស"),
        ("crude_oil", r"\b(crude oil|brent|wti|opec|petroleum|oil price|energy market|diesel|gasoline)\b|ប្រេងកាត|ប្រេងម៉ាស៊ូត|ប្រេងឆៅ"),
        ("semiconductor_chips", r"\b(semiconductor|chip|chips|wafer|tsmc|nvidia|intel|artificial intelligence|ai)\b|បន្ទះឈីប|បច្ចេកវិទ្យា ai"),
        ("bitcoin_crypto", r"\b(bitcoin|btc|cryptocurrency|crypto reserve|crypto|stablecoin|ethereum|eth)\b|គ្រីបតូ|ប្រាក់ឌីជីថល"),
        ("geopolitics_naval", r"\b(hormuz|strait of hormuz|red sea|naval|warship|persian gulf|military strike|war)\b|សង្គ្រាម|ច្រកសមុទ្រ"),
        ("wall_street", r"\b(wall street|nyse|nasdaq|s&p 500|stock market|equities)\b|ទីផ្សារភាគហ៊ុន"),
    ]

    @classmethod
    def get_image_for_news(cls, item: dict, analysis: dict = None, default_fetcher=None) -> bytes:
        """
        Main entry point to determine and generate the most accurate image for the news item.
        """
        title = item.get("title", "")
        desc = item.get("description", "")
        headline_km = ""
        key_event = ""
        if isinstance(analysis, dict):
            headline_km = analysis.get("headline_km", "")
            key_event = analysis.get("key_event", "")

        comb_text = f"{title} {desc} {headline_km} {key_event}".lower()

        # Step 1: Detect Leaders involved
        detected_leaders = []
        for leader_key, pat in cls.LEADER_PATTERNS:
            if re.search(pat, comb_text, re.IGNORECASE):
                img_path = os.path.join(cls.LEADERS_DIR, f"{leader_key}.jpg")
                if os.path.exists(img_path):
                    detected_leaders.append((leader_key, img_path))

        # If TWO leaders are involved, synthesize dual-leader split image!
        if len(detected_leaders) >= 2:
            l1, path1 = detected_leaders[0]
            l2, path2 = detected_leaders[1]
            logger.info(f"[StoryImageBuilder] Synthesizing Dual-Leader Split Image: {l1} + {l2}")
            split_bytes = cls.create_split_image(path1, path2)
            if split_bytes:
                return split_bytes

        # Step 1.5: Detect Brands / Tech Giants involved
        detected_brands = []
        for brand_key, pat in cls.BRAND_PATTERNS:
            if re.search(pat, comb_text, re.IGNORECASE):
                b_path = os.path.join(cls.BRANDS_DIR, f"{brand_key}_dark.jpg")
                if not os.path.exists(b_path):
                    b_path = os.path.join(cls.BRANDS_DIR, f"{brand_key}.png")
                if os.path.exists(b_path):
                    detected_brands.append((brand_key, b_path))

        # If ONE leader and ONE brand are involved (e.g. Zelenskyy + SpaceX / Starlink), synthesize Split Image!
        if len(detected_leaders) == 1 and len(detected_brands) >= 1:
            l1, path1 = detected_leaders[0]
            b1, path2 = detected_brands[0]
            logger.info(f"[StoryImageBuilder] Synthesizing Leader + Brand Split Image: {l1} + {b1}")
            split_bytes = cls.create_split_image(path1, path2)
            if split_bytes:
                return split_bytes

        # Step 2: Detect Countries / Flags involved
        detected_countries = []
        for c_code, pat in cls.COUNTRY_PATTERNS:
            if re.search(pat, comb_text, re.IGNORECASE):
                flag_path = os.path.join(cls.FLAGS_DIR, f"{c_code}.png")
                if os.path.exists(flag_path):
                    detected_countries.append((c_code, flag_path))

        # If TWO countries are involved (and no dual leader), synthesize dual-flag split image!
        if len(detected_countries) >= 2:
            c1, path1 = detected_countries[0]
            c2, path2 = detected_countries[1]
            logger.info(f"[StoryImageBuilder] Synthesizing Dual-Country Flag Split Image: {c1} + {c2}")
            split_bytes = cls.create_split_image(path1, path2, is_flags=True)
            if split_bytes:
                return split_bytes

        # Step 3: Single Leader Official Portrait
        if len(detected_leaders) == 1:
            l1, path1 = detected_leaders[0]
            logger.info(f"[StoryImageBuilder] Using Single Leader Portrait: {l1}")
            try:
                with open(path1, "rb") as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to read leader image {path1}: {e}")

        # Step 4: Direct Genuine Article Image from Publisher
        if default_fetcher:
            direct_photo = default_fetcher(item)
            if direct_photo:
                logger.info(f"[StoryImageBuilder] Using verified direct publisher article photo.")
                return direct_photo

        # Step 5: Macro Topic Authentic Ultra-HD Photo
        for topic_key, pat in cls.TOPIC_PATTERNS:
            if re.search(pat, comb_text, re.IGNORECASE):
                topic_path = os.path.join(cls.TOPICS_DIR, f"{topic_key}.jpg")
                if os.path.exists(topic_path):
                    logger.info(f"[StoryImageBuilder] Using Macro Topic Photo: {topic_key}")
                    try:
                        with open(topic_path, "rb") as f:
                            return f.read()
                    except Exception as e:
                        logger.warning(f"Failed to read topic image {topic_path}: {e}")

        # Step 6: Single Country High-Res Flag / Visual
        if len(detected_countries) == 1:
            c1, path1 = detected_countries[0]
            logger.info(f"[StoryImageBuilder] Using Single Country Flag Canvas: {c1}")
            flag_canvas = cls.create_single_flag_canvas(path1)
            if flag_canvas:
                return flag_canvas

        return None

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
