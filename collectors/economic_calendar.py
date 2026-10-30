import logging
import requests
from datetime import datetime
import pytz
from config import CAMBODIA_TZ

logger = logging.getLogger(__name__)

# High-impact keywords that directly move XAU/USD
HIGH_IMPACT_KEYWORDS = [
    "CPI", "Consumer Price Index", "NFP", "Non-Farm Payroll", "Non Farm", 
    "FOMC", "Fed Interest Rate", "Interest Rate Decision", "Fed Chair", "Fed Chair Speech",
    "PCE", "Core PCE", "GDP", "Unemployment Rate", "Retail Sales", "PMI", "PPI"
]

import os
import json
import time

CACHE_FILE = "calendar_cache.json"

class EconomicCalendarCollector:
    _global_cached_raw = None
    _global_last_fetch_ts = 0.0
    _global_rate_limit_until = 0.0
    _last_rate_limit_warn_ts = 0.0

    def __init__(self):
        # Open source economic calendar feeds
        self.ff_url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        if EconomicCalendarCollector._global_cached_raw is None:
            self._load_disk_cache()

    def _load_disk_cache(self):
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    EconomicCalendarCollector._global_cached_raw = data.get("events", [])
                    EconomicCalendarCollector._global_last_fetch_ts = data.get("timestamp", 0.0)
                    logger.info(f"[EconomicCalendarCollector] Loaded {len(EconomicCalendarCollector._global_cached_raw)} events from disk cache.")
        except Exception as e:
            logger.warning(f"[EconomicCalendarCollector] Could not load disk cache: {e}")

    def _save_disk_cache(self, raw_events: list):
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({"events": raw_events, "timestamp": time.time()}, f, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"[EconomicCalendarCollector] Could not save disk cache: {e}")

    def _fetch_raw_calendar(self, max_age: float = 60.0) -> list:
        now = time.time()
        # Strictly return cached events if still fresh or currently backed off due to rate limit
        if EconomicCalendarCollector._global_cached_raw and (now - EconomicCalendarCollector._global_last_fetch_ts < max_age or now < EconomicCalendarCollector._global_rate_limit_until):
            return EconomicCalendarCollector._global_cached_raw

        # If currently in rate-limit backoff period, NEVER hit network
        if now < EconomicCalendarCollector._global_rate_limit_until:
            return EconomicCalendarCollector._global_cached_raw or []

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            resp = requests.get(self.ff_url, headers=headers, timeout=12)
            if resp.status_code == 200:
                raw_data = resp.json()
                if isinstance(raw_data, list) and len(raw_data) > 0:
                    EconomicCalendarCollector._global_cached_raw = raw_data
                    EconomicCalendarCollector._global_last_fetch_ts = now
                    self._save_disk_cache(raw_data)
                    return raw_data
            elif resp.status_code == 429:
                EconomicCalendarCollector._global_rate_limit_until = now + 600.0  # Back off 10 minutes
                EconomicCalendarCollector._global_last_fetch_ts = now
                if now - EconomicCalendarCollector._last_rate_limit_warn_ts > 600.0:
                    logger.info(f"[EconomicCalendarCollector] Calendar API rate-limited (429). Cleanly serving {len(EconomicCalendarCollector._global_cached_raw or [])} cached events for 10 minutes.")
                    EconomicCalendarCollector._last_rate_limit_warn_ts = now
        except Exception as e:
            logger.debug(f"[EconomicCalendarCollector] Network exception: {e}")

        # Fallback to in-memory or disk cache
        if EconomicCalendarCollector._global_cached_raw:
            return EconomicCalendarCollector._global_cached_raw

        return []

    def fetch_events(self, max_age: float = 30.0) -> list:
        """
        Fetches this week's economic events, filters for USD / High-Impact events,
        and parses timestamps to Cambodia Time (UTC+7).
        """
        events = []
        raw_data = self._fetch_raw_calendar(max_age=max_age)
        for item in raw_data:
            currency = item.get("country", "")
            impact = item.get("impact", "")
            title = item.get("title", "")
            if currency in ("USD", "CNY") and impact in ("High", "Medium"):
                parsed = self._parse_event(item)
                if parsed:
                    events.append(parsed)
        return events

    def fetch_day_events(self, day: datetime = None) -> list:
        """All events (any currency/impact) for one Cambodia-time day, chronological."""
        day = day or datetime.now(CAMBODIA_TZ)
        out = []
        raw_data = self._fetch_raw_calendar(max_age=120.0)
        for item in raw_data:
            parsed = self._parse_event(item)
            if parsed and parsed["release_dt"].date() == day.date():
                out.append(parsed)
        out.sort(key=lambda ev: ev["release_dt"])
        return out

    def _parse_event(self, item: dict) -> dict:
        """Parses calendar item into normalized dictionary."""
        date_raw = item.get("date", "") # ISO format like '2026-09-20T08:30:00-04:00'
        try:
            event_dt = datetime.fromisoformat(date_raw)
            # Convert to Cambodia timezone
            event_dt_kh = event_dt.astimezone(CAMBODIA_TZ)
        except Exception:
            event_dt_kh = datetime.now(CAMBODIA_TZ)

        title = item.get("title", "Economic Event")
        currency = item.get("country", "USD")
        impact = item.get("impact", "High")
        forecast = item.get("forecast", "")
        previous = item.get("previous", "")
        actual = item.get("actual", "")

        event_id = f"{currency}_{title}_{event_dt_kh.strftime('%Y%m%d_%H%M')}".replace(" ", "_")

        return {
            "id": event_id,
            "title": title,
            "currency": currency,
            "impact": impact.upper(),
            "actual": actual,
            "forecast": forecast,
            "previous": previous,
            "release_dt": event_dt_kh,
            "release_time_str": event_dt_kh.strftime("%H:%M"),
            "release_date_str": event_dt_kh.strftime("%d/%m/%Y"),
            "source": "ForexFactory / Global Economic Calendar"
        }

    def is_news_danger_zone(self, buffer_minutes: int = 30) -> dict:
        """
        AI Market Regime & High-Impact News Filter:
        Returns information if current time is within +/- buffer_minutes of a High-Impact USD news event.
        (e.g., 30 mins before to 30 mins after CPI, NFP, FOMC).
        """
        now_kh = datetime.now(CAMBODIA_TZ)
        events = self.fetch_events()
        for ev in events:
            if ev.get("currency") == "USD" and ev.get("impact") == "HIGH":
                diff_minutes = (ev["release_dt"] - now_kh).total_seconds() / 60.0
                # Between 30 mins before and 30 mins after high-impact news release
                if -30 <= diff_minutes <= buffer_minutes:
                    return {
                        "is_danger": True,
                        "title": ev["title"],
                        "release_time": ev["release_time_str"],
                        "mins_left": round(diff_minutes, 1)
                    }
        return {"is_danger": False}

