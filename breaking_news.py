import logging
import hashlib
import xml.etree.ElementTree as ET
import requests

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    ("Investing.com Central Banks", "https://www.investing.com/rss/news_301.rss"),
    ("Investing.com Economy", "https://www.investing.com/rss/news_14.rss"),
    ("MarketWatch Real-time", "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines"),
    ("ForexLive News", "https://www.forexlive.com/feed/news"),
    ("FXStreet Financial", "https://www.fxstreet.com/rss/news"),
    ("Investing.com Gold", "https://www.investing.com/rss/news_14.rss"),
]

class BreakingNewsCollector:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _extract_image(self, entry) -> str:
        """Pulls the article image URL from RSS enclosure / media:* tags."""
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
                            
                            if title:
                                item_id = hashlib.md5((title + link).encode("utf-8")).hexdigest()
                                items.append({
                                    "id": item_id,
                                    "title": title,
                                    "link": link,
                                    "pub_date": pub_date,
                                    "description": desc,
                                    "source": source_name,
                                    "image_url": self._extract_image(entry)
                                })
            except Exception as e:
                logger.debug(f"[BreakingNewsCollector] Fetch failed for {source_name}: {e}")
                continue
        return items
