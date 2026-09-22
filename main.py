import re
import time
import logging
from datetime import datetime
from email.utils import parsedate_to_datetime
import requests
import pytz

from config import (
    CAMBODIA_TZ, DAILY_PRICE_ALERT_HOUR, DAILY_PRICE_ALERT_MINUTE,
    INTERVAL_NORMAL, INTERVAL_UPCOMING, INTERVAL_HIGH_IMPACT,
    BREAKING_ALERT_MIN_GAP
)
import database
from collectors.gold_price import GoldPriceCollector
from collectors.economic_calendar import EconomicCalendarCollector
from collectors.breaking_news import BreakingNewsCollector
from collectors.calendar_image import CalendarImageBuilder
from analyzers.gold_filter import GoldNewsFilter
from analyzers.gemini_analyzer import GeminiAnalyzer
from analyzers.fallback_analyzers import AnalyzerChain, build_fallback_analyzers
from formatters.khmer_formatter import KhmerFormatter
from telegram_notifier import TelegramNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("XAUUSD_News_Assistant")

class XAUUSDNewsAssistantBot:
    def __init__(self):
        self.gold_collector = GoldPriceCollector()
        self.calendar_collector = EconomicCalendarCollector()
        self.news_collector = BreakingNewsCollector()
        self.calendar_builder = CalendarImageBuilder()
        self.notifier = TelegramNotifier()
        self.analyzer = AnalyzerChain([GeminiAnalyzer()] + build_fallback_analyzers())
        if self.analyzer.is_available():
            names = [getattr(a, "name", a.__class__.__name__)
                     for a in self.analyzer.analyzers if a.is_available()]
            logger.info(f"AI analysis chain ENABLED: {' -> '.join(names)} -> rules")
        else:
            logger.info("No AI keys configured — using rule-based MacroAnalyzer fallback.")
        logger.info("Initializing XAUUSD News Assistant Bot (Cambodia Time UTC+7)...")

    def check_daily_gold_price(self):
        """Checks if daily gold price message needs to be sent and pinned."""
        now_kh = datetime.now(CAMBODIA_TZ)
        today_str = now_kh.strftime("%Y-%m-%d")

        # Check if already sent today
        if database.is_daily_price_sent(today_str):
            return

        # Trigger around scheduled hour (e.g. 07:00 AM Cambodia Time)
        if now_kh.hour >= DAILY_PRICE_ALERT_HOUR:
            logger.info(f"Triggering Daily Gold Price broadcast for {today_str}...")
            price_data = self.gold_collector.fetch_price()
            summary = self.analyzer.summarize_daily_price(price_data)
            msg = KhmerFormatter.format_daily_gold_price(price_data, summary=summary)
            
            # Send and Auto-Pin
            res = self.notifier.send_message(msg, auto_pin=True)
            msg_id = res.get("result", {}).get("message_id")
            database.record_daily_price_sent(today_str, msg_id)
            logger.info(f"Daily Gold Price successfully broadcasted and pinned (ID: {msg_id})")

    @staticmethod
    def _caption_fits(text: str, limit: int = 1024) -> bool:
        """Telegram captions are capped at 1024 characters (HTML tags not counted)."""
        return len(re.sub(r"<[^>]+>", "", text)) <= limit

    @staticmethod
    def _news_ts(item: dict) -> float:
        try:
            return parsedate_to_datetime(item.get("pub_date", "")).timestamp()
        except Exception:
            return 0.0

    @staticmethod
    def _fetch_news_image(item: dict) -> bytes:
        """Downloads the article's own image so the alert shows real news photo."""
        url = (item.get("image_url") or "").strip()
        if not url:
            return None
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if resp.status_code != 200:
                return None
            if not resp.headers.get("Content-Type", "").startswith("image/"):
                return None
            if len(resp.content) > 5_000_000:
                return None
            return resp.content
        except Exception as e:
            logger.warning(f"News image fetch failed: {e}")
            return None

    def _build_calendar_png(self) -> bytes:
        try:
            events = self.calendar_collector.fetch_day_events(datetime.now(CAMBODIA_TZ))
            if not events:
                return None
            return self.calendar_builder.build_day_png(events)
        except Exception as e:
            logger.warning(f"Calendar image build failed: {e}")
            return None

    def _attach_calendar_once(self):
        """Attaches today's calendar table image to at most one alert per cycle."""
        if self._calendar_attached:
            return
        self._calendar_attached = True
        png = self._build_calendar_png()
        if png:
            self.notifier.send_photo(
                png,
                caption=f"📅 <b>ប្រតិទិនសេដ្ឋកិច្ចថ្ងៃនេះ</b> — ម៉ោងកម្ពុជា (UTC+7)",
            )

    def check_economic_events(self) -> int:
        """
        Monitors economic calendar and triggers Mode 2 (Upcoming) and Mode 3 (Actual Release).
        Returns recommended sleep interval.
        """
        now_kh = datetime.now(CAMBODIA_TZ)
        events = self.calendar_collector.fetch_events()
        
        has_imminent_event = False
        has_waiting_actual = False

        for ev in events:
            ev_id = ev["id"]
            release_dt = ev["release_dt"]
            diff_seconds = (release_dt - now_kh).total_seconds()
            diff_minutes = int(diff_seconds // 60)

            # --- MODE 2: UPCOMING NEWS REMINDERS ---
            # 1. 10-15 Minutes Reminder
            if 0 < diff_minutes <= 15 and not database.is_event_stage_sent(ev_id, "upcoming_15m"):
                logger.info(f"Triggering 15m alert for {ev['title']}")
                msg = KhmerFormatter.format_upcoming_alert(ev, minutes_left=diff_minutes)
                self.notifier.send_message(msg)
                self._attach_calendar_once()
                database.record_event_stage(ev_id, ev["title"], ev["currency"], ev["release_time_str"], "upcoming_15m")
                has_imminent_event = True

            # 2. 5 Minutes Reminder
            if 0 < diff_minutes <= 5 and not database.is_event_stage_sent(ev_id, "upcoming_5m"):
                logger.info(f"Triggering 5m alert for {ev['title']}")
                msg = KhmerFormatter.format_upcoming_alert(ev, minutes_left=diff_minutes)
                self.notifier.send_message(msg)
                self._attach_calendar_once()
                database.record_event_stage(ev_id, ev["title"], ev["currency"], ev["release_time_str"], "upcoming_5m")
                has_imminent_event = True

            # If within 30 minutes, increase frequency
            if 0 <= diff_minutes <= 30:
                has_imminent_event = True

            # --- MODE 3: ACTUAL DATA RELEASE (FLASH ALERT) ---
            # If event time has arrived or passed (within last 4 hours)
            if -240 <= diff_minutes <= 0:
                actual_val = ev.get("actual", "").strip()
                if actual_val:
                    # Check if actual not already recorded
                    if not database.is_event_stage_sent(ev_id, "actual", actual_val):
                        logger.info(f"Triggering IMMEDIATE FLASH ALERT for {ev['title']} (Actual: {actual_val})")
                        analysis = self.analyzer.analyze_actual_vs_forecast(
                            ev["title"], actual_val, ev.get("forecast", ""), ev.get("previous", "")
                        )
                        msg = KhmerFormatter.format_actual_release_alert(ev, analysis)
                        self.notifier.send_message(msg)
                        self._attach_calendar_once()
                        database.record_event_stage(
                            ev_id, ev["title"], ev["currency"], ev["release_time_str"], 
                            "actual", actual_val=actual_val, forecast_val=ev.get("forecast", "")
                        )
                else:
                    # Event is past due, but Actual has not published yet -> Poll frequently
                    has_waiting_actual = True

        if has_waiting_actual:
            return INTERVAL_HIGH_IMPACT
        elif has_imminent_event:
            return INTERVAL_UPCOMING
        else:
            return INTERVAL_NORMAL

    def check_breaking_news(self):
        """
        Monitors RSS feeds for gold-relevant breaking news (Mode 1 / Mode 4).
        Deduplicated per item, and rate-limited to at most one alert per
        BREAKING_ALERT_MIN_GAP seconds (user spec: 1 alert per 2 hours).
        Items arriving inside a closed window are held and sent in a later one.
        """
        pending = []
        for item in self.news_collector.fetch_latest_news():
            news_id = item["id"]
            if database.is_news_sent(news_id):
                continue

            title = item["title"]
            desc = item.get("description", "")

            # Relevance Filter: Is this related to Gold/USD/Fed/Rates?
            if not GoldNewsFilter.is_gold_relevant(title, desc):
                continue
            pending.append(item)

        if not pending:
            return

        now = time.time()
        last_ts = float(database.get_state("last_breaking_alert_ts") or 0.0)
        if now - last_ts < BREAKING_ALERT_MIN_GAP:
            wait_min = int((BREAKING_ALERT_MIN_GAP - (now - last_ts)) // 60)
            logger.info(
                f"Breaking alert rate-limited: {len(pending)} item(s) held, "
                f"next alert allowed in ~{wait_min} min."
            )
            return

        item = max(
            pending,
            key=lambda it: (GoldNewsFilter.urgency_score(it["title"]), self._news_ts(it)),
        )
        title = item["title"]
        desc = item.get("description", "")
        logger.info(f"Sending breaking alert: {title}")
        analysis = self.analyzer.analyze_breaking_news(title, desc)
        msg = KhmerFormatter.format_breaking_event_alert(item, analysis)

        # One combined message: news photo (or calendar table) with the analysis as caption
        photo = self._fetch_news_image(item) or self._build_calendar_png()
        if photo and self._caption_fits(msg):
            res = self.notifier.send_photo(photo, caption=msg)
            sent_ok = bool(res.get("ok"))
            if sent_ok:
                self._calendar_attached = True
        else:
            if photo:
                self.notifier.send_photo(photo)
            res = self.notifier.send_message(msg)
            sent_ok = bool(res.get("ok"))

        if sent_ok:
            database.record_news_sent(item["id"], title, item.get("source", ""))
            database.set_state("last_breaking_alert_ts", str(time.time()))
        else:
            logger.error("Breaking alert send failed; item kept for retry next cycle.")

    def run_cycle(self) -> int:
        """Executes a single monitoring cycle and returns next sleep duration."""
        try:
            self._calendar_attached = False

            # 1. Daily Gold Price Check
            self.check_daily_gold_price()

            # 2. Breaking & Relevant Gold News Check
            self.check_breaking_news()

            # 3. Economic Calendar & Upcoming/Actual News Check
            recommended_interval = self.check_economic_events()
            return recommended_interval
        except Exception as e:
            logger.error(f"Error during bot execution cycle: {e}", exc_info=True)
            return 60

    def start_loop(self):
        """Main autonomous execution loop."""
        logger.info("Bot started in FULLY AUTONOMOUS RECEIVE-ONLY MODE.")
        while True:
            sleep_sec = self.run_cycle()
            logger.info(f"Cycle completed. Next check in {sleep_sec} seconds...")
            time.sleep(sleep_sec)

if __name__ == "__main__":
    bot = XAUUSDNewsAssistantBot()
    # Run 1 cycle immediately on launch
    interval = bot.run_cycle()
    print(f"\n[XAUUSD Assistant] Single cycle completed successfully. Recommended interval: {interval}s")
    print("[XAUUSD Assistant] To keep running indefinitely, invoke start_loop().")
