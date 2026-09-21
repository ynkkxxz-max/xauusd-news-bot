import time
import logging
from datetime import datetime
import pytz

from config import (
    CAMBODIA_TZ, DAILY_PRICE_ALERT_HOUR, DAILY_PRICE_ALERT_MINUTE,
    INTERVAL_NORMAL, INTERVAL_UPCOMING, INTERVAL_HIGH_IMPACT
)
import database
from collectors.gold_price import GoldPriceCollector
from collectors.economic_calendar import EconomicCalendarCollector
from collectors.breaking_news import BreakingNewsCollector
from analyzers.gold_filter import GoldNewsFilter
from analyzers.gemini_analyzer import GeminiAnalyzer
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
        self.notifier = TelegramNotifier()
        self.analyzer = GeminiAnalyzer()
        if self.analyzer.is_available():
            logger.info("Gemini AI analysis ENABLED (natural-language Khmer market analysis).")
        else:
            logger.info("Gemini not configured — using rule-based MacroAnalyzer fallback.")
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
                database.record_event_stage(ev_id, ev["title"], ev["currency"], ev["release_time_str"], "upcoming_15m")
                has_imminent_event = True

            # 2. 5 Minutes Reminder
            if 0 < diff_minutes <= 5 and not database.is_event_stage_sent(ev_id, "upcoming_5m"):
                logger.info(f"Triggering 5m alert for {ev['title']}")
                msg = KhmerFormatter.format_upcoming_alert(ev, minutes_left=diff_minutes)
                self.notifier.send_message(msg)
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
        Monitors RSS feeds for Mode 1 (hourly news) and Mode 4 (immediate breaking news).
        Uses deduplication to avoid spamming.
        """
        news_items = self.news_collector.fetch_latest_news()
        for item in news_items:
            news_id = item["id"]
            if database.is_news_sent(news_id):
                continue

            title = item["title"]
            desc = item.get("description", "")

            # 1. Relevance Filter: Is this related to Gold/USD/Fed/Rates?
            if not GoldNewsFilter.is_gold_relevant(title, desc):
                continue

            # 2. Check if Breaking / High-Impact (Mode 4)
            is_urgent = GoldNewsFilter.is_breaking_or_high_impact(title)
            
            logger.info(f"Processing gold-relevant news: {title} (Urgent: {is_urgent})")
            analysis = self.analyzer.analyze_breaking_news(title, desc)
            msg = KhmerFormatter.format_breaking_event_alert(item, analysis)

            # Send alert
            self.notifier.send_message(msg)
            database.record_news_sent(news_id, title, item.get("source", ""))

    def run_cycle(self) -> int:
        """Executes a single monitoring cycle and returns next sleep duration."""
        try:
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
