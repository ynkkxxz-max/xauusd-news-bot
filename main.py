import os
import re
import html
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
try:
    from gold_price import GoldPriceCollector
except ImportError:
    from collectors.gold_price import GoldPriceCollector

try:
    from economic_calendar import EconomicCalendarCollector
except ImportError:
    from collectors.economic_calendar import EconomicCalendarCollector

try:
    from breaking_news import BreakingNewsCollector
except ImportError:
    from collectors.breaking_news import BreakingNewsCollector

try:
    from calendar_image import CalendarImageBuilder
except ImportError:
    from collectors.calendar_image import CalendarImageBuilder

try:
    from tradingview_chart import TradingViewChartBuilder
except ImportError:
    try:
        from collectors.tradingview_chart import TradingViewChartBuilder
    except ImportError:
        TradingViewChartBuilder = None

try:
    from gold_filter import GoldNewsFilter
except ImportError:
    from analyzers.gold_filter import GoldNewsFilter

try:
    from gemini_analyzer import GeminiAnalyzer
except ImportError:
    from analyzers.gemini_analyzer import GeminiAnalyzer

try:
    from fallback_analyzers import AnalyzerChain, build_fallback_analyzers
except ImportError:
    from analyzers.fallback_analyzers import AnalyzerChain, build_fallback_analyzers

try:
    from macro_analyzer import MacroAnalyzer
except ImportError:
    from analyzers.macro_analyzer import MacroAnalyzer

try:
    from khmer_formatter import KhmerFormatter
except ImportError:
    from formatters.khmer_formatter import KhmerFormatter

try:
    from candlestick_analyzer import CandlestickPatternAnalyzer
except ImportError:
    from analyzers.candlestick_analyzer import CandlestickPatternAnalyzer

try:
    from cot_collector import CotCollector
except ImportError:
    from collectors.cot_collector import CotCollector

try:
    from macro_correlation import MarketMacroCorrelation
except ImportError:
    from collectors.macro_correlation import MarketMacroCorrelation

try:
    from khmer_voice import KhmerVoiceSynthesizer
except ImportError:
    from collectors.khmer_voice import KhmerVoiceSynthesizer

try:
    from order_book_tracker import OrderBookDepthTracker
except ImportError:
    from collectors.order_book_tracker import OrderBookDepthTracker

try:
    from fomc_interpreter import FomcSpeechInterpreter
except ImportError:
    from analyzers.fomc_interpreter import FomcSpeechInterpreter

try:
    from heatmap_builder import LiquidityHeatmapBuilder
except ImportError:
    from collectors.heatmap_builder import LiquidityHeatmapBuilder

try:
    from risk_calculator import RiskLotCalculator
except ImportError:
    from collectors.risk_calculator import RiskLotCalculator

try:
    from collectors.gold_price_card import DailyGoldPriceCardBuilder
