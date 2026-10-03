import html
import re
import logging
import hashlib
import concurrent.futures
import xml.etree.ElementTree as ET
import requests

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# The 7 Core Pillars High-Speed Feed Matrix (Sub-Second Global Wire Feeds)
# 1. 🌐 សេដ្ឋកិច្ច (Economy: GDP, CPI, Inflation, NFP, Retail Sales, PMI)
# 2. ⚔️ នយោបាយភូមិសាស្ត្រ (Geopolitics: War, Middle East, Iran, Ukraine, Hormuz)
# 3. 💻 បច្ចេកវិទ្យា (Technology / AI / Chips / Big Tech / Cybersecurity)
# 4. 🏦 គោលនយោបាយរូបិយវត្ថុ និងធនាគារកណ្តាល (Monetary Policy & Central Banks)
# 5. 🛢️ បរិស្ថាន និងធនធានធម្មជាតិ (Environment, OPEC, Crude Oil, Gold, Energy)
# 6. 👥 កត្តាសង្គម និងប្រជាសាស្ត្រ (Social, Demographics, Labor, Strikes, Wages)
# 7. ⚖️ ច្បាប់ បទប្បញ្ញត្តិ និងគោលនយោបាយរដ្ឋាភិបាល (Laws, Tariffs, Debt, Sanctions)
# -------------------------------------------------------------------------
RSS_FEEDS = [
    # --- Pillar 1: Economy ---
    ("Google News Economy 1h", "https://news.google.com/rss/search?q=(inflation+OR+cpi+OR+gdp+OR+pmi+OR+retail+sales+OR+recession)+when:1h&hl=en-US&gl=US&ceid=US:en"),
    ("CNBC Economy", "https://www.cnbc.com/id/20910258/device/rss/rss.html"),
    ("MarketWatch Real-time", "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines"),
    ("Yahoo Finance Global", "https://finance.yahoo.com/news/rssindex"),
    ("ForexLive News", "https://www.forexlive.com/feed/news"),

    # --- Pillar 2: Geopolitics ---
    ("Google News Geopolitics 1h", "https://news.google.com/rss/search?q=(iran+OR+israel+OR+war+OR+trump+OR+middle+east+OR+sanctions+OR+hormuz+OR+russia+OR+ukraine)+when:1h&hl=en-US&gl=US&ceid=US:en"),
    ("Al Jazeera World", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("BBC World News", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("CNBC World News", "https://www.cnbc.com/id/100727362/device/rss/rss.html"),

    # --- Pillar 3: Technology / AI / Semiconductor ---
    ("Google News Tech 1h", "https://news.google.com/rss/search?q=(ai+OR+semiconductor+OR+chips+OR+nvidia+OR+openai+OR+cyberattack+OR+big+tech)+when:1h&hl=en-US&gl=US&ceid=US:en"),
    ("CNBC Tech", "https://www.cnbc.com/id/19854910/device/rss/rss.html"),
    ("TechCrunch", "https://techcrunch.com/feed/"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),

    # --- Pillar 4: Monetary Policy & Central Banks ---
    ("Google News Central Banks 1h", "https://news.google.com/rss/search?q=(federal+reserve+OR+powell+OR+fomc+OR+interest+rate+OR+ecb+OR+boj+OR+central+bank)+when:1h&hl=en-US&gl=US&ceid=US:en"),
    ("Federal Reserve Press", "https://www.federalreserve.gov/feeds/press_monetary.xml"),
    ("ECB Press Releases", "https://www.ecb.europa.eu/rss/press.html"),

    # --- Pillar 5: Environment & Natural Resources (OPEC / Oil / Gold) ---
    ("Google News Energy 1h", "https://news.google.com/rss/search?q=(crude+oil+OR+opec+OR+gold+price+OR+xauusd+OR+energy+crisis+OR+natural+gas)+when:1h&hl=en-US&gl=US&ceid=US:en"),
    ("OilPrice Real-time", "https://oilprice.com/rss/main"),
    ("CNBC Energy", "https://www.cnbc.com/id/19836768/device/rss/rss.html"),

    # --- Pillar 6: Social & Demographics (Labor, Employment, Strikes) ---
    ("Google News Labor & Jobs 1h", "https://news.google.com/rss/search?q=(strike+OR+layoffs+OR+unemployment+claims+OR+consumer+sentiment+OR+wages)+when:1h&hl=en-US&gl=US&ceid=US:en"),
    ("CNBC Jobs & Economy", "https://www.cnbc.com/id/10000115/device/rss/rss.html"),

    # --- Pillar 7: Laws, Regulations & Government Policies (Tariffs, Sanctions, Debt) ---
    ("Google News Policies & Tariffs 1h", "https://news.google.com/rss/search?q=(tariffs+OR+trade+war+OR+debt+ceiling+OR+sanctions+OR+crypto+regulation)+when:1h&hl=en-US&gl=US&ceid=US:en"),
    ("CNBC US Politics", "https://www.cnbc.com/id/10000113/device/rss/rss.html"),

    # --- Pillar 8: Digital Assets, Bitcoin & Cryptocurrency (ប្រាក់ឌីជីថល) ---
    ("Google News Crypto 1h", "https://news.google.com/rss/search?q=(bitcoin+OR+crypto+OR+cbdc+OR+stablecoin+OR+ethereum+OR+sec+crypto)+when:1h&hl=en-US&gl=US&ceid=US:en"),
    ("CoinDesk Top News", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("CoinTelegraph Top", "https://cointelegraph.com/rss"),
]


class BreakingNewsCollector:
    DISALLOWED_SOURCES = [
        "united24", "moscow times", "france24", "ua.news", "tnglobal", "morningstar",
        "middle east eye", "blogger", "substack", "medium", "dailystar", "the sun", 
        "daily mail", "mirror", "pr newswire", "globenewswire", "business wire", "press release",
        "biggo", "hawaii", "tz", "vietnam", "tribune", "kalkine"
    ]

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # In-memory cleared sets for immediate data purging after sending
        self._cleared_ids = set()
        self._cleared_links = set()
        self._cleared_titles = set()

    def clear_item(self, news_id: str = "", link: str = "", title: str = ""):
        """
        Immediately purges and blacklists a news item from data pool right after sending
        so it can NEVER be fetched, processed, or sent again.
        """
        if news_id:
            self._cleared_ids.add(str(news_id).strip())
        if link:
            clean_l = link.split("?")[0].rstrip("/").lower()
            self._cleared_links.add(clean_l)
            slug = clean_l.split("/")[-1]
            if len(slug) >= 8:
                self._cleared_links.add(slug)
        if title:
            self._cleared_titles.add(title.strip().lower())
        logger.info(f"[DATA CLEARED] News item '{title[:50]}' purged from data pool immediately.")

    def is_cleared(self, item_id: str, link: str = "", title: str = "") -> bool:
        """Checks if item was already sent and cleared from data."""
        if item_id in self._cleared_ids:
            return True
        if title and title.strip().lower() in self._cleared_titles:
            return True
        if link:
            clean_l = link.split("?")[0].rstrip("/").lower()
            if clean_l in self._cleared_links:
                return True
            slug = clean_l.split("/")[-1]
            if slug and slug in self._cleared_links:
                return True
        return False

    def _extract_image(self, entry) -> str:
        """Pulls the article image URL from RSS enclosure / media:* / description img tags."""
        enc = entry.find("enclosure")
        if enc is not None and "image" in (enc.get("type") or ""):
            url = (enc.get("url") or "").strip()
            if url:
                return url
        for tag, attr_medium in (("content", True), ("thumbnail", False)):
            node = entry.find("{http://search.yahoo.com/mrss/}" + tag)
            if node is None:
                continue
            if attr_medium and not ((node.get("medium") == "image") or (node.get("type") or "").startswith("image")):
                continue
            url = (node.get("url") or "").strip()
            if url:
                return url
        for tag in ("description", "{http://purl.org/rss/1.0/modules/content/}encoded"):
            desc_text = entry.findtext(tag, "")
            if desc_text and "<img" in desc_text:
                m = re.search(r'<img[^>]+src=[\'"]([^\'"]+)[\'"]', desc_text, re.IGNORECASE)
                if m:
                    u = m.group(1).strip()
                    if u.startswith("http") and not any(ic in u.lower() for ic in ["icon", "logo", "avatar", "1x1"]):
                        return u
        return ""

    def _fetch_single_feed(self, source_name: str, feed_url: str) -> list:
        """Fetches and parses a single RSS feed."""
        items = []
        try:
            resp = requests.get(feed_url, headers=self.headers, timeout=6)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                channel = root.find("channel")
                if channel is not None:
                    for entry in channel.findall("item")[:10]:
                        title = entry.findtext("title", "").strip()
                        link = entry.findtext("link", "").strip()
                        pub_date = entry.findtext("pubDate", "").strip()
                        desc = entry.findtext("description", "").strip()

                        # Clean title and description of raw HTML and HTML entities
                        title = re.sub(r'<[^>]+>', ' ', title)
                        title = html.unescape(title)
                        title = re.sub(r'\s+', ' ', title).strip()

                        # Clean publisher brand suffixes & website taglines from title
                        PUBLISHER_SUFFIX_REGEX = r'\s*[-–—|]\s*(?:ABC(?:\s*News)?|BBC(?:\s*News)?|CNBC|Reuters|The Jerusalem Post|Fox Business|Fox News|Bloomberg|The Wall Street Journal|WSJ|AP(?:\s*News)?|MarketWatch|Yahoo Finance|FXStreet|ForexLive|Al Jazeera|Ars Technica|TechCrunch)(?:\b[^\n]*)?$'
                        title = re.sub(PUBLISHER_SUFFIX_REGEX, '', title, flags=re.IGNORECASE).strip()
                        title = re.sub(r'\s*[-–—|:]\s*[\w\.-]+\.(?:com|org|net|id|uk|kh|gov|io|edu|vn|th)\b.*$', '', title, flags=re.IGNORECASE).strip()
                        title = re.sub(r'\s*[-–—|:]\s*(?:Breaking News|Latest News|Videos|Top Stories|World News|Live Updates).*$', '', title, flags=re.IGNORECASE).strip()
                        title = re.sub(r'\s*[:\-–—|]\s*(?:Report|Reports|Analysis|Exclusive|Live updates|Live|Updates)\s*$', '', title, flags=re.IGNORECASE).strip()
                        title = re.sub(r'\s*[\[\(](?:Report|Reports|Analysis|Exclusive)[\]\)]\s*$', '', title, flags=re.IGNORECASE).strip()

                        clean_desc = re.sub(r'<[^>]+>', ' ', desc)
                        clean_desc = html.unescape(clean_desc)
                        clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()

                        # If clean_desc is identical to title or repeats title prefix, remove repetition
                        if clean_desc.lower() == title.lower() or clean_desc.lower().startswith(title.lower()):
                            remainder = clean_desc[len(title):].strip(" -–—:| ")
                            if len(remainder) < 15:
                                clean_desc = ""
                            else:
                                clean_desc = remainder

                        # Strictly reject questions anywhere in title (speculative / clickbait)
                        if not title or "?" in title:
                            continue

                        # Strictly reject reviews, opinions, podcasts, entertainment, streaming, movies, sports, satire, and memecoin/airdrop spam
                        full_entry_text = f"{title} {clean_desc}".lower()
                        NON_NEWS_PATTERNS = [
                            "press review", "review:", "opinion:", "opinion |", "analysis:", "analysis |", "podcast", "roundup", "editorial",
                            "new to streaming", "streaming:", "streaming on", "netflix", "hollywood", "box office", "tv series", "movie", "movies",
                            "film", "films", "trailer", "actor", "actress", "celebrity", "album", "concert", "recipe", "cuisine", "french food", "horoscope",
                            "hilarious", "satire", "parody", "comedy", "anti-enshittification", "funny",
                            "manchester city", "man city", "premier league", "champions league", "football", "soccer", "fifa", "uefa",
                            "la liga", "serie a", "bundesliga", "world cup", "olympics", "super bowl", "nfl", "nba", "mlb", "nhl", "cricket", "tennis",
                            "pinto", "whistleblower", "striker", "goalkeeper", "ballon d'or",
                            "dating", "romance", "relationship", "divorce", "girlfriend", "boyfriend", "breakup", "ended relationship",
                            "airdrop", "presale", "giveaway", "memecoin", "meme coin", "pepe", "shiba inu", "dogecoin", "100x", "pump and dump"
                        ]
                        if any(p in full_entry_text for p in NON_NEWS_PATTERNS):
                            continue

                        # Extract true publisher source (e.g. CNN, Reuters, AP News, Bloomberg)
                        actual_source = source_name
                        src_elem = entry.find("source")
                        if src_elem is not None and src_elem.text and src_elem.text.strip():
                            actual_source = src_elem.text.strip()

                        # Always strip trailing publisher suffix from title (e.g. " - CNBC", " - West Hawaii Today", " - PR Newswire")
                        if " - " in title:
                            parts = title.rsplit(" - ", 1)
                            if len(parts) == 2 and 2 <= len(parts[1].strip()) <= 45:
                                if actual_source == source_name:
                                    actual_source = parts[1].strip()
                                title = parts[0].strip()
                        elif " | " in title:
                            parts = title.rsplit(" | ", 1)
                            if len(parts) == 2 and 2 <= len(parts[1].strip()) <= 45:
                                if actual_source == source_name:
                                    actual_source = parts[1].strip()
                                title = parts[0].strip()

                        # Clean source name of verbose trailers
                        actual_source = re.sub(r'\s*[-–—|:]\s*(?:Breaking News|Latest News|Videos|Top Stories|World News|Live).*$', '', actual_source, flags=re.IGNORECASE).strip()

                        if any(bad in actual_source.lower() for bad in self.DISALLOWED_SOURCES):
                            continue
                        if any(ord(c) > 0x0600 and ord(c) < 0x06FF for c in actual_source):  # Arabic
                            continue

                        img_url = self._extract_image(entry)
                        # Reject any google logo or generic icons in RSS
                        if img_url and any(bad in img_url.lower() for bad in ["googleusercontent", "gstatic", "google", "logo", "icon", "avatar", "1x1"]):
                            img_url = ""

                        item_id = hashlib.md5((title + link).encode("utf-8")).hexdigest()
                        items.append({
                            "id": item_id,
                            "title": title,
                            "link": link,
                            "pub_date": pub_date,
                            "description": clean_desc,
                            "source": actual_source,
                            "image_url": img_url
                        })
        except Exception as e:
            logger.debug(f"[BreakingNewsCollector] Fetch failed for {source_name}: {e}")
        return items

    def fetch_latest_news(self) -> list:
        """Fetches news items from established 7-pillar market feeds simultaneously in parallel."""
        items = []
        seen_ids = set()
        seen_titles_norm = set()
        seen_slugs = set()

        # Concurrent parallel fetch across all 21 feeds for sub-second delivery
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(self._fetch_single_feed, s_name, f_url)
                for s_name, f_url in RSS_FEEDS
            ]
            for future in concurrent.futures.as_completed(futures):
                try:
                    feed_items = future.result()
                    for it in feed_items:
                        t = (it.get("title") or "").strip()
                        l = (it.get("link") or "").strip()
                        nid = it["id"]

                        # Strictly purge any item that has been cleared or already processed
                        if self.is_cleared(nid, l, t):
                            continue

                        # Check ID
                        if nid in seen_ids:
                            continue

                        # Check Normalized Title (strip punctuation/spaces/lowercase)
                        norm_t = re.sub(r'[^a-zA-Z0-9\u1780-\u17FF]', '', t).lower()
                        if norm_t and len(norm_t) >= 15:
                            t_sig = norm_t[:45]
                            if t_sig in seen_titles_norm:
                                continue
                            seen_titles_norm.add(t_sig)

                        # Check Link Slug (last path segment)
                        clean_link = l.split("?")[0].rstrip("/").lower()
                        slug = clean_link.split("/")[-1]
                        if len(slug) >= 12:
                            if slug in seen_slugs:
                                continue
                            seen_slugs.add(slug)

                        seen_ids.add(nid)
                        items.append(it)
                except Exception as err:
                    logger.debug(f"[BreakingNewsCollector] Thread pool worker error: {err}")

        return items
