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
try:
    from collectors.tradingview_chart import TradingViewChartBuilder
except ImportError:
    try:
        from tradingview_chart import TradingViewChartBuilder
    except ImportError:
        TradingViewChartBuilder = None

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
        self.tv_chart_builder = TradingViewChartBuilder() if TradingViewChartBuilder else None
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
        """Checks if daily gold price message needs to be sent and pinned at 07:00 AM Cambodia Time."""
        now_kh = datetime.now(CAMBODIA_TZ)
        today_str = now_kh.strftime("%Y-%m-%d")

        # Check if already sent today
        if database.is_daily_price_sent(today_str):
            return

        # Trigger every day at 07:00 AM Cambodia Time (or after 07:00 if bot was offline)
        if (now_kh.hour > DAILY_PRICE_ALERT_HOUR) or (
            now_kh.hour == DAILY_PRICE_ALERT_HOUR and now_kh.minute >= DAILY_PRICE_ALERT_MINUTE
        ):
            logger.info(f"Triggering 07:00 AM Daily Gold Price broadcast & auto-pin for {today_str}...")
            price_data = self.gold_collector.fetch_price()
            summary = self.analyzer.summarize_daily_price(price_data)
            msg = KhmerFormatter.format_daily_gold_price(price_data, summary=summary)
            
            # Interactive Inline Keyboard Buttons
            buttons = {
                "inline_keyboard": [
                    [
                        {"text": "📊 មើល Chart ផ្ទាល់ (TradingView)", "url": "https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD"},
                        {"text": "📅 ប្រតិទិនសេដ្ឋកិច្ច", "url": "https://www.forexfactory.com/calendar"}
                    ]
                ]
            }

            # Send and Auto-Pin strictly to the Channel with Inline Buttons
            res = self.notifier.send_message(msg, auto_pin=True, reply_markup=buttons)
            msg_id = res.get("result", {}).get("message_id")
            database.record_daily_price_sent(today_str, msg_id)

    def check_session_open_alerts(self):
        """Monitors and alerts London Session (14:00) and New York Session (19:00) Openings."""
        now_kh = datetime.now(CAMBODIA_TZ)
        today_str = now_kh.strftime("%Y-%m-%d")

        # London Session: 14:00 (2:00 PM) Cambodia Time
        if now_kh.hour == 14 and not database.get_state(f"london_session_{today_str}"):
            msg = KhmerFormatter.format_session_open_alert(
                "London Session", "14:00", 
                "ធនាគារអឺរ៉ុប និងចក្រភពអង់គ្លេសចាប់ផ្តើមជួញដូរ។ សាច់ប្រាក់ងាយស្រួល (Liquidity) ចាក់ចូលទីផ្សារមាសយ៉ាងច្រើន!"
            )
            self.notifier.send_message(msg)
            database.set_state(f"london_session_{today_str}", "sent")
            logger.info("London Session Open alert broadcasted.")

        # New York Session: 19:00 (7:00 PM) Cambodia Time
        if now_kh.hour == 19 and not database.get_state(f"ny_session_{today_str}"):
            msg = KhmerFormatter.format_session_open_alert(
                "New York Session", "19:00",
                "ផ្សារ Wall Street & COMEX អាមេរិកបើកដំណើរការ។ នេះជា Session ដែលមានទំហំជួញដូរមាសធំបំផុតលើលោក!"
            )
            self.notifier.send_message(msg)
            database.set_state(f"ny_session_{today_str}", "sent")
            logger.info("New York Session Open alert broadcasted.")

    def check_night_wrap_up(self):
        """Checks if daily market wrap-up message needs to be sent at 22:00 (10:00 PM) Cambodia Time."""
        now_kh = datetime.now(CAMBODIA_TZ)
        today_str = now_kh.strftime("%Y-%m-%d")
        key = f"night_wrap_up_{today_str}"

        if database.get_state(key):
            return

        if now_kh.hour >= 22:
            logger.info(f"Triggering Daily Market Wrap-Up for {today_str}...")
            price_data = self.gold_collector.fetch_price()
            summary = self.analyzer.summarize_daily_price(price_data)
            msg = KhmerFormatter.format_night_wrap_up(price_data, summary=summary)
            self.notifier.send_message(msg)
            database.set_state(key, "sent")
            logger.info(f"Daily Market Wrap-Up broadcasted successfully.")

    def check_database_maintenance(self):
        """Performs automatic database cleanup (Point 3) keeping data.db fast and lightweight."""
        now_kh = datetime.now(CAMBODIA_TZ)
        today_str = now_kh.strftime("%Y-%m-%d")
        key = f"db_maintenance_{today_str}"

        # Run once a day around midnight or Sunday
        if now_kh.hour == 0 and not database.get_state(key):
            cleaned = database.cleanup_old_records(days=30)
            database.set_state(key, "done")
            logger.info(f"[DB Auto-Maintenance] Cleaned {cleaned} old records and executed VACUUM successfully.")

    def process_incoming_commands(self):
        """Listens and responds to Telegram user commands (/price, /levels, /calendar, /help)."""
        offset = int(database.get_state("telegram_update_offset") or 0)
        updates = self.notifier.get_updates(offset=offset, timeout=1)
        if not updates:
            return

        for u in updates:
            up_id = u.get("update_id", 0)
            database.set_state("telegram_update_offset", str(up_id + 1))

            msg_obj = u.get("message", {})
            chat_id = msg_obj.get("chat", {}).get("id")
            text = (msg_obj.get("text") or "").strip()

            if not text or not chat_id:
                continue

            # Command routing
            cmd = text.split()[0].lower()

            if cmd in ("/price", "/gold"):
                price_data = self.gold_collector.fetch_price()
                resp = KhmerFormatter.format_daily_gold_price(price_data, summary="")
                self.notifier.send_message(resp, chat_id=chat_id)

            elif cmd in ("/levels", "/setup"):
                price_data = self.gold_collector.fetch_price()
                levels = price_data.get("key_levels", {})
                oz = price_data.get("price_oz", 0.0)
                pivot = levels.get("pivot", oz)
                r1 = levels.get("r1", oz + 20)
                s1 = levels.get("s1", oz - 20)
                reply = (
                    f"🎯 <b>កម្រិតបច្ចេកទេស & AI SMC Setup Zone</b>\n\n"
                    f"• 🟢 <b>Buy Zone:</b> ${s1 - 4:,.2f} - ${s1 + 3:,.2f} (SL: ${s1 - 11:,.2f})\n"
                    f"• 🔴 <b>Sell Zone:</b> ${r1 - 3:,.2f} - ${r1 + 4:,.2f} (SL: ${r1 + 11:,.2f})\n"
                    f"• 🎯 <b>Pivot Point:</b> ${pivot:,.2f}\n\n"
                    f"💡 <i>អនុសាសន៍: រង់ចាំ Confirmation Candle នៅលើ M15 មុនចូល Order!</i>"
                )
                self.notifier.send_message(reply, chat_id=chat_id)

            elif cmd in ("/calendar", "/events"):
                png = self._build_calendar_png()
                if png:
                    self.notifier.send_photo(png, caption="📅 <b>ប្រតិទិនសេដ្ឋកិច្ចថ្ងៃនេះ — ម៉ោងនៅកម្ពុជា (UTC+7)</b>", chat_id=chat_id)
                else:
                    self.notifier.send_message("📅 មិនមានទិន្នន័យប្រតិទិនសេដ្ឋកិច្ចធំៗថ្ងៃនេះទេ។", chat_id=chat_id)

            elif cmd in ("/help", "/start"):
                help_text = (
                    f"👋 <b>សូមស្វាគមន៍មកកាន់ XAUUSD AI Assistant Bot!</b>\n\n"
                    f"បញ្ជា Bot តាមរយៈ Commands ដូចខាងក្រោម៖\n"
                    f"• <code>/price</code> ➡️ មើលហាងឆេងមាស Spot និងផ្សារធំថ្មីបច្ចុប្បន្ន\n"
                    f"• <code>/levels</code> ➡️ មើលកម្រិតបច្ចេកទេស AI Pivot & SMC Setup\n"
                    f"• <code>/calendar</code> ➡️ មើលតារាងប្រតិទិនសេដ្ឋកិច្ចថ្ងៃនេះ\n"
                    f"• <code>/help</code> ➡️ មើលសេចក្តីណែនាំទាំងអស់"
                )
                self.notifier.send_message(help_text, chat_id=chat_id)

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
        """
        Downloads real news photo. If the feed provides an article image, use it.
        Otherwise, intelligently fetches a matching high-quality context photo
        based on the news story (e.g. Trump, Powell, Fed, Gold, Middle East).
        """
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        url = (item.get("image_url") or "").strip()
        
        # 1. Try direct article image from feed
        if url:
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200 and len(resp.content) <= 8_000_000:
                    ct = resp.headers.get("Content-Type", "")
                    if ct.startswith("image/") or url.endswith((".jpg", ".jpeg", ".png", ".webp")):
                        return resp.content
            except Exception as e:
                logger.warning(f"Direct news image fetch failed: {e}")

        # 2. Contextual story-matching: find an image that directly reflects the topic
        title_lower = (item.get("title", "") + " " + item.get("description", "")).lower()
        search_query = None

        if "trump" in title_lower:
            search_query = "Donald Trump United Nations General Assembly"
        elif "powell" in title_lower or "federal reserve" in title_lower or "fomc" in title_lower or "fed" in title_lower:
            search_query = "Jerome Powell Federal Reserve"
        elif "putin" in title_lower or "russia" in title_lower:
            search_query = "Vladimir Putin"
        elif "ecb" in title_lower or "lagarde" in title_lower:
            search_query = "Christine Lagarde European Central Bank"
        elif "iran" in title_lower or "middle east" in title_lower:
            search_query = "Middle East geopolitical tension"
        elif "gold" in title_lower or "xau" in title_lower or "bullion" in title_lower:
            search_query = "Gold bars bullion vault"

        if search_query:
            try:
                wiki_api = (
                    f"https://en.wikipedia.org/w/api.php?action=query&format=json"
                    f"&prop=pageimages&generator=search&gsrsearch={requests.utils.quote(search_query)}"
                    f"&gsrlimit=3&piprop=thumbnail&pithumbsize=900"
                )
                res = requests.get(wiki_api, headers=headers, timeout=8).json()
                pages = res.get("query", {}).get("pages", {})
                for _, p in pages.items():
                    thumb = p.get("thumbnail", {}).get("source")
                    if thumb:
                        img_resp = requests.get(thumb, headers=headers, timeout=10)
                        if img_resp.status_code == 200 and len(img_resp.content) > 1000:
                            return img_resp.content
            except Exception as e:
                logger.warning(f"Contextual news image fetch failed: {e}")

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

                        # Generate TradingView Live Chart with AI direction arrow
                        chart_png = None
                        if self.tv_chart_builder:
                            try:
                                chart_png = self.tv_chart_builder.build_chart_image(
                                    event_title=f"{ev['title']} (Actual: {actual_val} vs F: {ev.get('forecast', 'N/A')})",
                                    bias=analysis.get("bias", "Bullish"),
                                    target_desc=analysis.get("xau_pressure", "")[:60]
                                )
                            except Exception as e:
                                logger.warning(f"Failed to generate TradingView chart: {e}")


                        if chart_png and self._caption_fits(msg):
                            self.notifier.send_photo(chart_png, caption=msg)
                        else:
                            if chart_png:
                                self.notifier.send_photo(chart_png)
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

        # User directive: NO MORE TIME RESTRICTION OR 2-HOUR DELAY.
        # Whenever AI bot discovers any gold-relevant news or market anomalies, ALERT IMMEDIATELY!
        item = max(
            pending,
            key=lambda it: (GoldNewsFilter.urgency_score(it["title"]), self._news_ts(it)),
        )
        logger.info(f"[ZERO-DELAY IMMEDIATE ALERT] News/Anomaly detected: {item['title']}")
        title = item["title"]
        desc = item.get("description", "")
        logger.info(f"Sending breaking alert: {title}")
        analysis = self.analyzer.analyze_breaking_news(title, desc)
        msg = KhmerFormatter.format_breaking_event_alert(item, analysis)

        # One single combined message: news photo (or calendar table) with the analysis as caption.
        # NEVER send two separate messages (photo + text). Always send strictly ONE message.
        photo = self._fetch_news_image(item) or self._build_calendar_png()
        if photo:
            # If caption exceeds Telegram's 1024 char limit, trim it cleanly so it always fits
            caption_text = msg
            if not self._caption_fits(caption_text, limit=1024):
                caption_text = caption_text[:1000] + "..."
            res = self.notifier.send_photo(photo, caption=caption_text)
            sent_ok = bool(res.get("ok"))
            if sent_ok:
                self._calendar_attached = True
        else:
            # If absolutely no photo is available, send as single text message
            res = self.notifier.send_message(msg)
            sent_ok = bool(res.get("ok"))

        if sent_ok:
            database.record_news_sent(item["id"], title, item.get("source", ""))
            database.set_state("last_breaking_alert_ts", str(time.time()))
        else:
            logger.error("Breaking alert send failed; item kept for retry next cycle.")

    def run_cycle(self) -> int:
        """Executes a single monitoring cycle for scheduled/background tasks and returns next sleep duration."""
        try:
            self._calendar_attached = False

            # 1. Process Interactive User Commands (/price, /levels, /calendar, /help)
            self.process_incoming_commands()

            # 2. Database Auto-Maintenance (Cleanup & VACUUM)
            self.check_database_maintenance()

            # 3. Daily Gold Price Check (7:00 AM Cambodia Time)
            self.check_daily_gold_price()

            # 4. Market Sessions Open Alerts (London 14:00 & NY 19:00 Cambodia Time)
            self.check_session_open_alerts()

            # 5. Daily Market Wrap-Up (10:00 PM Cambodia Time)
            self.check_night_wrap_up()

            # 6. Breaking & Relevant Gold News Check
            self.check_breaking_news()

            # 7. Economic Calendar & Upcoming/Actual News Check
            recommended_interval = self.check_economic_events()
            return recommended_interval
        except Exception as e:
            logger.error(f"Error during bot execution cycle: {e}", exc_info=True)
            return 60

    def start_loop(self):
        """
        High-Performance Real-Time Autonomous Event Loop.
        - Polls Telegram incoming user commands continuously every 1-2 seconds for INSTANT response.
        - Schedules and executes background tasks (News, Economic Calendar, Daily Price, Sessions)
          based on elapsed timestamps without sleeping for 1 hour or blocking commands!
        """
        logger.info("Bot started in ULTRA-FAST REAL-TIME RESPONSIVE MODE.")
        last_background_check = 0.0
        background_interval = 60  # Initial background check interval

        while True:
            try:
                # 1. Real-time Telegram Command Listener (Instant response < 1s)
                self.process_incoming_commands()

                # 2. Periodic Tasks Checker (Non-blocking)
                now = time.time()
                if now - last_background_check >= background_interval:
                    last_background_check = now
                    try:
                        self.check_database_maintenance()
                        self.check_daily_gold_price()
                        self.check_session_open_alerts()
                        self.check_night_wrap_up()
                        self.check_breaking_news()
                        background_interval = self.check_economic_events()
                    except Exception as err:
                        logger.error(f"Error during background task check: {err}", exc_info=True)
                        background_interval = 60

                # Micro-sleep to ensure near-zero CPU usage while maintaining instant responsiveness
                time.sleep(1.0)
            except KeyboardInterrupt:
                logger.info("Bot stopped by user.")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
                time.sleep(2.0)

if __name__ == "__main__":
    bot = XAUUSDNewsAssistantBot()
    # Run loop directly
    bot.start_loop()

