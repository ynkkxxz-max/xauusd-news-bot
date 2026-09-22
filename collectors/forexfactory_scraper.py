import logging
import requests
from datetime import datetime
from config import CAMBODIA_TZ

logger = logging.getLogger(__name__)

class ForexFactoryScraper:
    def __init__(self):
        self.calendar_json_url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    def fetch_market_snapshot(self) -> dict:
        """
        Gathers:
        1. Majors Forex currency movements (EUR/USD, GBP/USD, USD/JPY, USD/CHF)
        2. Today's high/medium impact calendar events from ForexFactory
        """
        calendar_events = self._fetch_today_events()
        currencies_overview = self._fetch_currencies_overview()
        
        return {
            "currencies": currencies_overview,
            "today_events": calendar_events,
            "timestamp": datetime.now(CAMBODIA_TZ).strftime("%Y-%m-%d %H:%M")
        }

    def _fetch_today_events(self) -> list:
        events = []
        try:
            resp = requests.get(self.calendar_json_url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                raw_data = resp.json()
                now_kh = datetime.now(CAMBODIA_TZ)
                today_str = now_kh.strftime("%Y-%m-%d")

                for item in raw_data:
                    date_raw = item.get("date", "")
                    try:
                        event_dt = datetime.fromisoformat(date_raw).astimezone(CAMBODIA_TZ)
                        if event_dt.strftime("%Y-%m-%d") == today_str:
                            events.append({
                                "title": item.get("title", ""),
                                "country": item.get("country", ""),
                                "impact": item.get("impact", ""),
                                "forecast": item.get("forecast", ""),
                                "previous": item.get("previous", ""),
                                "actual": item.get("actual", ""),
                                "time_kh": event_dt.strftime("%I:%M %p")
                            })
                    except Exception:
                        continue
        except Exception as e:
            logger.warning(f"[ForexFactoryScraper] Calendar fetch error: {e}")
        return events

    def _fetch_currencies_overview(self) -> dict:
        """Fetches major currency pairs snapshot."""
        overview = {}
        # Fetch Swissquote or Yahoo finance major pairs for real interbank currency rates
        pairs = {
            "EURUSD": "EUR/USD",
            "GBPUSD": "GBP/USD",
            "USDJPY": "USD/JPY",
            "USDCHF": "USD/CHF"
        }
        for code, label in pairs.items():
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}=X?interval=1d&range=1d"
                r = requests.get(url, headers=self.headers, timeout=5)
                if r.status_code == 200:
                    meta = r.json()["chart"]["result"][0]["meta"]
                    price = meta.get("regularMarketPrice", 0.0)
                    prev = meta.get("previousClose") or price
                    pct = ((price - prev) / prev * 100) if prev else 0.0
                    overview[label] = {
                        "price": round(price, 4),
                        "change_pct": round(pct, 2)
                    }
            except Exception:
                overview[label] = {"price": "N/A", "change_pct": 0.0}
        return overview
