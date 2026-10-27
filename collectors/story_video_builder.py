import os
import re
import io
import time
import hashlib
import logging
import urllib.request
import urllib.parse
import requests

logger = logging.getLogger(__name__)

class StoryVideoBuilder:
    """
    VIP High-Impact Breaking News Video Engine.
    Detects, validates, and extracts authentic HD video clips (.mp4) for 
    ultra-important news events (SpaceX launches, military defense/missiles, 
    Fed speeches, major market catalysts, EV/robotics demos).
    Enforces strict 24-hour video cooldown (Zero Video Repetition) and 
    strict <= 25MB payload size for seamless sub-second Telegram mobile streaming.
    """
    VIDEO_COOLDOWN_SECONDS = 86400.0  # 24 hours cooldown
    _RECENT_USED_VIDEOS = {}

    # High-impact topics where video is highly compelling
    VIDEO_CATALYST_PATTERNS = [
        r"\b(missile|air defense|strike|airstrike|iron dome|drone attack|explosion)\b",
        r"\b(rocket|starship|spacex|falcon 9|launch|booster catch|test flight)\b",
        r"\b(unveil|demo|optimus|robot|cybercab|robotaxi|roadster)\b",
        r"\b(speech|press conference|fomc statement|powell speaks|warsh speaks)\b",
        r"\b(tanker attacked|strait of hormuz|red sea|oil spill|protest|clashes)\b",
        r"\b(breaking video|live footage|raw video|video shows)\b",
        # Khmer patterns
        r"មីស៊ីល|ដ្រូន|វាយប្រហារ|បាញ់|ផ្ទុះ|រ៉ុក្កែត|បាញ់បង្ហោះ|ថ្លែងសុន្ទរកថា|បាតុកម្ម|សន្និសីទកាសែត|តេស្តសាកល្បង|រ៉ូបូត"
    ]

    @classmethod
    def is_video_on_cooldown(cls, video_key: str) -> bool:
        """Checks if a video was already used in recent broadcasts within 24 hours."""
        now = time.time()
        last_time = cls._RECENT_USED_VIDEOS.get(video_key, 0.0)
        return (now - last_time) < cls.VIDEO_COOLDOWN_SECONDS

    @classmethod
    def record_video_used(cls, video_key: str):
        """Records video use to prevent repetition for 24 hours."""
        cls._RECENT_USED_VIDEOS[video_key] = time.time()

    @classmethod
    def is_high_importance_for_video(cls, title: str, description: str = "", analysis: dict = None) -> bool:
        """Determines if the news event is of ultra-high importance where video adds massive value."""
        text = f"{title} {description}".lower()
        if analysis and isinstance(analysis, dict):
            text += f" {analysis.get('headline_km', '')} {analysis.get('what_happened', '')}".lower()

        for pat in cls.VIDEO_CATALYST_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                return True
        return False

    @classmethod
    def fetch_story_video(cls, item: dict, analysis: dict = None) -> bytes | str | None:
        """
        Attempts to fetch or acquire an authentic HD video clip (.mp4) for important breaking news.
        Returns:
          - bytes: raw MP4 bytes (ready for Telegram upload)
          - str: direct video URL or local file path
          - None: if no valid, authentic video is found (system will safely use photo or Mode B)
        """
        if not item or not isinstance(item, dict):
            return None

        title = item.get("title", "")
        desc = item.get("description", "")
        article_url = item.get("link", "")
        direct_video_url = item.get("video_url", "")

        is_important = cls.is_high_importance_for_video(title, desc, analysis=analysis)

        # Candidate 1: Direct video URL provided in RSS enclosure / media:content
        if direct_video_url and direct_video_url.startswith("http"):
            v_key = hashlib.md5(direct_video_url.encode("utf-8")).hexdigest()
            if not cls.is_video_on_cooldown(f"vid_{v_key}"):
                logger.info(f"[StoryVideoBuilder] Found direct publisher video candidate: {direct_video_url[:80]}...")
                v_bytes = cls._download_video_stream(direct_video_url, max_bytes=25 * 1024 * 1024)
                if v_bytes and len(v_bytes) >= 100 * 1024:  # At least 100KB
                    cls.record_video_used(f"vid_{v_key}")
                    logger.info(f"[StoryVideoBuilder] Successfully downloaded authentic publisher video ({len(v_bytes)} bytes).")
                    return v_bytes

        # Candidate 2: For high importance news, inspect article metadata (og:video)
        if is_important and article_url and article_url.startswith("http"):
            try:
                scraped_vurl = cls._probe_article_og_video(article_url)
                if scraped_vurl:
                    v_key = hashlib.md5(scraped_vurl.encode("utf-8")).hexdigest()
                    if not cls.is_video_on_cooldown(f"vid_{v_key}"):
                        logger.info(f"[StoryVideoBuilder] Found article og:video candidate: {scraped_vurl[:80]}...")
                        v_bytes = cls._download_video_stream(scraped_vurl, max_bytes=25 * 1024 * 1024)
                        if v_bytes and len(v_bytes) >= 100 * 1024:
                            cls.record_video_used(f"vid_{v_key}")
                            logger.info(f"[StoryVideoBuilder] Acquired authentic article video ({len(v_bytes)} bytes).")
                            return v_bytes
            except Exception as e:
                logger.debug(f"[StoryVideoBuilder] Error probing og:video: {e}")

        # If no authentic video is available, return None so system falls back to photo or Mode B
        return None

    @classmethod
    def _probe_article_og_video(cls, url: str) -> str:
        """Inspects HTML head tags for authentic direct video stream links (og:video, og:video:secure_url)."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            with requests.get(url, headers=headers, timeout=3.5, stream=True) as resp:
                if resp.status_code != 200:
                    return ""
                # Read only the first 80KB to find HTML head metadata quickly
                chunk = resp.raw.read(80000).decode("utf-8", errors="ignore")
                
                # Match og:video or og:video:secure_url
                m_og = re.search(r'<meta\s+property=["\']og:video(?::secure_url)?["\']\s+content=["\'](https?://[^"\']+\.mp4[^"\']*)["\']', chunk, re.IGNORECASE)
                if not m_og:
                    m_og = re.search(r'<meta\s+content=["\'](https?://[^"\']+\.mp4[^"\']*)["\']\s+property=["\']og:video(?::secure_url)?["\']', chunk, re.IGNORECASE)
                
                if m_og:
                    v_url = m_og.group(1).strip()
                    # Filter out ad networks or tracking URLs
                    if not any(bad in v_url.lower() for bad in ["doubleclick", "adroll", "googlesyndication", "pixel"]):
                        return v_url
        except Exception:
            pass
        return ""

    @classmethod
    def _download_video_stream(cls, url: str, max_bytes: int = 25 * 1024 * 1024) -> bytes | None:
        """Downloads video stream safely, aborting if size exceeds max_bytes."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            with requests.get(url, headers=headers, timeout=12.0, stream=True) as resp:
                if resp.status_code != 200:
                    return None
                
                # Check Content-Length header if provided
                cl = resp.headers.get("Content-Length")
                if cl and int(cl) > max_bytes:
                    logger.warning(f"[StoryVideoBuilder] Video exceeds max size ({int(cl)} > {max_bytes} bytes). Skipping.")
                    return None

                buf = io.BytesIO()
                downloaded = 0
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        downloaded += len(chunk)
                        if downloaded > max_bytes:
                            logger.warning(f"[StoryVideoBuilder] Video exceeded {max_bytes} bytes during stream. Aborting.")
                            return None
                        buf.write(chunk)
                return buf.getvalue()
        except Exception as e:
            logger.debug(f"[StoryVideoBuilder] Video download failed: {e}")
            return None
