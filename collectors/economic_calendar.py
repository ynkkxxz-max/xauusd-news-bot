import logging
import requests
from datetime import datetime
import pytz
from config import CAMBODIA_TZ

logger = logging.getLogger(__name__)

# High-impact keywords that directly move XAU/USD
HIGH_IMPACT_KEYWORDS = [
    "CPI", "Consumer Price Index", "NFP", "Non-Farm Payroll", "Non Farm", 
    "FOMC", "Fed Interest Rate", "Interest Rate Decision", "Fed Chair", "Powell",
    "PCE", "Core PCE", "GDP", "Unemployment Rate", "Retail Sales", "PMI", "PPI"
]

class EconomicCalendarCollector:
    def __init__(self):
        # Open source economic calendar feeds
        self.ff_url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

    def fetch_events(self) -> list:
        """
        Fetches this week's economic events, filters for USD / High-Impact events,
        and parses timestamps to Cambodia Time (UTC+7).
        """
        events = []
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(self.ff_url, headers=headers, timeout=12)
            if resp.status_code == 200:
                raw_data = resp.json()
                for item in raw_data:
                    currency = item.get("country", "")
                    impact = item.get("impact", "")
                    title = item.get("title", "")
                    
                    # Focus on USD events or High/Medium impact events
                    if currency in ("USD", "CNY") and impact in ("High", "Medium"):
                        parsed = self._parse_event(item)
                        if parsed:
                            events.append(parsed)
                return events
        except Exception as e:
            logger.warning(f"[EconomicCalendarCollector] Failed to fetch live calendar: {e}")

        return events

    def fetch_day_events(self, day: datetime = None) -> list:
        """All events (any currency/impact) for one Cambodia-time day, chronological."""
        day = day or datetime.now(CAMBODIA_TZ)
        out = []
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(self.ff_url, headers=headers, timeout=12)
            if resp.status_code == 200:
                for item in resp.json():
                    parsed = self._parse_event(item)
                    if parsed and parsed["release_dt"].date() == day.date():
                        out.append(parsed)
        except Exception as e:
            logger.warning(f"[EconomicCalendarCollector] Failed to fetch day calendar: {e}")
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