except ImportError:
    try:
        from gold_price_card import DailyGoldPriceCardBuilder
    except ImportError:
        DailyGoldPriceCardBuilder = None

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
        self.candle_analyzer = CandlestickPatternAnalyzer()
        self.cot_collector = CotCollector()
        self.macro_collector = MarketMacroCorrelation()
        self.voice_synth = KhmerVoiceSynthesizer()
        self.order_book_tracker = OrderBookDepthTracker()
        self.fomc_interpreter = FomcSpeechInterpreter()
        self.heatmap_builder = LiquidityHeatmapBuilder()
        self.gold_card_builder = DailyGoldPriceCardBuilder() if DailyGoldPriceCardBuilder else None
        self.notifier = TelegramNotifier()

        self.analyzer = AnalyzerChain([GeminiAnalyzer()] + build_fallback_analyzers())
        if self.analyzer.is_available():
            names = [getattr(a, "name", a.__class__.__name__)
                     for a in self.analyzer.analyzers if a.is_available()]
            logger.info(f"AI analysis chain ENABLED: {' -> '.join(names)} -> rules")
        else:
            logger.info("No AI keys configured — using rule-based MacroAnalyzer fallback.")
        logger.info("Initializing XAUUSD News Assistant Bot (Cambodia Time UTC+7)...")
        self._calendar_attached = False
        self._session_alert_locks = set()
        self._daily_price_locks = set()
        self._broadcasted_titles_cache = set()
        now_ts = time.time()
        saved_last_alert = float(database.get_state("last_breaking_alert_ts") or "0")
        if saved_last_alert > 0:
            self._last_breaking_sent_ts = saved_last_alert
        else:
            self._last_breaking_sent_ts = now_ts - BREAKING_ALERT_MIN_GAP
            try:
                database.set_state("last_breaking_alert_ts", str(self._last_breaking_sent_ts))
            except Exception:
                pass

        # Bind HTTP health check port & self-pinger if running on Render / Railway
        port_env = os.getenv("PORT")
        if port_env:
            try:
                self._start_http_health_server(int(port_env))
                self._start_self_pinger()
            except Exception as e:
                logger.warning(f"Could not start HTTP health server on port {port_env}: {e}")

        self._bootstrap_news_cache()

    def _start_self_pinger(self):
        """Pings public URL every 8 minutes to prevent Render Free Tier from idling or sleeping."""
        try:
            import threading
            import urllib.request
            def pinger_worker():
                url = os.getenv("RENDER_EXTERNAL_URL", "https://xauusd-news-bot-kh.onrender.com")
                time.sleep(30)
                while True:
                    try:
                        req = urllib.request.Request(url, headers={"User-Agent": "Render-Internal-KeepAlive/1.0"})
                        with urllib.request.urlopen(req, timeout=25) as resp:
                            pass
                    except Exception:
                        pass
                    time.sleep(480)
            t = threading.Thread(target=pinger_worker, daemon=True, name="Keep-Alive-Pinger")
            t.start()
            logger.info("[Cloud Self-Pinger] Started background keep-alive loop (8-min cadence).")
        except Exception as e:
            logger.warning(f"[Cloud Self-Pinger] Could not start: {e}")

    def _start_http_health_server(self, port: int = 10000):
        """Starts a lightweight HTTP server so Cloud platforms (Render, Railway, cron-job.org) know the app is alive."""
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler
            import threading
            class HealthHandler(BaseHTTPRequestHandler):
                def do_HEAD(self):
                    self.send_response(200)
                    self.send_header("Content-type", "text/plain")
                    self.send_header("Content-length", "2")
                    self.end_headers()
                def do_GET(self):
                    self.send_response(200)
                    self.send_header("Content-type", "text/plain; charset=utf-8")
                    self.send_header("Content-length", "2")
                    self.end_headers()
                    self.wfile.write(b"OK")
                def log_message(self, format, *args):
                    pass
            server = HTTPServer(("0.0.0.0", port), HealthHandler)
            t = threading.Thread(target=server.serve_forever, daemon=True, name="HTTP-Health")
            t.start()
            logger.info(f"[Cloud Health Server] Successfully listening on port {port} (Zero-Restart Shield).")
        except Exception as e:
            logger.warning(f"[Cloud Health Server] Warning on port {port}: {e}")

    def _fetch_channel_html(self, max_cache_age: float = 30.0) -> str:
        """Caches public Telegram channel feed HTML for 30s to prevent spamming Telegram web and lagging the event loop."""
        now = time.time()
        if hasattr(self, "_cached_channel_html") and self._cached_channel_html:
            if now - getattr(self, "_cached_channel_html_ts", 0) < max_cache_age:
                return self._cached_channel_html
        try:
            import urllib.request
            req = urllib.request.Request(
                "https://t.me/s/GoldMarketKH8888",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                self._cached_channel_html = html
                self._cached_channel_html_ts = now
                return html
        except Exception as e:
            logger.debug(f"[Channel HTML Fetch] {e}")
            return getattr(self, "_cached_channel_html", "")

    def _bootstrap_news_cache(self):
        """
        On startup, seeds existing headlines that are either older than 4 hours
        or ALREADY posted to the Telegram channel feed, so only fresh, unposted news
        is processed for breaking alerts. Uses cached channel HTML for sub-second execution.
        """
        try:
            items = self.news_collector.fetch_latest_news()
            bootstrapped_count = 0
            now = time.time()
            channel_html = self._fetch_channel_html()
            for item in items:
                news_id = item.get("id")
                title = (item.get("title") or "").strip()
                link = item.get("link", "")
                item_ts = self._news_ts(item)
                
                # Check if truly stale (> 4h) or already posted to @GoldMarketKH8888
                is_stale = item_ts > 0 and (now - item_ts) > 4 * 3600
                is_in_channel = self._is_already_in_telegram_channel(title, link) if channel_html else False
                
                if is_stale or is_in_channel:
                    if title:
                        self._broadcasted_titles_cache.add(title.lower())
                    self.news_collector.clear_item(news_id=news_id, link=link, title=title)
                    if news_id and not database.is_news_sent(news_id):
                        database.record_news_sent(news_id, title, item.get("source", ""), is_broadcasted=1 if is_in_channel else 0)
                    bootstrapped_count += 1
            logger.info(f"[Startup News Sync] Seeded {bootstrapped_count} stale/already-sent headlines from data in sub-second time.")
        except Exception as e:
            logger.warning(f"[Startup News Sync] Warning: {e}")

    def _is_daily_price_already_in_channel(self, date_str: str) -> bool:
        """Inspects live channel feed to verify if today's daily gold price was already broadcasted."""
        try:
            import urllib.request
            req = urllib.request.Request(
                "https://t.me/s/GoldMarketKH8888",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                channel_html = resp.read().decode("utf-8", errors="ignore")
            # If today's date formatted (e.g. 02/10/2026) is already in channel, return True
            if date_str in channel_html:
                return True
        except Exception as e:
            logger.debug(f"[Channel Gold Price Check] {e}")
        return False

    def check_daily_gold_price(self):
        """Checks if daily gold price message needs to be sent at 07:00 AM Cambodia Time (strictly once per day)."""
        now_kh = datetime.now(CAMBODIA_TZ)
        today_str = now_kh.strftime("%Y-%m-%d")
        date_display_str = now_kh.strftime("%d/%m/%Y")

        # 1. In-memory lock guard
        if today_str in self._daily_price_locks:
            return

        # 2. Database SQLite persistence guard
        if database.is_daily_price_sent(today_str):
            self._daily_price_locks.add(today_str)
            return

        # 3. Live Telegram Channel Feed Verification Guard (survives zero-database cloud reboots)
        if self._is_daily_price_already_in_channel(date_display_str):
            logger.info(f"[Daily Gold Price] Already verified in channel feed for {today_str}. Locking today.")
            database.record_daily_price_sent(today_str, 0)
            self._daily_price_locks.add(today_str)
            return

        # Trigger STRICTLY at 07:00 AM Cambodia Time (07:00 - 07:15 AM only)
        if now_kh.hour == DAILY_PRICE_ALERT_HOUR and now_kh.minute <= 15 and now_kh.minute >= DAILY_PRICE_ALERT_MINUTE:
            self._daily_price_locks.add(today_str)
            logger.info(f"Triggering 07:00 AM Daily Gold Price broadcast for {today_str}...")
            price_data = self.gold_collector.fetch_price(force_refresh=True)
            
            # Render Ultra-HD Graphic Card per user design specification
            card_png = self.gold_card_builder.build_card_png(price_data) if self.gold_card_builder else None
            if card_png:
                res = self.notifier.send_photo(card_png, caption="", reply_markup=None)
            else:
                msg = KhmerFormatter.format_daily_gold_price(price_data)
                res = self.notifier.send_message(msg, auto_pin=False, reply_markup=None)

            msg_id = res.get("result", {}).get("message_id")
            database.record_daily_price_sent(today_str, msg_id)
            logger.info(f"Daily Gold Price broadcast completed for {today_str} (msg_id: {msg_id}).")

    def _is_session_alert_sent(self, key: str) -> bool:
        if key in self._session_alert_locks:
            return True
        if database.get_state(key):
            self._session_alert_locks.add(key)
            return True
        return False

    def _mark_session_alert_sent(self, key: str):
        self._session_alert_locks.add(key)
        try:
            database.set_state(key, "sent")
        except Exception as e:
            logger.warning(f"Could not persist session state {key}: {e}")

    def check_session_open_alerts(self):
        """
        Monitors and alerts London Session (14:00) and New York Session (19:00) Openings.
        Strictly armed with 4-Tier Zero-Spam Protection:
        1. Minute window guard (only first 10 minutes: 14:00-14:10 or 19:00-19:10)
        2. In-memory Set lock (instant, survives any within-process loops)
        3. Pre-send lock acquisition (locked BEFORE calling Telegram API)
        4. SQLite WAL persistence
        """
        now_kh = datetime.now(CAMBODIA_TZ)
        today_str = now_kh.strftime("%Y-%m-%d")

        # London Session: 14:00 (2:00 PM) Cambodia Time (strictly 14:00 - 14:10)
        london_key = f"london_session_{today_str}"
        if now_kh.hour == 14 and now_kh.minute <= 10 and not self._is_session_alert_sent(london_key):
            # Lock IMMEDIATELY before generating / sending to prevent concurrent loops
            self._mark_session_alert_sent(london_key)
            try:
                price_data = self.gold_collector.fetch_price()
                order_book = self.order_book_tracker.fetch_order_book_depth()
                msg = KhmerFormatter.format_session_open_alert(
                    "London Session", "14:00",
                    price_data=price_data,
                    order_book=order_book
                )
                heatmap_png = self.heatmap_builder.generate_heatmap_png(price_data, order_book)
                if heatmap_png:
                    self.notifier.send_photo(heatmap_png, caption=msg)
                else:
                    self.notifier.send_message(msg)
                logger.info("London Session Open alert + Heatmap broadcasted.")
            except Exception as e:
                logger.error(f"Error broadcasting London Session Open alert: {e}")

        # New York Session: 19:00 (7:00 PM) Cambodia Time (strictly 19:00 - 19:10)
        ny_key = f"ny_session_{today_str}"
        if now_kh.hour == 19 and now_kh.minute <= 10 and not self._is_session_alert_sent(ny_key):
            # Lock IMMEDIATELY before generating / sending to prevent concurrent loops
            self._mark_session_alert_sent(ny_key)
            try:
                price_data = self.gold_collector.fetch_price()
                order_book = self.order_book_tracker.fetch_order_book_depth()
                msg = KhmerFormatter.format_session_open_alert(
                    "New York Session", "19:00",
                    price_data=price_data,
                    order_book=order_book
                )
                heatmap_png = self.heatmap_builder.generate_heatmap_png(price_data, order_book)
                if heatmap_png:
                    self.notifier.send_photo(heatmap_png, caption=msg)
                else:
                    self.notifier.send_message(msg)
                logger.info("New York Session Open alert + Heatmap broadcasted.")
            except Exception as e:
                logger.error(f"Error broadcasting New York Session Open alert: {e}")



    def check_candlestick_confirmation(self):
        """
        Monitors M15 candlestick confirmations when price arrives at SMC Key Zones.
        Sends actionable Buy/Sell Confirmation Alerts when Pin Bar or Engulfing candle completes.
        """
        now = time.time()
        last_conf = float(database.get_state("last_candle_conf_ts") or 0.0)
        if now - last_conf < 2700:  # 45-minute cooldown between confirmation alerts
            return

        price_data = self.gold_collector.fetch_price()
        current_price = price_data.get("price_oz", 0.0)
        levels = price_data.get("key_levels", {})
        oz = current_price
        pivot = levels.get("pivot", oz)
        r1 = levels.get("r1", oz + 20)
        s1 = levels.get("s1", oz - 20)

        buy_zone = (s1 - 4, s1 + 3)
        sell_zone = (r1 - 3, r1 + 4)

        DAILY_MAX_SIGNALS = 5
        if not database.can_issue_signal_today(DAILY_MAX_SIGNALS):
            return

        now_kh = datetime.now(CAMBODIA_TZ)
        hour_kh = now_kh.hour
        # Signals strictly cut off at 22:00 (10:00 PM) Cambodia Time
        is_active_session = (14 <= hour_kh < 18) or (19 <= hour_kh < 22)
        if not is_active_session:
            return

        conf = self.candle_analyzer.detect_confirmation(current_price, buy_zone, sell_zone)
        if conf:
            # Audit setup through AI to guarantee Grade A+ accuracy
            macro_data = self.macro_collector.fetch_macro_correlations()
            order_book = self.order_book_tracker.fetch_order_book_depth()
            raw_conf_sig = {
                "action": "BUY" if "BULLISH" in conf.get("type", "") else "SELL",
                "entry": conf.get("entry", current_price),
                "sl": conf.get("sl"),
                "tp1": conf.get("tp"),
                "tp2": conf.get("tp2", conf.get("tp")),
                "pattern": conf.get("pattern", "Candlestick Confirmation"),
                "reason": conf.get("desc", "")
            }
            ai_audit = self.analyzer.analyze_and_validate_sniper_signal(
                raw_signal=raw_conf_sig,
                current_price=current_price,
                key_levels=levels,
                macro_data=macro_data,
                order_book=order_book
            )
            if not ai_audit or not ai_audit.get("approved"):
                logger.info(f"[CANDLE CONF REJECTED BY AI] Audit failed or low confluence: {ai_audit.get('rejection_reason') if ai_audit else 'No response'}")
                return

            if not database.can_issue_signal_today(DAILY_MAX_SIGNALS):
                return

            new_daily_c = database.increment_daily_signal_count()
            conf["daily_count"] = new_daily_c
            conf["daily_max"] = DAILY_MAX_SIGNALS
            logger.info(f"[CANDLESTICK CONFIRMATION DETECTED & AI APPROVED] {conf['pattern']} at {conf['zone_name']} | Daily Position: {new_daily_c}/{DAILY_MAX_SIGNALS}")
            msg = KhmerFormatter.format_candlestick_confirmation(conf)
            
            # Render chart image for visual confirmation
            candles = self.candle_analyzer.fetch_m15_candles(count=35)
            chart_png = self.chart_renderer.render_candlestick_chart(
                candles=candles,
                current_price=current_price,
                key_levels=levels,
                setup={"entry": conf.get("entry", current_price), "sl": conf.get("sl"), "tp1": conf.get("tp")},
                timeframe="M15",
                title_extra=conf.get("pattern", "")
            )
            # Direct Signal Alert via Private Bot DM ONLY (Never sent to public channel)
            subscribers = database.get_signal_subscribers()
            admin_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
            if admin_id and admin_id.isdigit():
                subscribers = list(set(subscribers + [int(admin_id)]))

            for sub_id in subscribers:
                try:
                    if chart_png:
                        self.notifier.send_photo(chart_png, caption=self._truncate_html_caption(msg, 950), chat_id=sub_id)
                    else:
                        self.notifier.send_message(msg, chat_id=sub_id)
                except Exception as e:
                    logger.warning(f"[Private Signal DM] Error sending to {sub_id}: {e}")

            database.set_state("last_candle_conf_ts", str(now))

    def check_news_danger_zone(self):
        """
        AI Market Regime & High-Impact News Filter:
        Monitors if market is within 30 minutes of a High-Impact USD release (CPI, NFP, FOMC).
        Broadcasts high-priority Danger Warning and sets temporary No-Trade lock.
        """
        now = time.time()
        danger_info = self.calendar_collector.is_news_danger_zone(buffer_minutes=30)
        
        if danger_info.get("is_danger"):
            # Mark danger state in database
            database.set_state("news_danger_zone_active", "true")
            database.set_state("news_danger_event_title", danger_info.get("title", ""))
            
            last_alert = float(database.get_state("last_danger_zone_alert_ts") or 0.0)
            # Send alert once per danger event (cooldown 45 mins)
            if now - last_alert >= 2700:
                logger.warning(f"[AI NEWS DANGER ZONE] High-impact event approaching: {danger_info['title']}")
                msg = KhmerFormatter.format_danger_zone_alert(danger_info)
                self.notifier.send_message(msg)
                database.set_state("last_danger_zone_alert_ts", str(now))
        else:
            database.set_state("news_danger_zone_active", "false")

    def check_sniper_instant_signals(self):
        """
        Monitors live market for AI Sniper Instant Entry (BUY DIP / SELL TOP) with precise SL & TP.
        Deeply audited by AI for maximum accuracy and strictly capped at 5 positions per day.
        Blocked automatically if AI News Danger Zone is active or market is in Asian/pre-market low volume.
        """
        # Safety Gate 1: Do NOT send buy/sell signals within 30 minutes of High-Impact News!
        danger_info = self.calendar_collector.is_news_danger_zone(buffer_minutes=30)
        if danger_info.get("is_danger"):
            logger.info(f"[SNIPER SIGNAL BLOCKED] Danger zone active for {danger_info.get('title')}. Capital protection active.")
            return

        # Safety Gate 2: Trading Sessions Filter (Strictly 07:00 AM to 23:00 / 11:00 PM Cambodia Time)
        now_kh = datetime.now(CAMBODIA_TZ)
        hour_kh = now_kh.hour
        # Signals strictly allowed from 07:00 AM to 23:00 (11:00 PM) Cambodia Time (7:00 - 23:00)
        is_active_session = (7 <= hour_kh < 23)
        if not is_active_session:
            # Outside active trading window (between 23:00 / 11:00 PM and 07:00 AM)
            return

        # Safety Gate 3: Strict Daily Signal Limit (Strictly maximum 5 position signals per day)
        DAILY_MAX_SIGNALS = 5
        daily_count = database.get_daily_signal_count()
        if daily_count >= DAILY_MAX_SIGNALS:
            logger.info(f"[SNIPER SIGNAL BLOCKED] Daily signal limit reached ({daily_count}/{DAILY_MAX_SIGNALS}). Overtrading protection active.")
            return

        now = time.time()
        last_sniper = float(database.get_state("last_sniper_signal_ts") or 0.0)
        last_action = database.get_state("last_sniper_action") or ""
        
        # 30-minute cooldown or until opposite signal appears
        if now - last_sniper < 1800:
            return

        price_data = self.gold_collector.fetch_price()
        current_price = price_data.get("price_oz", 0.0)
        levels = price_data.get("key_levels", {})

        sig = self.candle_analyzer.detect_sniper_instant_signal(current_price, levels)
        if sig:
            # Avoid repeating the same direction consecutively within short period
            if sig.get("action") == last_action and (now - last_sniper < 3600):
                return

            # Safety Gate 4: AI Deep Analysis & Accuracy Verification (AI Analy ត្រឹមត្រូវបំផុត)
            macro_data = self.macro_collector.fetch_macro_correlations()
            order_book = self.order_book_tracker.fetch_order_book_depth()
            ai_audit = self.analyzer.analyze_and_validate_sniper_signal(
                raw_signal=sig,
                current_price=current_price,
                key_levels=levels,
                macro_data=macro_data,
                order_book=order_book
            )
            if not ai_audit or not ai_audit.get("approved"):
                logger.info(f"[SNIPER SIGNAL REJECTED BY AI AUDITOR] Reason: {ai_audit.get('rejection_reason') if ai_audit else 'Low confluence'}")
                return

            # Final check on daily quota limit before issuing
            if not database.can_issue_signal_today(DAILY_MAX_SIGNALS):
                logger.info(f"[SNIPER SIGNAL BLOCKED] Daily position limit of {DAILY_MAX_SIGNALS} reached. Capital protection active.")
                return

            new_daily_count = database.increment_daily_signal_count()
            sig["daily_count"] = new_daily_count
            sig["daily_max"] = DAILY_MAX_SIGNALS

            # Apply AI audited & refined parameters
            sig["entry"] = float(ai_audit.get("entry", sig["entry"]))
            sig["sl"] = float(ai_audit.get("sl", sig["sl"]))
            sig["tp1"] = float(ai_audit.get("tp1", sig["tp1"]))
            sig["tp2"] = float(ai_audit.get("tp2", sig["tp2"]))
            sig["rr_ratio"] = ai_audit.get("rr_ratio", sig.get("rr_ratio", "1:2.0"))
            sig["confidence_score"] = ai_audit.get("confidence_score", sig.get("confidence_score", "88%"))
            sig["ai_analysis"] = ai_audit.get("ai_analysis", "")
            sig["macro_context"] = ai_audit.get("macro_context", "")
            sig["invalidation_note"] = ai_audit.get("invalidation_note", "")
            sig["execution_tips"] = ai_audit.get("execution_tips", "")

            sig_id = f"sig_{int(now)}"
            logger.info(f"[AI SNIPER INSTANT SIGNAL APPROVED] {sig['action_title']} at ${sig['entry']} (ID: {sig_id}) | Daily Position: {new_daily_count}/{DAILY_MAX_SIGNALS}")
            msg = KhmerFormatter.format_sniper_instant_alert(sig)
            
            # Direct Signal Alert via Private Bot DM ONLY (Never sent to public channel)
            subscribers = database.get_signal_subscribers()
            admin_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
            if admin_id and admin_id.isdigit():
                subscribers = list(set(subscribers + [int(admin_id)]))

            for sub_id in subscribers:
                try:
                    self.notifier.send_message(msg, chat_id=sub_id)
                except Exception as e:
                    logger.warning(f"[Private Sniper Signal DM] Error sending to {sub_id}: {e}")

            database.set_state("last_sniper_signal_ts", str(now))
            database.set_state("last_sniper_action", sig.get("action", ""))
            # Save active signal details for Dynamic Break-Even & Profit Lock tracking
            database.set_state("active_trade_action", sig.get("action", ""))
            database.set_state("active_trade_entry", str(sig.get("entry", 0.0)))
            database.set_state("active_trade_tp1", str(sig.get("tp1", 0.0)))
            database.set_state("active_trade_tp2", str(sig.get("tp2", 0.0)))
            database.set_state("active_trade_sl", str(sig.get("sl", 0.0)))
            database.set_state("active_trade_be_sent", "false")

    def check_dynamic_breakeven_trailing(self):
        """
        Monitors active trades in real time.
        When price moves +30 pips in profit towards TP1, automatically fires
        Dynamic Break-Even & Profit Lock Alert to Telegram so members lock risk-free profits.
        """
        active_action = database.get_state("active_trade_action")
        if not active_action:
            return

        be_sent = database.get_state("active_trade_be_sent")
        if be_sent == "true":
            return

        try:
            entry_p = float(database.get_state("active_trade_entry") or 0.0)
            tp1_p = float(database.get_state("active_trade_tp1") or 0.0)
            if entry_p <= 0:
                return

            price_data = self.gold_collector.fetch_price()
            curr_p = price_data.get("price_oz", 0.0)
            if curr_p <= 0:
                return

            pips_gained = 0.0
            trigger_be = False

            if "BUY" in active_action:
                pips_gained = (curr_p - entry_p) * 10.0
                # Trigger when gained >= 30 pips ($3.00)
                if pips_gained >= 30.0:
                    trigger_be = True
            elif "SELL" in active_action:
                pips_gained = (entry_p - curr_p) * 10.0
                if pips_gained >= 30.0:
                    trigger_be = True

            if trigger_be:
                logger.info(f"[DYNAMIC BREAK-EVEN TRIGGERED] {active_action} gained +{pips_gained:.1f} pips. Sending lock alert.")
                be_info = {
                    "action": active_action,
                    "entry_price": entry_p,
                    "current_price": curr_p,
                    "tp1_price": tp1_p,
                    "pips_gained": pips_gained
                }
                msg = KhmerFormatter.format_breakeven_profit_alert(be_info)
                self.notifier.send_message(msg)
                database.set_state("active_trade_be_sent", "true")
        except Exception as e:
            logger.warning(f"Error checking dynamic breakeven: {e}")

    def check_liquidity_sweep(self):
        """
        Monitors for real-time institutional liquidity sweeps (Stop Loss Hunts)
        at Asian High/Low and Key Session levels.
        """
        now = time.time()
        last_sweep = float(database.get_state("last_liquidity_sweep_ts") or 0.0)
        if now - last_sweep < 3600:  # 1-hour cooldown between liquidity sweep alerts
            return

        sweep = self.candle_analyzer.detect_liquidity_sweep()
        if sweep:
            logger.info(f"[LIQUIDITY SWEEP DETECTED] {sweep['type']} at {sweep['level_name']}")
            msg = KhmerFormatter.format_liquidity_sweep(sweep)
            self.notifier.send_message(msg)
            database.set_state("last_liquidity_sweep_ts", str(now))

    def check_macro_divergence(self):
        """
        Monitors institutional divergence between Gold and US Dollar Index (DXY).
        Sends high-priority alert when Gold shows Bullish Accumulation or Bearish Distribution.
        """
        now = time.time()
        last_div = float(database.get_state("last_macro_divergence_ts") or 0.0)
        if now - last_div < 7200:  # 2-hour cooldown between divergence alerts
            return

        price_data = self.gold_collector.fetch_price()
        current_price = price_data.get("price_oz", 0.0)
        gold_pct = price_data.get("change_pct", 0.0)

        div = self.macro_collector.detect_divergence(current_price, gold_pct)
        if div:
            logger.info(f"[MACRO DIVERGENCE DETECTED] {div['type']}")
            msg = KhmerFormatter.format_divergence_alert(div)
            self.notifier.send_message(msg)
            database.set_state("last_macro_divergence_ts", str(now))



    def check_weekly_sunday_outlook(self):
        """
        Broadcasts Weekly Macro Outlook every Sunday at 19:00 (7:00 PM Cambodia Time)
        before markets open on Monday morning.
        """
        now_kh = datetime.now(CAMBODIA_TZ)
        # Sunday is weekday 6
        if now_kh.weekday() == 6 and now_kh.hour >= 19:
            today_str = now_kh.strftime("%Y-%m-%d")
            key = f"weekly_outlook_{today_str}"
            if database.get_state(key):
                return

            logger.info(f"Triggering Weekly Sunday Outlook for {today_str}...")
            price_data = self.gold_collector.fetch_price()
            events = self.calendar_collector.fetch_events()
            high_impact = [e for e in events if e.get("impact") == "HIGH"]

            summary = self.analyzer.summarize_daily_price(price_data)
            cot_data = self.cot_collector.fetch_gold_cot()
            msg = KhmerFormatter.format_weekly_outlook(price_data, high_impact, summary=summary, cot_data=cot_data)
            self.notifier.send_message(msg)
            database.set_state(key, "sent")
            logger.info("Weekly Sunday Outlook broadcasted successfully.")

    def check_database_maintenance(self):
        """Performs automatic database cleanup keeping data.db fast and lightweight (1-2 days retention)."""
        now_kh = datetime.now(CAMBODIA_TZ)
        today_str = now_kh.strftime("%Y-%m-%d")
        key = f"db_maintenance_{today_str}"

        # Run once a day around midnight
        if now_kh.hour == 0 and not database.get_state(key):
            cleaned = database.cleanup_old_records(days=2)
            # Auto-clear scratch directory files older than 2 days
            try:
                scratch_dir = BASE_DIR / "scratch"
                if scratch_dir.exists():
                    cutoff = time.time() - (2 * 86400)
                    for item in scratch_dir.iterdir():
                        if item.is_file() and item.stat().st_mtime < cutoff:
                            item.unlink()
            except Exception as e:
                logger.debug(f"Scratch cleanup notice: {e}")

            database.set_state(key, "done")
            logger.info(f"[DB Auto-Maintenance] Cleaned {cleaned} old records (retention: 2 days) and executed VACUUM successfully.")

    def process_incoming_commands(self):
        """Listens and responds to Telegram user commands (/price, /levels, /calendar, /help)."""
        offset = int(database.get_state("telegram_update_offset") or 0)
        updates = self.notifier.get_updates(offset=offset, timeout=1)
        if not updates:
            return

        for u in updates:
            up_id = u.get("update_id", 0)
            database.set_state("telegram_update_offset", str(up_id + 1))

            lot_calculator_inline_buttons = {
                "inline_keyboard": [
                    [
                        {"text": "💵 $50", "callback_data": "lot_calc:50:2:10"},
                        {"text": "💵 $100", "callback_data": "lot_calc:100:2:10"},
                        {"text": "💵 $200", "callback_data": "lot_calc:200:2:10"}
                    ],
                    [
                        {"text": "💵 $500", "callback_data": "lot_calc:500:1.5:10"},
                        {"text": "💵 $1,000", "callback_data": "lot_calc:1000:1.5:10"},
                        {"text": "💵 $2,000", "callback_data": "lot_calc:2000:1:10"}
                    ],
                    [
                        {"text": "💎 $3,000", "callback_data": "lot_calc:3000:1:10"},
                        {"text": "💎 $5,000", "callback_data": "lot_calc:5000:1:10"},
                        {"text": "👑 $10,000", "callback_data": "lot_calc:10000:1:10"}
                    ],
                    [
                        {"text": "⚡ $100 (Risk 5%)", "callback_data": "lot_calc:100:5:10"},
                        {"text": "🔥 $1,000 (Risk 2%)", "callback_data": "lot_calc:1000:2:10"}
                    ],
                    [
                        {"text": "📱 បើក Mini App គិត Lot (Sliders)", "url": "https://ynkkxxz-max.github.io/xauusd-news-bot/?tab=lot"}
                    ]
                ]
            }

            # 2-Button Clean Custom Keyboard directly at the bottom (Price & SMC)
            bottom_keyboard = {
                "keyboard": [
                    [
                        {"text": "Price"},
                        {"text": "SMC", "web_app": {"url": "https://ynkkxxz-max.github.io/xauusd-news-bot/?v=150&tab=smc"}}
                    ]
                ],
                "resize_keyboard": True,
                "is_persistent": True
            }

            # 1. Handle Callback Query clicks (Inline Buttons)
            cb_query = u.get("callback_query")
            if cb_query:
                cb_id = cb_query.get("id")
                cb_data = cb_query.get("data", "")
                cb_chat_id = cb_query.get("message", {}).get("chat", {}).get("id")
                user_obj = cb_query.get("from", {})
                user_id = user_obj.get("id", 0)
                user_name = user_obj.get("first_name", "Trader")

                # Handle Signal Win/Loss Vote (Hit TP / Hit SL)
                if cb_data.startswith("vote_tp:") or cb_data.startswith("vote_sl:"):
                    vote_type = "TP" if cb_data.startswith("vote_tp:") else "SL"
                    signal_id = cb_data.split(":", 1)[1] if ":" in cb_data else "general"

                    res = database.record_signal_vote(signal_id=signal_id, user_id=user_id, user_name=user_name, vote_type=vote_type)
                    tp_c = res.get("tp_count", 0)
                    sl_c = res.get("sl_count", 0)

                    if vote_type == "TP":
                        alert_msg = f"🎉 អបអរសាទរ {user_name}! បានកត់ត្រា Hit TP ជោគជ័យ។ (សរុប TP: {tp_c} | SL: {sl_c})"
                    else:
                        alert_msg = f"💪 មិនអីទេ {user_name}! លើកទឹកចិត្តឱ្យរក្សា Risk Management។ (សរុប TP: {tp_c} | SL: {sl_c})"

                    self.notifier.answer_callback_query(cb_id, text=alert_msg, show_alert=True)
                    continue

                if cb_data.startswith("lot_calc:") and cb_chat_id:
                    self.notifier.answer_callback_query(cb_id, text="🧮 កំពុងគណនា Lot Size...")
                    parts = cb_data.split(":")
                    if len(parts) == 4:
                        bal = float(parts[1])
                        rp = float(parts[2])
                        sl_usd = float(parts[3])
                        calc = RiskLotCalculator.calculate_lot_size(balance=bal, risk_pct=rp, sl_points_usd=sl_usd)
                        resp = KhmerFormatter.format_lot_size_calculator(calc)
                        self.notifier.send_message(resp, chat_id=cb_chat_id, reply_markup=lot_calculator_inline_buttons)
                    continue

                # 🔒 Handle Official Channel Join Verification Gate
                if cb_data == "verify_channel_join":
                    is_now_member = self.notifier.is_user_member_of_channel(user_id=user_id)
                    if is_now_member:
                        self.notifier.answer_callback_query(cb_id, text="🎉 ផ្ទៀងផ្ទាត់ជោគជ័យ! អរគុណសម្រាប់ការចូលរួម Channel។", show_alert=True)
                        unlock_text = (
                            "🎉 <b>អបអរសាទរ! ការផ្ទៀងផ្ទាត់បានជោគជ័យ</b>\n\n"
                            "✅ គណនីរបស់អ្នកត្រូវបានផ្ទៀងផ្ទាត់ថាបានចូលរួម <b>GOLD FX Official Channel</b> រួចរាល់ហើយ!\n\n"
                            "📱 ឥឡូវនេះលោកអ្នកអាចបើកប្រើប្រាស់ <b>Telegram Mini App (SMC AI Terminal)</b> និង Signal Live បានពេញលេញ!"
                        )
                        unlocked_markup = {
                            "inline_keyboard": [
                                [
                                    {"text": "📱 បើក Mini App ដើម្បីទទួលបាន Signal Live", "url": "https://ynkkxxz-max.github.io/xauusd-news-bot/?v=150&tab=smc"}
                                ],
                                [
                                    {"text": "📊 មើល TradingView Live Chart", "url": "https://ynkkxxz-max.github.io/xauusd-news-bot/?v=150&tab=chart"},
                                    {"text": "🧮 គិត Lot Size", "url": "https://ynkkxxz-max.github.io/xauusd-news-bot/?v=150&tab=lot"}
                                ]
                            ]
                        }
                        self.notifier.send_message(unlock_text, chat_id=cb_chat_id, reply_markup=unlocked_markup)
                        self.notifier.send_message("👇 <b>ចុចប៊ូតុង [ SMC ] ខាងក្រោមដើម្បីបើក Mini App គ្រប់ពេល៖</b>", chat_id=cb_chat_id, reply_markup=bottom_keyboard)
                    else:
                        self.notifier.answer_callback_query(cb_id, text="⚠️ លោកអ្នកមិនទាន់បាន Join Channel នៅឡើយទេ! សូមចុចប៊ូតុង [📢 ចូលរួម Telegram Channel] ជាមុនសិន។", show_alert=True)
                    continue

            # 2. Handle Text Messages or WebApp Data
            msg_obj = u.get("message", {})
            chat_id = msg_obj.get("chat", {}).get("id")
            web_app_data = msg_obj.get("web_app_data", {}).get("data", "")
            text = (web_app_data or msg_obj.get("text") or "").strip()

            if not text or not chat_id:
                continue

            # 🔒 Force Join Channel Gate for Private Users (chat_id > 0)
            if chat_id > 0:
                from_user = msg_obj.get("from", {})
                from_user_id = from_user.get("id") or chat_id
                # Register private user for Direct Signal DMs
                database.add_signal_subscriber(
                    chat_id=chat_id,
                    username=from_user.get("username"),
                    first_name=from_user.get("first_name")
                )
                # Check if user has joined the official channel
                is_member = self.notifier.is_user_member_of_channel(user_id=from_user_id)
                if not is_member:
                    force_join_text = (
                        "🔒 <b>សូមចូលរួម (Join) Telegram Channel ជាមុនសិន!</b>\n\n"
                        "ដើម្បីទប់ស្កាត់ការលួចចម្លង Signal និងអាចបើកប្រើប្រាស់ <b>Telegram Mini App</b> បាន "
                        "លោកអ្នកត្រូវតែជាសមាជិកនៃ Channel ផ្លូវការរបស់យើងខ្ញុំជាមុនសិន។\n\n"
                        "📢 <b>Channel ផ្លូវការ:</b> @GoldMarketKH8888 (GOLD FX)\n\n"
                        "<i>បន្ទាប់ពីចុច Join រួចរាល់ សូមចុចប៊ូតុង «✅ ខ្ញុំបាន Join រួចហើយ» ខាងក្រោមដើម្បីដោះសោរបើក Mini App!</i>"
                    )
                    force_join_markup = {
                        "inline_keyboard": [
                            [
                                {"text": "📢 ចូលរួម Telegram Channel (Join Now)", "url": "https://t.me/GoldMarketKH8888"}
                            ],
                            [
                                {"text": "✅ ខ្ញុំបាន Join រួចហើយ (Verify & Open)", "callback_data": "verify_channel_join"}
                            ]
                        ]
                    }
                    self.notifier.send_message(force_join_text, chat_id=chat_id, reply_markup=force_join_markup)
                    continue

            inline_trading_buttons = {
                "inline_keyboard": [
                    [
                        {"text": "📊 មើល Chart ផ្ទាល់ (TradingView)", "url": "https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD"},
                        {"text": "📅 ប្រតិទិនសេដ្ឋកិច្ច", "url": "https://www.forexfactory.com/calendar"}
                    ]
                ]
            }

            # Command routing
            clean_cmd = text.split()[0].lower()

            if clean_cmd in ("/stats", "/winrate", "stats", "winrate") or "ស្ថិតិ" in text:
                stats = database.get_overall_signal_vote_stats()
                resp = KhmerFormatter.format_signal_stats(stats)
                self.notifier.send_message(resp, chat_id=chat_id, reply_markup=bottom_keyboard)

            elif clean_cmd in ("/lot", "/risk", "lot", "risk") or "lot" in text.lower() or "risk" in text.lower() or "គិត" in text:
                parsed = RiskLotCalculator.parse_user_input(text)
                if parsed:
                    calc = RiskLotCalculator.calculate_lot_size(
                        balance=parsed["balance"],
                        risk_pct=parsed["risk_pct"],
                        entry_price=parsed.get("entry_price"),
                        sl_price=parsed.get("sl_price"),
                        sl_points_usd=parsed.get("sl_points_usd")
                    )
                    resp = KhmerFormatter.format_lot_size_calculator(calc)
                    self.notifier.send_message(resp, chat_id=chat_id, reply_markup=lot_calculator_inline_buttons)
                else:
                    # Provide default quick calculation with interactive buttons
                    default_calc = RiskLotCalculator.calculate_lot_size(balance=1000, risk_pct=1.0, sl_points_usd=10.0)
                    resp = (
                        f"{KhmerFormatter.format_lot_size_calculator(default_calc)}\n\n"
                        f"👇 <b>ចុចប៊ូតុងខាងក្រោមដើម្បីជ្រើសរើសដើមទុនភ្លាមៗ ឬវាយតាមទម្រង់ផ្ទាល់ខ្លួន៖</b>\n"
                        f"• <code>/lot 1000 1 10</code> <i>(ដើមទុន $1000, Risk 1%, SL $10)</i>\n"
                        f"• <code>/lot 500 2 4365 4355</code> <i>(Entry 4365, SL 4355)</i>"
                    )
                    self.notifier.send_message(resp, chat_id=chat_id, reply_markup=lot_calculator_inline_buttons)

            elif clean_cmd in ("/price", "/gold", "price") or "ហាងឆេងមាស" in text:
                from collectors.market_cache import market_cache
                # Ultra-Fast In-Memory RAM Cache Check (< 0.001s)
                cached_msg = market_cache.get_preformatted_price_msg()
                if cached_msg:
                    self.notifier.send_message(cached_msg, chat_id=chat_id, reply_markup=bottom_keyboard)
                else:
                    price_data = self.gold_collector.fetch_price()
                    resp = KhmerFormatter.format_daily_gold_price(price_data, summary="", include_smc=False)
                    market_cache.set_preformatted_price_msg(resp)
                    self.notifier.send_message(resp, chat_id=chat_id, reply_markup=bottom_keyboard)

            elif clean_cmd in ("/levels", "/setup", "smc") or "កម្រិត smc" in text.lower():
                from collectors.market_cache import market_cache
                import time
                smc_sig_id = f"smc_{datetime.now().strftime('%Y%m%d_%H')}"
                smc_inline_buttons = {
                    "inline_keyboard": [
                        [
                            {"text": "📱 បើក Mini App ដើម្បីទទួលបាន Signal Live", "url": "https://ynkkxxz-max.github.io/xauusd-news-bot/?v=150&tab=smc"}
                        ],
                        [
                            {"text": "📊 មើល TradingView Live Chart", "url": "https://ynkkxxz-max.github.io/xauusd-news-bot/?v=150&tab=chart"},
                            {"text": "🧮 គិត Lot Size", "url": "https://ynkkxxz-max.github.io/xauusd-news-bot/?v=150&tab=lot"}
                        ]
                    ]
                }
                # Ultra-Fast Sub-Second In-Memory RAM Cache Check (< 0.001s)
                cached_smc_msg = market_cache.get_preformatted_smc_msg()
                if cached_smc_msg:
                    self.notifier.send_message(cached_smc_msg, chat_id=chat_id, reply_markup=smc_inline_buttons)
                else:
                    price_data = self.gold_collector.fetch_price()
                    levels = price_data.get("key_levels", {})
                    oz = price_data.get("price_oz", 0.0)

                    setup = market_cache.get_smc_setup()
                    if not setup:
                        macro_data = self.macro_collector.fetch_macro_correlations()
                        order_book = self.order_book_tracker.fetch_order_book_depth()
                        setup = self.analyzer.generate_smart_smc_setup(
                            current_price=oz,
                            key_levels=levels,
                            macro_data=macro_data,
                            order_book=order_book
                        )
                        if not setup:
                            setup = MacroAnalyzer.generate_smart_smc_setup(
                                current_price=oz,
                                key_levels=levels,
                                macro_data=macro_data,
                                order_book=order_book
                            )
                    reply = KhmerFormatter.format_single_smc_setup(setup, key_levels=levels, current_price=oz)
                    market_cache.set_preformatted_smc_msg(reply)
                    self.notifier.send_message(reply, chat_id=chat_id, reply_markup=smc_inline_buttons)

            elif clean_cmd in ("/calendar", "/events") or "ប្រតិទិនសេដ្ឋកិច្ច" in text:
                png = self._build_calendar_png()
                if png:
                    self.notifier.send_photo(png, caption="📅 <b>ប្រតិទិនសេដ្ឋកិច្ចថ្ងៃនេះ — ម៉ោងនៅកម្ពុជា (UTC+7)</b>", chat_id=chat_id, reply_markup=bottom_keyboard)
                else:
                    self.notifier.send_message("📅 មិនមានទិន្នន័យប្រតិទិនសេដ្ឋកិច្ចធំៗថ្ងៃនេះទេ។", chat_id=chat_id, reply_markup=bottom_keyboard)

            elif clean_cmd in ("/cot", "/cftc", "cot") or "ស្ថាប័ន cftc" in text.lower():
                cot_data = self.cot_collector.fetch_gold_cot()
                resp = KhmerFormatter.format_cot_report(cot_data)
                self.notifier.send_message(resp, chat_id=chat_id, reply_markup=bottom_keyboard)

            elif clean_cmd in ("/dxy", "/macro", "/divergence") or "ដុល្លារ" in text:
                price_data = self.gold_collector.fetch_price()
                current_price = price_data.get("price_oz", 0.0)
                gold_pct = price_data.get("change_pct", 0.0)
                macro = self.macro_collector.fetch_macro_correlations()
                dxy_p = macro.get("dxy_price", 100.0)
                dxy_c = macro.get("dxy_pct", 0.0)
                us10y = macro.get("us10y_yield", 4.0)
                gld_v = macro.get("gld_volume", 0)

                div = self.macro_collector.detect_divergence(current_price, gold_pct)
                if div:
                    resp = KhmerFormatter.format_divergence_alert(div)
                else:
                    g_sign = "+" if gold_pct >= 0 else ""
                    d_sign = "+" if dxy_c >= 0 else ""
                    resp = (
                        f"📊 <b>MACRO CORRELATION (DXY & US10Y) ស្ថិតិទីផ្សារ</b>\n\n"
                        f"• 🥇 <b>Gold Spot (XAU/USD):</b> <code>${current_price:,.2f}</code> ({g_sign}{gold_pct:.2f}%)\n"
                        f"• 💵 <b>US Dollar Index (DXY):</b> <code>{dxy_p}</code> ({d_sign}{dxy_c:.2f}%)\n"
                        f"• 📈 <b>US 10-Year Bond Yield:</b> <code>{us10y}%</code>\n"
                        f"• 🐋 <b>SPDR Gold Shares (GLD Volume):</b> <code>{gld_v:,}</code>\n\n"
                        f"⚖️ <b>ស្ថានភាព Divergence:</b> ទីផ្សារកំពុងដើរតាម Normal Correlation (មិនទាន់មាន Divergence ច្បាស់លាស់ទេ)។"
                    )
                self.notifier.send_message(resp, chat_id=chat_id, reply_markup=bottom_keyboard)

            elif clean_cmd in ("/voice", "/audio", "voice") or "សំឡេង" in text:
                price_data = self.gold_collector.fetch_price()
                self.notifier.send_message("🎙️ <i>កំពុងបង្កើតសំឡេងសង្ខេបភាសាខ្មែរ សូមរង់ចាំមួយភ្លែត...</i>", chat_id=chat_id)
                voice_script = self.voice_synth.build_morning_voice_script(price_data)
                voice_bytes = self.voice_synth.text_to_speech(voice_script)
                if voice_bytes and len(voice_bytes) > 1000:
                    self.notifier.send_voice(
                        voice_bytes,
                        caption="🎙️ <b>សំឡេងសង្ខេបហាងឆេងមាស (Khmer Gold Audio Brief)</b>",
                        chat_id=chat_id,
                        reply_markup=bottom_keyboard
                    )
                else:
                    self.notifier.send_message("⚠️ មិនអាចបង្កើតសំឡេងបាននៅពេលនេះទេ សូមព្យាយាមម្តងទៀត។", chat_id=chat_id, reply_markup=bottom_keyboard)

            elif clean_cmd in ("/heatmap", "/liquidity", "heatmap") or "ផែនទីកម្តៅ" in text or "heatmap" in text.lower():
                self.notifier.send_message("🧠 <i>AI កំពុងគូរផែនទីកម្តៅ Liquidity Heatmap HD ផ្អែកលើ Order Flow & Stop Loss clusters...</i>", chat_id=chat_id)
                price_data = self.gold_collector.fetch_price()
                order_book = self.order_book_tracker.fetch_order_book_depth()
                heatmap_png = self.heatmap_builder.generate_heatmap_png(price_data, order_book)
                if heatmap_png:
                    spot = price_data.get("price_oz", 0.0)
                    bid_ratio = order_book.get("bid_dominance_pct", 50.0) if order_book else 50.0
                    ask_ratio = order_book.get("ask_dominance_pct", 50.0) if order_book else 50.0
                    bias = order_book.get("bias", "Normal") if order_book else "Balanced"
                    caption = (
                        f"🧠 <b>SMART MONEY ORDER FLOW HEATMAP (XAU/USD)</b>\n\n"
                        f"• 🥇 <b>Current Spot:</b> <code>${spot:,.2f}</code>\n"
                        f"• 🔴 <b>BSL (Buy Side Liquidity):</b> តំបន់ Stop Loss Clusters (ខាងលើ)\n"
                        f"• 🟢 <b>SSL (Sell Side Liquidity):</b> តំបន់ Stop Loss Clusters (ខាងក្រោម)\n"
                        f"• 📊 <b>Depth Imbalance:</b> Bids {bid_ratio:.1f}% vs Asks {ask_ratio:.1f}%\n"
                        f"• ⚖️ <b>ស្ថានភាព:</b> {bias}\n\n"
                        f"💡 <i>ផែនទីកម្តៅបង្ហាញពីតំបន់ដែលស្ថាប័នធំៗចូលចិត្តទាញតម្លៃទៅ Hunt Liquidity មុនពេលប្តូរទិសដៅ!</i>"
                    )
                    self.notifier.send_photo(heatmap_png, caption=caption, chat_id=chat_id, reply_markup=bottom_keyboard)
                else:
                    self.notifier.send_message("⚠️ មិនអាចបង្កើត Heatmap បានទេនៅពេលនេះ។", chat_id=chat_id, reply_markup=bottom_keyboard)

            elif clean_cmd in ("/chart", "/scan", "/scanner", "/pattern", "chart") or "ស្កេន" in text or "chart" in text.lower():
                self.notifier.send_message("👁️‍🗨️ <i>AI Multimodal Vision កំពុងទាញយកទិន្នន័យទៀនផ្សារ Live និងស្កេនទម្រង់ Candlestick & SMC Patterns...</i>", chat_id=chat_id)
                price_data = self.gold_collector.fetch_price()
                oz = price_data.get("price_oz", 0.0)
                levels = price_data.get("key_levels", {})
                candles = self.candle_analyzer.fetch_m15_candles(count=40)
                
                # Fetch SMC setup context
                macro_data = self.macro_collector.fetch_macro_correlations()
                order_book = self.order_book_tracker.fetch_order_book_depth()
                setup = self.analyzer.generate_smart_smc_setup(
                    current_price=oz,
                    key_levels=levels,
                    macro_data=macro_data,
                    order_book=order_book
                )

                # Render HD Candlestick Chart
                chart_png = self.chart_renderer.render_candlestick_chart(
                    candles=candles,
                    current_price=oz,
                    key_levels=levels,
                    setup=setup,
                    timeframe="M15",
                    title_extra=setup.get("setup_title", "") if setup else ""
                )

                if chart_png:
                    # Run Gemini Multimodal Vision analysis on the chart image
                    vision_res = self.analyzer.analyze_chart_image(chart_png, current_price=oz, key_levels=levels)
                    if vision_res:
                        caption_text = KhmerFormatter.format_chart_vision_scan(oz, vision_res, timeframe="M15")
                    else:
                        pattern_name = "ទម្រង់ទៀនបញ្ជាក់ច្បាស់ (Confirmed Action)"
                        caption_text = (
                            f"👁️‍🗨️ <b>AI LIVE CANDLESTICK & SMC PATTERN SCANNER (M15)</b>\n\n"
                            f"• 🥇 <b>Spot XAU/USD:</b> <code>${oz:,.2f}</code>\n"
                            f"• 🕯️ <b>ស្ថានភាពទៀន:</b> <b>{pattern_name}</b>\n"
                            f"• 🎯 <b>ទិសដៅ AI SMC:</b> <b>{setup.get('setup_title', 'BUY')}</b>\n\n"
                            f"💡 <i>អនុសាសន៍: រង់ចាំទៀន M15 បិទដើម្បីបញ្ជាក់ពីប្រតិកម្មទាត់ចោលថ្លៃ (Rejection) មុនចូល Order!</i>"
                        )

                    caption_clean = self._truncate_html_caption(caption_text, max_visible_chars=950)
                    self.notifier.send_photo(
                        chart_png,
                        caption=caption_clean,
                        chat_id=chat_id,
                        reply_markup=inline_trading_buttons
                    )
                else:
                    self.notifier.send_message("⚠️ មិនអាចទាញយក Chart បានទេនៅពេលនេះ សូមព្យាយាមម្តងទៀត។", chat_id=chat_id, reply_markup=bottom_keyboard)

            elif clean_cmd in ("/depth", "/orderbook", "/iceberg", "orderbook") or "ជម្រៅទីផ្សារ" in text:
                depth = self.order_book_tracker.fetch_order_book_depth()
                resp = KhmerFormatter.format_order_book_depth(depth)
                self.notifier.send_message(resp, chat_id=chat_id, reply_markup=bottom_keyboard)

            elif clean_cmd in ("/fomc", "/fed", "/chair") or "fed" in text.lower():
                self.notifier.send_message("⚡ <i>AI កំពុងទាញយកសេចក្តីថ្លែងការណ៍ FOMC និងសុន្ទរកថា Fed ចុងក្រោយបង្អស់មកវិភាគបកប្រែ...</i>", chat_id=chat_id)
                # Fetch latest Fed official press releases
                fed_items = [it for it in self.news_collector.fetch_latest_news() if any(k in it['title'].lower() for k in ['fed', 'fomc', 'federal reserve', 'fed chair', 'monetary policy'])]
                if fed_items:
                    target = fed_items[0]
                    interp = self.fomc_interpreter.interpret_powell_speech(f"{target['title']}\n{target.get('description', '')}", event_title=target['title'])
                    if interp:
                        resp = KhmerFormatter.format_fomc_speech_alert(target['title'], interp)
                        self.notifier.send_message(resp, chat_id=chat_id, reply_markup=bottom_keyboard)
                        if interp.get("voice_script"):
                            v_b = self.voice_synth.text_to_speech(interp["voice_script"])
                            if v_b and len(v_b) > 1000:
                                spk = "Fed"
                                for name in ["Kevin Warsh", "Warsh", "Jerome Powell", "Powell", "Christopher Waller", "Waller", "Michelle Bowman", "Bowman", "Austan Goolsbee", "Goolsbee", "John Williams", "Williams"]:
                                    if name.lower() in target['title'].lower():
                                        spk = name
                                        break
                                self.notifier.send_voice(v_b, caption=f"🎙️ <b>សំឡេងបកប្រែសង្ខេប Fed / {spk} Speech (Live Voice Brief)</b>", chat_id=chat_id)
                        return

                self.notifier.send_message("📅 មិនទាន់មានសេចក្តីថ្លែងការណ៍ FOMC ថ្មីភ្លាមៗក្នុងរយៈពេលប៉ុន្មានម៉ោងនេះទេ (រង់ចាំការប្រជុំ FOMC បន្ទាប់)។", chat_id=chat_id, reply_markup=bottom_keyboard)

            elif clean_cmd in ("/help", "/start") or "ជំនួយ" in text:
                parts = text.split()
                if len(parts) > 1 and (parts[1].lower().startswith("vote_tp_") or parts[1].lower().startswith("vote_sl_")):
                    param = parts[1].lower()
                    vote_type = "TP" if "vote_tp_" in param else "SL"
                    signal_id = param.replace("vote_tp_", "").replace("vote_sl_", "")
                    from_user = msg_obj.get("from", {})
                    u_id = from_user.get("id", chat_id)
                    u_name = from_user.get("first_name", "Trader")

                    res = database.record_signal_vote(signal_id=signal_id, user_id=u_id, user_name=u_name, vote_type=vote_type)
                    tp_c = res.get("tp_count", 0)
                    sl_c = res.get("sl_count", 0)

                    if vote_type == "TP":
                        reply_vote = (
                            f"🎉 <b>អបអរសាទរ {u_name}!</b>\n\n"
                            f"✅ បានកត់ត្រាលទ្ធផល <b>🎯 ឈ្នះ (Hit TP)</b> ជោគជ័យ!\n"
                            f"📊 ស្ថិតិ Signal នេះ: 🎯 TP: <code>{tp_c}</code> | 🛑 SL: <code>{sl_c}</code>\n\n"
                            f"💡 <i>សូមបន្តគោរព Money Management និងរក្សាប្រាក់ចំណេញ!</i>"
                        )
                    else:
                        reply_vote = (
                            f"💪 <b>មិនអីទេ {u_name}!</b>\n\n"
                            f"✅ បានកត់ត្រាលទ្ធផល <b>🛑 ចាញ់ (Hit SL)</b> ជោគជ័យ!\n"
                            f"📊 ស្ថិតិ Signal នេះ: 🎯 TP: <code>{tp_c}</code> | 🛑 SL: <code>{sl_c}</code>\n\n"
                            f"💡 <i>ការកាត់ខាតតាម SL គឺជាវិន័យដ៏ត្រឹមត្រូវបំផុតរបស់អ្នកអាជីព។ ត្រៀមឱកាស Setup ល្អបន្ទាប់!</i>"
                        )
                    self.notifier.send_message(reply_vote, chat_id=chat_id, reply_markup=bottom_keyboard)
                elif len(parts) > 1 and parts[1].lower() == "price":
                    price_data = self.gold_collector.fetch_price()
                    resp = KhmerFormatter.format_daily_gold_price(price_data, summary="", include_smc=False)
                    self.notifier.send_message(resp, chat_id=chat_id, reply_markup=bottom_keyboard)
                elif len(parts) > 1 and parts[1].lower() == "smc":
                    price_data = self.gold_collector.fetch_price()
                    levels = price_data.get("key_levels", {})
                    oz = price_data.get("price_oz", 0.0)
                    macro_data = self.macro_collector.fetch_macro_correlations()
                    order_book = self.order_book_tracker.fetch_order_book_depth()

                    # Generate AI Decisive Single-Direction Setup (Buy ONLY or Sell ONLY)
                    setup = self.analyzer.generate_smart_smc_setup(
                        current_price=oz,
                        key_levels=levels,
                        macro_data=macro_data,
                        order_book=order_book
                    )
                    if not setup:
                        setup = MacroAnalyzer.generate_smart_smc_setup(
                            current_price=oz,
                            key_levels=levels,
                            macro_data=macro_data,
                            order_book=order_book
                        )
                    smc_inline_buttons = {
                        "inline_keyboard": [
                            [
                                {"text": "📱 បើក Mini App ដើម្បីទទួលបាន Signal Live", "url": "https://ynkkxxz-max.github.io/xauusd-news-bot/?v=150&tab=smc"}
                            ],
                            [
                                {"text": "🧮 គិត Lot Size តាមដើមទុន", "url": "https://ynkkxxz-max.github.io/xauusd-news-bot/?tab=lot"}
                            ]
                        ]
                    }
                    reply = KhmerFormatter.format_single_smc_setup(setup, key_levels=levels, current_price=oz)
                    self.notifier.send_message(reply, chat_id=chat_id, reply_markup=smc_inline_buttons)
                elif len(parts) > 1 and parts[1].lower() in ("lot", "risk"):
                    default_calc = RiskLotCalculator.calculate_lot_size(balance=1000, risk_pct=1.0, sl_points_usd=10.0)
                    resp = (
                        f"{KhmerFormatter.format_lot_size_calculator(default_calc)}\n\n"
                        f"👇 <b>ចុចប៊ូតុងខាងក្រោមដើម្បីជ្រើសរើសដើមទុនភ្លាមៗ ឬវាយតាមទម្រង់ផ្ទាល់ខ្លួន៖</b>\n"
                        f"• <code>/lot 1000 1 10</code> <i>(ដើមទុន $1000, Risk 1%, SL $10)</i>\n"
                        f"• <code>/lot 500 2 4365 4355</code> <i>(Entry 4365, SL 4355)</i>"
                    )
                    self.notifier.send_message(resp, chat_id=chat_id, reply_markup=lot_calculator_inline_buttons)
                elif len(parts) > 1 and parts[1].lower() == "cot":
                    cot_data = self.cot_collector.fetch_gold_cot()
                    resp = KhmerFormatter.format_cot_report(cot_data)
                    self.notifier.send_message(resp, chat_id=chat_id, reply_markup=bottom_keyboard)
                else:
                    help_text = (
                        f"👋 <b>សូមស្វាគមន៍មកកាន់ XAUUSD AI Assistant!</b>\n\n"
                        f"សូមជ្រើសរើសចុចប៊ូតុងខាងក្រោម៖\n"
                        f"• <b>[ Price ]</b> ➡️ មើលហាងឆេងមាស Spot និងផ្សារធំថ្មីបច្ចុប្បន្ន\n"
                        f"• <b>[ SMC ]</b> ➡️ មើលកម្រិតបច្ចេកទេស AI Pivot & SMC Setup Zone"
                    )
                    self.notifier.send_message(help_text, chat_id=chat_id, reply_markup=bottom_keyboard)



    @staticmethod
    def _caption_fits(text: str, limit: int = 1024) -> bool:
        """Telegram captions are capped at 1024 characters (HTML tags not counted)."""
        return len(re.sub(r"<[^>]+>", "", text)) <= limit

    @staticmethod
    def _truncate_html_caption(text: str, max_visible_chars: int = 900) -> str:
        """Safely trims narrative text while strictly preserving header, impact line, and clickable source link."""
        if XAUUSDNewsAssistantBot._caption_fits(text, limit=1000):
            return text

        blocks = text.split("\n\n")
        if len(blocks) <= 1:
            clean = re.sub(r"<[^>]+>", "", text)
            return clean[:max_visible_chars] + "..."

        header = blocks[0]
        source_line = blocks[-1]

        # Check if second to last block is impact_line
        impact_line = ""
        body_blocks = []
        _impact_prefixes = ("ផល", "ឥទ្ធិពល", "វាផល")
        if len(blocks) >= 4 and blocks[-2].strip().startswith(_impact_prefixes):
            impact_line = blocks[-2].strip()
            body_blocks = blocks[1:-2]
        elif len(blocks) >= 3:
            if blocks[-2].strip().startswith(_impact_prefixes):
                impact_line = blocks[-2].strip()
                body_blocks = blocks[1:-2]
            else:
                body_blocks = blocks[1:-1]
        else:
            body_blocks = blocks[1:]

        body = "\n\n".join(body_blocks)

        reserved = len(re.sub(r"<[^>]+>", "", header)) + len(re.sub(r"<[^>]+>", "", source_line)) + len(impact_line) + 25
        avail = max(100, max_visible_chars - reserved)

        clean_body = re.sub(r"<[^>]+>", "", body)
        if len(clean_body) > avail:
            trimmed_body = clean_body[:avail].rsplit(" ", 1)[0] + "..."
        else:
            trimmed_body = clean_body

        parts = [p for p in [header, trimmed_body, impact_line, source_line] if p]
        res = "\n\n".join(parts)

        # Auto-close open tags
        for tag in ["i", "b", "code", "a"]:
            open_count = len(re.findall(rf"<{tag}(?:\s+[^>]*)?>", res))
            close_count = len(re.findall(rf"</{tag}>", res))
            if open_count > close_count:
                res += f"</{tag}>" * (open_count - close_count)
        return res

    @staticmethod
    def _news_ts(item: dict) -> float:
        try:
            return parsedate_to_datetime(item.get("pub_date", "")).timestamp()
        except Exception:
            return 0.0

    @staticmethod
    def _enrich_article_description(item: dict) -> str:
        """Enriches sparse RSS descriptions (< 100 chars) with rich og:description directly from article web page."""
        desc = (item.get("description") or "").strip()
        link = (item.get("link") or item.get("url") or "").strip()
        if len(desc) >= 120 or not link or not link.startswith("http") or "news.google.com" in link:
            return desc

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        try:
            resp = requests.get(link, headers=headers, timeout=6)
            if resp.status_code == 200:
                html_text = resp.text
                patterns = [
                    r'<meta[^>]+property=[\'"]og:description[\'"][^>]+content=[\'"]([^\'"]+)[\'"]',
                    r'<meta[^>]+content=[\'"]([^\'"]+)[\'"][^>]+property=[\'"]og:description[\'"]',
                    r'<meta[^>]+name=[\'"]description[\'"][^>]+content=[\'"]([^\'"]+)[\'"]',
                    r'<meta[^>]+content=[\'"]([^\'"]+)[\'"][^>]+name=[\'"]description[\'"]',
                ]
                for p in patterns:
                    m = re.search(p, html_text, re.IGNORECASE)
                    if m:
                        og_desc = html.unescape(m.group(1)).strip()
                        og_desc = re.sub(r'<[^>]+>', ' ', og_desc)
                        og_desc = re.sub(r'\s+', ' ', og_desc).strip()
                        if len(og_desc) > len(desc) and len(og_desc) >= 30:
                            logger.info(f"[ARTICLE CONTEXT ENRICHED] Added {len(og_desc)} chars of journalistic background for '{item.get('title')}'")
                            desc = og_desc
                            break

                # Also extract genuine article image if not already present
                if not item.get("image_url"):
                    img_patterns = [
                        r'<meta[^>]+property=[\'"]og:image[\'"][^>]+content=[\'"]([^\'"]+)[\'"]',
                        r'<meta[^>]+content=[\'"]([^\'"]+)[\'"][^>]+property=[\'"]og:image[\'"]',
                        r'<meta[^>]+name=[\'"]twitter:image[\'"][^>]+content=[\'"]([^\'"]+)[\'"]',
                    ]
                    for ip in img_patterns:
                        im = re.search(ip, html_text, re.IGNORECASE)
                        if im:
                            img_u = html.unescape(im.group(1)).strip()
                            if img_u.startswith("http") and not any(bad in img_u.lower() for bad in ["logo", "icon", "placeholder", "google"]):
                                item["image_url"] = img_u
                                logger.info(f"[ARTICLE IMAGE ENRICHED] Found genuine photo: {img_u[:60]}...")
                                break
        except Exception as e:
            logger.warning(f"[_enrich_article_description error] {e}")
        return desc

    @staticmethod
    def _fetch_news_image(item: dict) -> bytes:
        """
        Downloads the genuine photo attached to the news article.
        Strictly NEVER accepts generic logos (Google News logo, site icons, placeholders).
        If no genuine news photo is found, returns None so the message is sent cleanly as text per Rule 8.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        }
        url = (item.get("image_url") or "").strip()
        link = (item.get("link") or item.get("url") or "").strip()

        FORBIDDEN_PATTERNS = [
            "googleusercontent", "gstatic", "google", "logo", "icon", "avatar",
            "1x1", "placeholder", "default", "favicon", "badge", "button", "app-icon",
            "branding", "spinner", "loader"
        ]

        def _is_valid_article_img(img_url: str) -> bool:
            if not img_url or not img_url.startswith("http"):
                return False
            u_low = img_url.lower()
            return not any(pat in u_low for pat in FORBIDDEN_PATTERNS)

        def _verify_image_bytes(img_bytes: bytes) -> bool:
            if not img_bytes or len(img_bytes) < 4000:
                return False
            try:
                from PIL import Image
                import io
                with Image.open(io.BytesIO(img_bytes)) as im:
                    w, h = im.size
                    # Reject small square logos / icons; genuine news photos are landscape >= 380x200
                    if w >= 380 and h >= 180 and (w / max(h, 1)) >= 1.15:
                        return True
            except Exception:
                pass
            return False

        # 1. Try direct article image from feed
        if _is_valid_article_img(url):
            try:
                resp = requests.get(url, headers=headers, timeout=8)
                if resp.status_code == 200 and _verify_image_bytes(resp.content):
                    return resp.content
            except Exception as e:
                logger.warning(f"Direct news image fetch failed: {e}")

        # 2. Extract genuine article image directly from the publisher's web page (og:image / twitter:image)
        # Must be a specific deep article URL (not a generic section homepage like /world or /news)
        is_deep_article = (
            link.count("/") >= 4 and
            not any(link.rstrip("/").endswith(sec) for sec in ["/world", "/news", "/politics", "/markets", "/business", "/economy", "/home"])
        )
        if link and link.startswith("http") and "news.google.com" not in link and is_deep_article:
            try:
                art_resp = requests.get(link, headers=headers, timeout=6)
                if art_resp.status_code == 200:
                    patterns = [
                        r'<meta[^>]+property=[\'"]og:image[\'"][^>]+content=[\'"]([^\'"]+)[\'"]',
                        r'<meta[^>]+content=[\'"]([^\'"]+)[\'"][^>]+property=[\'"]og:image[\'"]',
                        r'<meta[^>]+name=[\'"]twitter:image(?:[:\w]+)?[\'"][^>]+content=[\'"]([^\'"]+)[\'"]',
                        r'<meta[^>]+content=[\'"]([^\'"]+)[\'"][^>]+name=[\'"]twitter:image(?:[:\w]+)?[\'"]',
                    ]
                    for p in patterns:
                        m = re.search(p, art_resp.text, re.IGNORECASE)
                        if m:
                            raw_img_url = m.group(1).replace("&amp;", "&").strip()
                            if _is_valid_article_img(raw_img_url):
                                from urllib.parse import urljoin
                                full_img_url = urljoin(link, raw_img_url)
                                img_resp = requests.get(full_img_url, headers=headers, timeout=8)
                                if img_resp.status_code == 200 and _verify_image_bytes(img_resp.content):
                                    return img_resp.content
            except Exception as e:
                logger.debug(f"Webpage og:image fetch failed for {link}: {e}")

        # Strictly return None - NEVER use random or unrelated images
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


                        if chart_png:
                            caption_text = msg
                            if not self._caption_fits(caption_text, limit=1024):
                                caption_text = caption_text[:1000] + "..."
                            self.notifier.send_photo(chart_png, caption=caption_text)
                        else:
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

    def _is_already_in_telegram_channel(self, title: str, link: str = "", khmer_text: str = "", fresh: bool = False) -> bool:
        """Inspects the public Telegram channel feed to prevent duplicate broadcasts across distributed containers."""
        try:
            import urllib.parse
            max_age = 0.0 if fresh else 30.0
            channel_html = self._fetch_channel_html(max_cache_age=max_age)
            if not channel_html:
                return False

            # 1. Exact Link & Article Slug Verification (Bulletproof Match)
            if link:
                clean_link = link.split("?")[0].rstrip("/")
                if clean_link and (clean_link in channel_html or urllib.parse.unquote(clean_link) in channel_html):
                    return True
                slug = clean_link.split("/")[-1]
                if len(slug) >= 12:
                    if slug.lower() in channel_html.lower() or slug.replace("-", " ").lower() in channel_html.lower():
                        return True

            # 2. Extract salient English/Khmer keyword tokens (min length 4)
            words = [w for w in re.findall(r'\b[A-Za-z0-9\u1780-\u17FF]{4,}\b', title) 
                     if w.lower() not in ("news", "today", "live", "world", "market", "report", "the", "says", "with", "from", "after", "gold", "price", "rate", "year", "time", "week", "state", "states", "view", "channel", "message", "telegram")]
            if len(words) >= 4:
                matches = sum(1 for w in words if w.lower() in channel_html.lower())
                if matches >= 3 and (matches / len(words)) >= 0.65:
                    return True
            elif len(words) in (2, 3):
                matches = sum(1 for w in words if w.lower() in channel_html.lower())
                if matches == len(words):
                    return True

            # 3. Khmer Translated Content Deduplication
            if khmer_text:
                kh_words = [w for w in re.findall(r'[\u1780-\u17FF]{6,}', khmer_text)]
                if len(kh_words) >= 4:
                    kh_matches = sum(1 for w in kh_words if w in channel_html)
                    if kh_matches >= 3 and (kh_matches / len(kh_words)) >= 0.4:
                        return True

            # 4. Macro Cluster & Event Verification in Channel Feed (Prevents cross-container duplicates)
            cluster = GoldNewsFilter.get_news_cluster(title)
            if cluster == "us_jobs" and re.search(r'29,000|29K|ការងារ|nfp|payroll', channel_html, re.I):
                return True
            if cluster == "inflation" and re.search(r'cpi|អតិផរណា|pce', channel_html, re.I):
                return True
            if cluster == "fed_rates" and re.search(r'fomc|អត្រាការប្រាក់|powell|kevin warsh', channel_html, re.I):
                return True
        except Exception as e:
            logger.debug(f"[Channel Feed Check] {e}")
        return False

    def check_breaking_news(self):
        """
        Monitors RSS feeds for high-impact breaking news across the 7 Core Pillars.
        Protected by Triple Anti-Duplicate Shield:
        1. Channel Live Feed Verification: Checks @GoldMarketKH8888 live messages so NO duplicate can ever be sent.
        2. In-Memory Process Set & SQLite Deduplication: Records each item_id and title as seen.
        3. Strict Gap Enforcement & Single Dispatch per cycle: Never sends back-to-back duplicates.
        """
        now = time.time()
        last_alert_ts = float(database.get_state("last_breaking_alert_ts") or "0")
        time_since_last = min(now - last_alert_ts, now - self._last_breaking_sent_ts)
        # Fast-track gate: if less than 90s passed, wait to protect against Telegram flood
        if time_since_last < 90.0:
            return

        pending = []
        for item in self.news_collector.fetch_latest_news():
            news_id = item["id"]
            title = (item.get("title") or "").strip()
            desc = item.get("description", "")

            # Strict relevance & question/opinion rejection
            if not title or "?" in title or not GoldNewsFilter.is_gold_relevant(title, desc):
                continue

            # SQLite check by news_id
            if database.is_news_sent(news_id):
                continue

            # SQLite check by title
            if database.is_title_already_broadcasted(title):
                continue

            # In-memory process check
            if title.lower() in self._broadcasted_titles_cache:
                continue

            # Freshness Gate: strictly reject stale items older than 4 hours
            item_ts = self._news_ts(item)
            if item_ts > 0 and (now - item_ts) > 4 * 3600:
                database.record_news_sent(news_id, title, item.get("source", ""), is_broadcasted=0)
                continue

            pending.append(item)

        if not pending:
            return

        recent_sent_titles = database.get_recent_news_titles(hours=24)
        for it in pending:
            title = it["title"]
            desc = it.get("description", "")

            # Dynamically recalculate gap before evaluating each item
            now = time.time()
            last_alert_ts = float(database.get_state("last_breaking_alert_ts") or "0")
            time_since_last = min(now - last_alert_ts, now - self._last_breaking_sent_ts)

            # Fast-track priority check: critical news gets 90s gap, regular gets BREAKING_ALERT_MIN_GAP (180s = 3m)
            is_critical = any(k in (title + " " + desc).lower() for k in [
                "war", "attack", "missile", "airstrike", "fomc", "rate cut", "rate hike",
                "interest rate", "powell", "kevin warsh", "cpi", "nfp", "emergency", "nuclear"
            ])
            required_gap = 90.0 if is_critical else BREAKING_ALERT_MIN_GAP
            if time_since_last < required_gap:
                logger.debug(f"[BREAKING GAP] {time_since_last:.1f}s elapsed < {required_gap}s required. Deferring to next cycle.")
                break

            if database.is_title_already_broadcasted(title):
                self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                continue

            # Macro Cluster Deduplication & Cooldown Shield (Prevents repeated NFP, Oil, AI, or Fed floods across feeds)
            cluster = GoldNewsFilter.get_news_cluster(title + " " + desc)
            if cluster:
                last_cluster_ts = float(database.get_state(f"cluster_last_ts_{cluster}") or "0")
                # Cooldowns: 4 hours for economic reports (jobs, inflation), 2 hours for Fed, 60 mins for tech/energy/crypto
                cluster_cooldown = 14400.0 if cluster in ("us_jobs", "inflation") else (7200.0 if cluster == "fed_rates" else 3600.0)
                if (now - last_cluster_ts) < cluster_cooldown:
                    logger.info(f"[CLUSTER COOLDOWN] Dropping '{title}' (Cluster: {cluster}, {(now - last_cluster_ts)/60:.1f}m ago < {cluster_cooldown/60}m required).")
                    self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                    database.record_news_sent(it["id"], title, it.get("source", ""), is_broadcasted=0)
                    continue

            if GoldNewsFilter.is_duplicate_or_similar(title, recent_sent_titles):
                self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                continue

            # TRIPLE SHIELD: Check if ALREADY in Telegram channel @GoldMarketKH8888 live feed
            if self._is_already_in_telegram_channel(title, it.get("link", "")):
                logger.info(f"[CHANNEL DEDUPLICATION] '{title}' already in channel feed. Purging from data!")
                self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                database.clear_news_from_data(it["id"], title, it.get("source", ""))
                self._broadcasted_titles_cache.add(title.lower())
                continue

            # Enrich short description if needed
            desc = it.get("description", "")
            if len(desc) < 120:
                desc = self._enrich_article_description(it)
                it["description"] = desc

            analysis = self.analyzer.analyze_breaking_news(title, desc)
            if not analysis:
                continue

            if isinstance(analysis, dict) and analysis.get("is_clear") is False:
                self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                database.record_news_sent(it["id"], title, it.get("source", ""), is_broadcasted=0)
                continue

            impact = ""
            if isinstance(analysis, dict):
                impact = (analysis.get("impact") or "").strip()

            is_positive = "វិជ្ជមាន" in impact and "អវិជ្ជមាន" not in impact
            is_negative = "អវិជ្ជមាន" in impact
            if not (is_positive or is_negative) or "អព្យាក្រឹត" in impact:
                self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                database.record_news_sent(it["id"], title, it.get("source", ""), is_broadcasted=0)
                continue

            msg = KhmerFormatter.format_breaking_event_alert(it, analysis)

            # ZERO ENGLISH LEAKAGE GATE: Ensure the broadcasted body is genuinely translated into Khmer
            narrative_body = (analysis.get("key_event") or analysis.get("what_happened") or "").strip()
            khmer_count = len(re.findall(r'[\u1780-\u17FF]', narrative_body))
            latin_count = len(re.findall(r'[a-zA-Z]', narrative_body))
            if khmer_count < 20 or (latin_count > 0 and (latin_count / (khmer_count + latin_count)) > 0.40):
                logger.warning(f"[REJECTED ENGLISH LEAK] Breaking news '{title}' has untranslated English body (Khmer: {khmer_count}, Latin: {latin_count}). Dropping from broadcast.")
                self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                database.record_news_sent(it["id"], title, it.get("source", ""), is_broadcasted=0)
                continue

            # Re-verify channel feed right before dispatch (with fresh real-time web check)
            if self._is_already_in_telegram_channel(title, it.get("link", ""), khmer_text=msg, fresh=True):
                self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                database.clear_news_from_data(it["id"], title, it.get("source", ""))
                self._broadcasted_titles_cache.add(title.lower())
                continue

            # Lock in-memory and database atomically BEFORE dispatching
            database.clear_news_from_data(it["id"], title, it.get("source", ""))
            self._broadcasted_titles_cache.add(title.lower())
            database.set_state("last_breaking_alert_ts", str(time.time()))
            self._last_breaking_sent_ts = time.time()
            if cluster:
                database.set_state(f"cluster_last_ts_{cluster}", str(time.time()))
            self._cached_channel_html = "" # Invalidate channel cache
            photo = self._fetch_news_image(it)
            if photo:
                caption_text = self._truncate_html_caption(msg, max_visible_chars=950)
                self.notifier.send_photo(photo, caption=caption_text, reply_markup=None)
            else:
                self.notifier.send_message(msg, reply_markup=None)

            # 💥 USER DIRECTIVE: CLEAR FROM DATA IMMEDIATELY AFTER SENDING
            self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
            database.clear_news_from_data(it["id"], title, it.get("source", ""))
            self._broadcasted_titles_cache.add(title.lower())
            pending.clear()

            logger.info(f"[BREAKING NEWS APPROVED & BROADCASTED] '{title}' sent. Data purged immediately. Real-time cadence active.")
            break

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

            # 5.1 Weekly Sunday Outlook (Every Sunday 19:00 Cambodia Time)
            self.check_weekly_sunday_outlook()

            # 5.2 Real-Time Signals & Trade Trailing
            self.check_news_danger_zone()
            self.check_sniper_instant_signals()
            self.check_dynamic_breakeven_trailing()
            self.check_candlestick_confirmation()
            self.check_liquidity_sweep()
            self.check_macro_divergence()

            # 6. Breaking News Alert (Triple Anti-Duplicate Shield)
            self.check_breaking_news()

            # 7. Economic Calendar & Upcoming/Actual News Check
            recommended_interval = self.check_economic_events()
            return recommended_interval
        except Exception as e:
            logger.error(f"Error during bot execution cycle: {e}", exc_info=True)
            return 60

    def _prewarm_cache_worker(self):
        """
        Sub-Second In-Memory RAM Caching Engine (Background Thread).
        Continuously pre-fetches and pre-computes in RAM:
        - 3-Way Triangulated Spot Price (Swissquote + Binance PAXG + COMEX)
        - Technical Key Levels (Pivot, R1/R2, S1/S2)
        - Institutional Order Book Depth & Macro Correlations
        - Decisive AI SMC Setup (Single Direction Plan)
        - Pre-formatted Telegram messages ready for instant 0.001s dispatch.

        This ensures 100% of user clicks ([ Price ] and [ SMC ]) hit the RAM cache
        with ZERO wait time (< 0.05 seconds) and ZERO network latency.
        """
        from collectors.market_cache import market_cache
        logger.info("[RAM Caching Engine] Sub-Second In-Memory Background Worker activated.")
        while True:
            try:
                # 1. Fetch & Triangulate Price (Updates market_cache._price_cache)
                price_data = self.gold_collector.fetch_price(force_refresh=True)
                if price_data:
                    # Pre-format Price Telegram Response in RAM
                    price_msg = KhmerFormatter.format_daily_gold_price(price_data, summary="", include_smc=False)
                    market_cache.set_preformatted_price_msg(price_msg)

                    oz = price_data.get("price_oz", 0.0)
                    levels = price_data.get("key_levels", {})

                    # 2. Fetch Macro & Order Book Depth
                    macro_data = self.macro_collector.fetch_macro_correlations()
                    order_book = self.order_book_tracker.fetch_order_book_depth()

                    # 3. Pre-compute Fast Institutional SMC Setup in RAM (Instant < 1ms, zero API quota use)
                    setup = MacroAnalyzer.generate_smart_smc_setup(
                        current_price=oz,
                        key_levels=levels,
                        macro_data=macro_data,
                        order_book=order_book
                    )
                    if setup:
                        market_cache.set_smc_setup(setup)
                        smc_msg = KhmerFormatter.format_single_smc_setup(setup, key_levels=levels, current_price=oz)
                        market_cache.set_preformatted_smc_msg(smc_msg)

            except Exception as e:
                logger.debug(f"[RAM Caching Engine] Background cycle warning: {e}")

            # Sleep 6 seconds before refreshing cache in background
            time.sleep(6.0)

    def start_loop(self):
        """
        High-Performance Real-Time Autonomous Event Loop.
        - Spawns background Sub-Second RAM Cache pre-warming thread.
        - Polls Telegram incoming user commands continuously every 1-2 seconds for INSTANT response.
        - Schedules and executes background tasks (Economic Calendar, Daily Price, Sessions)
          based on elapsed timestamps without sleeping for 1 hour or blocking commands!
        """
        logger.info("Bot started in ULTRA-FAST REAL-TIME RESPONSIVE MODE.")
        
        # Start Proactive Sub-Second RAM Cache Pre-warmer in dedicated daemon thread
        import threading
        cache_thread = threading.Thread(target=self._prewarm_cache_worker, daemon=True, name="RAM-Prewarmer")
        cache_thread.start()

        last_background_check = 0.0
        background_interval = 60  # Initial background check interval
        last_breaking_check = 0.0
        breaking_interval = 10.0  # Ultra-fast real-time breaking news monitor (every 10s)
        last_signal_check = 0.0
        signal_interval = 30.0    # Real-time high-speed signals & trade trailing monitor (every 30s)

        while True:
            try:
                # 1. Real-time Telegram Command Listener (Instant response < 1s)
                self.process_incoming_commands()

                now = time.time()
                # 2. Real-Time Breaking News Check (Dedicated cadence with Triple Anti-Duplicate Shield)
                if now - last_breaking_check >= breaking_interval:
                    last_breaking_check = now
                    try:
                        self.check_breaking_news()
                    except Exception as err:
                        logger.error(f"Error checking breaking news: {err}", exc_info=True)

                # 3. Real-Time Sniper Signals & Trade Trailing Check (Dedicated 30-second cadence)
                if now - last_signal_check >= signal_interval:
                    last_signal_check = now
                    try:
                        self.check_news_danger_zone()
                        self.check_sniper_instant_signals()
                        self.check_dynamic_breakeven_trailing()
                        self.check_candlestick_confirmation()
                        self.check_liquidity_sweep()
                        self.check_macro_divergence()
                    except Exception as err:
                        logger.error(f"Error checking signals or trade trailing: {err}", exc_info=True)

                # 4. Scheduled & Periodic Tasks Checker (Non-blocking)
                if now - last_background_check >= background_interval:
                    last_background_check = now
                    try:
                        self.check_database_maintenance()
                        self.check_daily_gold_price()
                        self.check_session_open_alerts()
                        self.check_weekly_sunday_outlook()
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

