import html
import re
import logging
import hashlib
import xml.etree.ElementTree as ET
import requests

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    # 1. Real-time Global Geopolitics & Middle East / Iran / World News (Google News Verified)
    ("Google News Geopolitics", "https://news.google.com/rss/search?q=(iran+OR+israel+OR+war+OR+trump+OR+middle+east+OR+sanctions+OR+hormuz+OR+rial)+when:1d&hl=en-US&gl=US&ceid=US:en"),
    ("Google News Gold & Macro", "https://news.google.com/rss/search?q=(xauusd+OR+gold+price+OR+federal+reserve+OR+powell+OR+fomc)+when:1d&hl=en-US&gl=US&ceid=US:en"),
    ("Google News Global Economy", "https://news.google.com/rss/search?q=(inflation+OR+cpi+OR+gdp+OR+tariffs+OR+opec+OR+crude+oil)+when:1d&hl=en-US&gl=US&ceid=US:en"),
    
    # 2. Institutional Media Feeds
    ("Al Jazeera World", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("CNBC US Politics", "https://www.cnbc.com/id/10000113/device/rss/rss.html"),
    ("CNBC World News", "https://www.cnbc.com/id/100727362/device/rss/rss.html"),
    ("ForexLive News", "https://www.forexlive.com/feed/news"),
    ("MarketWatch Real-time", "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines"),
    ("Federal Reserve Official", "https://www.federalreserve.gov/feeds/press_monetary.xml"),
]

class BreakingNewsCollector:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _extract_image(self, entry) -> str:
        """Pulls the article image URL from RSS enclosure / media:* / description img tags."""
        import re
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

    def fetch_latest_news(self) -> list:
        """Fetches news items from established RSS market feeds."""
        items = []
        for source_name, feed_url in RSS_FEEDS:
            try:
                resp = requests.get(feed_url, headers=self.headers, timeout=8)
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

                            if not title or title.endswith("?"):
                                continue

                            if any(title.lower().startswith(p) for p in ["opinion:", "opinion |", "analysis:", "analysis |"]):
                                continue

                            # Extract true publisher source (e.g. CNN, Reuters, AP News, Bloomberg)
                            actual_source = source_name
                            src_elem = entry.find("source")
                            if src_elem is not None and src_elem.text and src_elem.text.strip():
                                actual_source = src_elem.text.strip()
                            elif " - " in title:
                                parts = title.rsplit(" - ", 1)
                                if len(parts) == 2 and 2 <= len(parts[1].strip()) <= 30:
                                    actual_source = parts[1].strip()
                                    title = parts[0].strip()

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
                continue
        return items
