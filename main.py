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
    DAILY_PRICE_MORNING_HOUR, DAILY_PRICE_EVENING_HOUR,
    INTERVAL_NORMAL, INTERVAL_UPCOMING, INTERVAL_HIGH_IMPACT,
    BREAKING_ALERT_MIN_GAP, MAX_DAILY_BREAKING_NEWS
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
    from story_image_builder import StoryImageBuilder
except ImportError:
    try:
        from collectors.story_image_builder import StoryImageBuilder
    except ImportError:
        StoryImageBuilder = None

try:
    from story_video_builder import StoryVideoBuilder
except ImportError:
    try:
        from collectors.story_video_builder import StoryVideoBuilder
    except ImportError:
        StoryVideoBuilder = None

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

try:
    from semantic_deduplicator import SemanticEventDeduplicator
except ImportError:
    try:
        from analyzers.semantic_deduplicator import SemanticEventDeduplicator
    except ImportError:
        SemanticEventDeduplicator = None

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
        self._enforce_single_instance_lock()
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

    def _enforce_single_instance_lock(self):
        """
        Guarantees 100% single-instance execution using bot.lock file.
        If an older or orphaned bot process is found running, terminates it immediately.
        Acquires exclusive OS-level PID registration to prevent concurrent runs physically.
        """
        import os
        import sys
        import atexit
        lock_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.lock")
        current_pid = os.getpid()
        
        # Check if lock file exists
        if os.path.exists(lock_file_path):
            try:
                with open(lock_file_path, "r", encoding="utf-8") as f:
                    old_pid_str = f.read().strip()
                if old_pid_str.isdigit():
                    old_pid = int(old_pid_str)
                    if old_pid != current_pid:
                        try:
                            import psutil
                            if psutil.pid_exists(old_pid):
                                proc = psutil.Process(old_pid)
                                logger.warning(f"[PROCESS LOCK] Detected older orphaned bot process (PID: {old_pid}). Terminating it now...")
                                proc.terminate()
                                proc.wait(timeout=3)
                        except Exception:
                            try:
                                if os.name == 'nt':
                                    os.system(f"taskkill /PID {old_pid} /F >nul 2>&1")
                                else:
                                    os.kill(old_pid, 9)
                            except Exception:
                                pass
            except Exception as e:
                logger.warning(f"[PROCESS LOCK] Error checking old lock: {e}")

        # Write current PID
        try:
            with open(lock_file_path, "w", encoding="utf-8") as f:
                f.write(str(current_pid))
            def _cleanup_lock():
                try:
                    if os.path.exists(lock_file_path):
                        with open(lock_file_path, "r", encoding="utf-8") as f:
                            if f.read().strip() == str(current_pid):
                                os.remove(lock_file_path)
                except Exception:
                    pass
            atexit.register(_cleanup_lock)
            logger.info(f"[PROCESS LOCK] Acquired exclusive single-instance lock for PID {current_pid}.")
        except Exception as e:
            logger.warning(f"[PROCESS LOCK] Could not write lock file: {e}")

    def _start_self_pinger(self):
        """Pings public URL every 8 minutes to prevent Render Free Tier from idling or sleeping."""
        try:
            import threading
            import urllib.request
            def pinger_worker():
                url = os.getenv("RENDER_EXTERNAL_URL", "https://xauusd-news-bot-jcc9.onrender.com")
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

    def _fetch_channel_html(self, max_cache_age: float = 180.0) -> str:
        """Caches public Telegram channel feed HTML for 180s to prevent bandwidth waste, spamming Telegram web, and event loop lag."""
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
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                self._cached_channel_html = html
                self._cached_channel_html_ts = now
                return html
        except Exception as e:
            logger.debug(f"[Channel HTML Fetch] {e}")
            return getattr(self, "_cached_channel_html", "")

    def _bootstrap_news_cache(self):
        """
        On startup, seeds existing headlines that are either older than 30 minutes,
        already posted, or part of initial backlog, so only fresh news arriving
        AFTER startup is processed for breaking alerts. Prevents restart/deploy floods.
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
                
                # Only seed items that are genuinely stale (> 30 mins) or already in Telegram channel
                is_stale = item_ts == 0.0 or (now - item_ts) > 1800.0
                is_in_channel = self._is_already_in_telegram_channel(title, link) if channel_html else False
                
                if is_stale or is_in_channel:
                    if title:
                        self._broadcasted_titles_cache.add(title.lower())
                    self.news_collector.clear_item(news_id=news_id, link=link, title=title)
                    if news_id and not database.is_news_sent(news_id):
                        database.record_news_sent(news_id, title, item.get("source", ""), is_broadcasted=1 if is_in_channel else 0)
                    bootstrapped_count += 1
                else:
                    logger.info(f"[Startup News Sync] Preserving fresh active breaking news: '{title}'")
            logger.info(f"[Startup News Sync] Seeded {bootstrapped_count} initial backlog headlines (fresh news preserved).")
        except Exception as e:
            logger.warning(f"[Startup News Sync] Warning: {e}")

    def _is_daily_price_already_in_channel(self, date_str: str, session_keyword: str = "") -> bool:
        """Inspects live channel feed to verify if daily gold price was already broadcasted for this session."""
        try:
            channel_html = self._fetch_channel_html(max_cache_age=300.0)
            if date_str in channel_html:
                if not session_keyword:
                    return True
                kw = "ព្រឹក" if "ព្រឹក" in session_keyword else "យប់"
                if session_keyword in channel_html or kw in channel_html:
                    return True
                return False
        except Exception as e:
            logger.debug(f"[Channel Gold Price Check] {e}")
        return False

    def check_daily_gold_price(self):
        """Checks if daily gold price message needs to be sent at 07:00 AM and 07:00 PM Cambodia Time (twice per day)."""
        now_kh = datetime.now(CAMBODIA_TZ)
        today_str = now_kh.strftime("%Y-%m-%d")

        # 1. Determine active gold price broadcast slot
        # Morning window: 07:00 - 09:59 AM Cambodia Time
        # Evening window: 19:00 - 21:59 PM Cambodia Time
        # Prevents missing the broadcast if Render dyno or local process reboots after schedule
        if DAILY_PRICE_MORNING_HOUR <= now_kh.hour <= 9:
            session_type = "morning"
            session_key = f"{today_str}_morning"
            session_label = "07:00 ព្រឹក"
        elif DAILY_PRICE_EVENING_HOUR <= now_kh.hour <= 21:
            session_type = "evening"
            session_key = f"{today_str}_evening"
            session_label = "07:00 យប់"
        else:
            return

        # 2. In-memory lock guard (already broadcasted during current process session)
        if session_key in self._daily_price_locks:
            return
        if session_type == "morning" and today_str in self._daily_price_locks:
            return

        # 3. Database SQLite persistence guard (only counts confirmed broadcasts where message_id > 0)
        # Supports session_key and legacy today_str format for morning
        if database.is_daily_price_sent(session_key) or (session_type == "morning" and database.is_daily_price_sent(today_str)):
            self._daily_price_locks.add(session_key)
            return

        # 3.5 Live channel verification guard (check if today's date and session are already on channel)
        date_formatted = now_kh.strftime("%d/%m/%Y")
        if self._is_daily_price_already_in_channel(date_formatted, session_keyword=session_label):
            self._daily_price_locks.add(session_key)
            try:
                database.record_daily_price_sent(session_key, 999999)
            except Exception:
                pass
            return

        # 4. Trigger Daily Gold Price broadcast (07:00 AM or 07:00 PM)
        self._daily_price_locks.add(session_key)
        logger.info(f"Triggering {session_label} Daily Gold Price broadcast for {today_str} ({session_type})...")
        price_data = self.gold_collector.fetch_price(force_refresh=True)

        # Render Ultra-HD Graphic Card per user design specification
        card_png = self.gold_card_builder.build_card_png(price_data, session=session_type) if self.gold_card_builder else None
        if card_png:
            res = self.notifier.send_photo(card_png, caption="", reply_markup=None)
        else:
            msg = KhmerFormatter.format_daily_gold_price(price_data, session_time=session_label)
            res = self.notifier.send_message(msg, auto_pin=False, reply_markup=None)

        msg_id = res.get("result", {}).get("message_id") if res else None
        if msg_id:
            database.record_daily_price_sent(session_key, msg_id)
            logger.info(f"Daily Gold Price broadcast completed for {session_key} ({session_label}) (msg_id: {msg_id}).")
        else:
            logger.error(f"Failed to broadcast Daily Gold Price for {session_key}: {res}")

    def _is_session_alert_already_in_channel(self, session_keyword: str) -> bool:
        """Inspects live Telegram channel feed to verify if session open alert was already broadcasted today."""
        try:
            channel_html = self._fetch_channel_html(max_cache_age=300.0)
            # If session keyword (e.g. 'LONDON SESSION OPENING' or 'NEW YORK SESSION OPENING') is already in channel
            if session_keyword.upper() in channel_html.upper():
                return True
        except Exception as e:
            logger.debug(f"[Channel Session Check] {e}")
        return False

    def _is_session_alert_sent(self, key: str, session_keyword: str = "") -> bool:
        if key in self._session_alert_locks:
            return True
        if database.get_state(key):
            self._session_alert_locks.add(key)
            return True
        if session_keyword and self._is_session_alert_already_in_channel(session_keyword):
            self._session_alert_locks.add(key)
            try:
                database.set_state(key, "sent")
            except Exception:
                pass
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
        [PERMANENTLY DISABLED PER USER DIRECTIVE]
        Market Session Open Alerts (London 14:00 & New York 19:00 Cambodia Time) are permanently disabled.
        No alerts or heatmaps will ever be broadcasted to Telegram channels or groups.
        """
        return



    def check_candlestick_confirmation(self):
        """[PERMANENTLY DISABLED PER USER DIRECTIVE] Trade signals permanently disabled."""
        return

    def check_news_danger_zone(self):
        """[PERMANENTLY DISABLED PER USER DIRECTIVE] Trade danger alerts permanently disabled."""
        return

    def check_sniper_instant_signals(self):
        """[PERMANENTLY DISABLED PER USER DIRECTIVE] Trade Signals (Point 5) permanently disabled."""
        return

    def check_dynamic_breakeven_trailing(self):
        """[PERMANENTLY DISABLED PER USER DIRECTIVE] Trade Trailing (Point 5) permanently disabled."""
        return

    def check_liquidity_sweep(self):
        """[PERMANENTLY DISABLED PER USER DIRECTIVE] Liquidity Sweep alerts permanently disabled."""
        return

    def check_macro_divergence(self):
        """[PERMANENTLY DISABLED PER USER DIRECTIVE] Macro Divergence alerts permanently disabled."""
        return



    def check_weekly_sunday_outlook(self):
        """
        🚫 USER DIRECTIVE: Permanently disabled Weekly Sunday Gold Outlook alert.
        Weekly Gold Outlook (🏛️ WEEKLY GOLD OUTLOOK) is banned permanently from the channel.
        """
        return

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
            try:
                import gc
                gc.collect()
            except Exception:
                pass
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

            # Admin Recall / Delete Commands (Instant Remote Control to remove flawed post from channel)
            if clean_cmd in ("/recall", "/delete", "/del"):
                from_user_id = msg_obj.get("from", {}).get("id") or chat_id
                is_admin = self.notifier.is_user_admin_of_channel(from_user_id) if hasattr(self.notifier, "is_user_admin_of_channel") else True
                if is_admin:
                    parts = text.split()
                    del_id = None
                    if len(parts) > 1 and parts[1].isdigit():
                        del_id = int(parts[1])
                    else:
                        last_saved = database.get_state("last_channel_post_id")
                        if last_saved and last_saved.isdigit():
                            del_id = int(last_saved)

                    if del_id:
                        ok = self.notifier.delete_message(del_id)
                        if ok:
                            self.notifier.send_message(f"🗑️ <b>បានលុបសារ #{del_id} ចេញពី Channel រួចរាល់ដោយជោគជ័យ!</b>", chat_id=chat_id)
                        else:
                            self.notifier.send_message(f"⚠️ មិនអាចលុបសារ #{del_id} បានទេ (សារអាចត្រូវបានលុបរួចហើយ ឬចាស់ហួស ៤៨ ម៉ោង)។", chat_id=chat_id)
                    else:
                        self.notifier.send_message("ℹ️ សូមបញ្ជាក់ Message ID ឧ. <code>/delete 2340</code> ឬវាយ <code>/recall</code> ដើម្បីលុបសារចុងក្រោយ។", chat_id=chat_id)
                else:
                    self.notifier.send_message("⛔ លោកអ្នកមិនមានសិទ្ធិ Admin ក្នុងការបញ្ជាលុបសារក្នុង Channel ឡើយ!", chat_id=chat_id)
                continue

            elif clean_cmd in ("/stats", "/winrate", "stats", "winrate") or "ស្ថិតិ" in text:
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
                fed_items = [it for it in self.news_collector.fetch_latest_news() if any(k in it['title'].lower() for k in ['fed', 'fomc', 'federal reserve', 'fed chair', 'monetary policy', 'warsh'])]
                target = None
                interp = None
                if fed_items:
                    target = fed_items[0]
                    interp = self.fomc_interpreter.interpret_powell_speech(f"{target['title']}\n{target.get('description', '')}", event_title=target['title'])
                else:
                    target = {"title": "Fed Governor Kevin Warsh Speech on Economic Outlook & Monetary Policy"}
                    interp = self.fomc_interpreter.interpret_powell_speech(target['title'], event_title=target['title'])

                if interp:
                    resp = KhmerFormatter.format_fomc_speech_alert(target['title'], interp)
                    speaker_key = interp.get("speaker") or target['title']
                    photo_bytes = self._get_speaker_photo(speaker_key)
                    if photo_bytes:
                        self.notifier.send_photo(photo_bytes, caption=resp, chat_id=chat_id, reply_markup=bottom_keyboard)
                    else:
                        self.notifier.send_message(resp, chat_id=chat_id, reply_markup=bottom_keyboard)
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
    def _truncate_html_caption(text: str, max_visible_chars: int = 574) -> str:
        """Safely trims narrative text while strictly preserving header, impact line, and clickable source link to stay strictly <= max_visible_chars visible characters."""
        vis_len = len(re.sub(r"<[^>]+>", "", text))
        if vis_len <= max_visible_chars:
            return text

        blocks = text.split("\n\n")
        if len(blocks) <= 1:
            clean = re.sub(r"<[^>]+>", "", text)
            return clean[:max_visible_chars].rstrip(" .…-–—") + "។"

        header = blocks[0]
        source_line = blocks[-1]

        # Check if second to last block is impact_line
        impact_line = ""
        body_blocks = []
        _impact_prefixes = ("🔹", "🔸", "🔶", "🔴", "🟢", "ផល", "ឥទ្ធិពល", "វាផល", "ហានិភ័យ")
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
        clean_body = re.sub(r"<[^>]+>", "", body)

        vis_header = len(re.sub(r"<[^>]+>", "", header))
        vis_source = len(re.sub(r"<[^>]+>", "", source_line))
        vis_impact = len(re.sub(r"<[^>]+>", "", impact_line))
        num_separators = sum(1 for p in [header, clean_body, impact_line, source_line] if p) - 1
        sep_overhead = max(num_separators, 1) * 2

        avail = max(40, max_visible_chars - (vis_header + vis_source + vis_impact + sep_overhead))

        if len(clean_body) > avail:
            sub = clean_body[:avail]
            last_period = max(sub.rfind("។ "), sub.rfind("។\n"), sub.rfind("។"))
            if last_period > 30:
                trimmed_body = sub[:last_period + 1].strip()
            else:
                last_space = sub.rfind(" ")
                if last_space > 25:
                    trimmed_body = sub[:last_space].strip() + "។"
                else:
                    trimmed_body = sub.strip() + "។"
        else:
            trimmed_body = clean_body

        parts = [p for p in [header, trimmed_body, impact_line, source_line] if p]
        res = "\n\n".join(parts)

        # Progressive hard clamp to guarantee strictly <= max_visible_chars
        while len(re.sub(r"<[^>]+>", "", res)) > max_visible_chars and len(trimmed_body) > 30:
            excess = len(re.sub(r"<[^>]+>", "", res)) - max_visible_chars
            cut_idx = max(len(trimmed_body) - excess - 5, 20)
            sub = trimmed_body[:cut_idx]
            last_period = max(sub.rfind("។ "), sub.rfind("។\n"), sub.rfind("។"))
            if last_period > 20:
                trimmed_body = sub[:last_period + 1].strip()
            else:
                last_space = sub.rfind(" ")
                trimmed_body = (sub[:last_space].strip() if last_space > 15 else sub.strip()) + "។"
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
        pd = item.get("pub_date", "")
        if not pd:
            return 0.0
        try:
            from collectors.breaking_news import BreakingNewsCollector
            return BreakingNewsCollector.parse_pub_date(pd)
        except Exception:
            try:
                from email.utils import parsedate_to_datetime
                return parsedate_to_datetime(pd).timestamp()
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
    def _fetch_direct_publisher_image(item: dict) -> bytes:
        """
        Extracts genuine direct article image from feed or deep article webpage (og:image / twitter:image / json-ld),
        with high-definition CDN upgrading, Google News token decoding, and live editorial search fallback.
        """
        try:
            from collectors.internet_image_fetcher import InternetImageFetcher
            return InternetImageFetcher.fetch_image_for_news(item)
        except Exception as e:
            logger.debug(f"[InternetImageFetcher error] {e}")
            return None

    @staticmethod
    def _fetch_news_image(item: dict, analysis: dict = None) -> bytes:
        """
        Retrieves or synthesizes the most authentic, story-accurate image matching the narrative:
        1. Dual-Leader Split Image (Meloni + Trump, Trump + Putin, etc.)
        2. Dual-Country Flag Split Image (India + Canada, US + China, etc.)
        3. Single Leader Official Portrait
        4. Direct Verified Publisher Article Photo / Live Editorial Press Photo
        5. Macro Topic Authentic Ultra-HD Photo
        6. Single Country High-Res Flag Canvas
        """
        if StoryImageBuilder:
            try:
                img_bytes = StoryImageBuilder.get_image_for_news(
                    item,
                    analysis=analysis,
                    default_fetcher=XAUUSDNewsAssistantBot._fetch_direct_publisher_image
                )
                if img_bytes:
                    return img_bytes
            except Exception as e:
                logger.warning(f"[StoryImageBuilder] Error in get_image_for_news: {e}")

        # Fallback to direct internet image fetcher if builder is unavailable
        direct = XAUUSDNewsAssistantBot._fetch_direct_publisher_image(item)
        if direct:
            return direct

        # MODE B GUARANTEE: If no authentic article photo from publisher or dynamic canvas exists,
        # return None so the message broadcasts cleanly in MODE B (Clean VIP Text Mode)!
        logger.info("[_fetch_news_image] No authentic direct photo. Defaulting to MODE B (Clean VIP Text Mode).")
        return None

    @staticmethod
    def _fetch_news_video(item: dict, analysis: dict = None):
        """
        Retrieves or probes an authentic HD video clip (.mp4) for ultra-important news events.
        If available, the news will be broadcasted with authentic streaming video!
        """
        if StoryVideoBuilder:
            try:
                v_data = StoryVideoBuilder.fetch_story_video(item, analysis=analysis)
                if v_data:
                    return v_data
            except Exception as e:
                logger.debug(f"[StoryVideoBuilder] Error in fetch_story_video: {e}")
        return None

    @staticmethod
    def _get_speaker_photo(text_low: str) -> bytes:
        """Returns official portrait bytes for key leaders/speakers if available."""
        return None

    @staticmethod
    def _get_topic_photo(text_low: str) -> bytes:
        """
        Permanently disabled: Static topic stock photos (semiconductor_chips, etc.)
        are completely banned to prevent repeating the same generic images 20-30 times.
        Always returns None to enforce Mode B clean text broadcast.
        """
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
        fetch_max_age = 5.0 if getattr(self, "_has_waiting_actual", False) else 15.0
        events = self.calendar_collector.fetch_events(max_age=fetch_max_age)
        
        has_imminent_event = False
        has_waiting_actual = False

        for ev in events:
            ev_id = ev["id"]
            release_dt = ev["release_dt"]
            diff_seconds = (release_dt - now_kh).total_seconds()
            diff_minutes = int(diff_seconds // 60)

            # --- MODE 2: UPCOMING NEWS REMINDERS (PERMANENTLY DISABLED PER USER DIRECTIVE) ---
            # All 15-minute and 5-minute countdown reminders ("🚨 5 នាទីទៀតដល់ម៉ោងចេញទិន្នន័យសំខាន់! (5-MIN COUNTDOWN)")
            # are permanently banned and disabled to keep the channel clean and free from clutter.

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
                        spot_price_str = ""
                        try:
                            if hasattr(self, "gold_collector") and self.gold_collector:
                                spot = self.gold_collector.get_spot_gold_price()
                                if spot and spot.get("price"):
                                    spot_price_str = f"${float(spot['price']):,.2f}"
                        except Exception:
                            pass

                        msg = KhmerFormatter.format_actual_release_alert(ev, analysis, spot_price=spot_price_str)

                        # Ultra-fast sub-second text alert (Zero chart rendering latency per user directive)
                        self.notifier.send_message(msg)

                        database.record_event_stage(
                            ev_id, ev["title"], ev["currency"], ev["release_time_str"], 
                            "actual", actual_val=actual_val, forecast_val=ev.get("forecast", "")
                        )
                else:
                    # Event is past due, but Actual has not published yet -> Poll frequently
                    has_waiting_actual = True

        self._has_waiting_actual = has_waiting_actual
        if has_waiting_actual:
            return 5  # Ultra-fast 5s polling when waiting for high-impact actual release numbers
        elif has_imminent_event:
            return 15 # Responsive 15s cadence when high-impact event is imminent
        else:
            return 30  # Responsive 30s cadence to never miss timely actual release updates

    def _channel_time_since_last_post(self) -> float:
        """Returns elapsed seconds since the latest message was published in @GoldMarketKH8888 live channel feed."""
        try:
            import datetime
            channel_html = self._fetch_channel_html(max_cache_age=0.0)
            times = re.findall(r'<time[^>]*datetime="([^"]+)"', channel_html)
            if times:
                last_dt = datetime.datetime.fromisoformat(times[-1])
                now_utc = datetime.datetime.now(datetime.timezone.utc)
                elapsed = (now_utc - last_dt).total_seconds()
                return max(0.0, elapsed)
        except Exception as e:
            logger.debug(f"[Channel Post Time Check] {e}")
        return 999999.0

    def _get_channel_live_feed_state(self):
        """
        Extracts live channel state directly from @GoldMarketKH8888 HTML feed across multiple posts.
        Returns (channel_elapsed_seconds, latest_clusters, latest_entities, recent_clusters_dict, recent_entities_dict).
        Provides an indestructible shield across Render container restarts!
        """
        try:
            import datetime
            import html as html_module
            channel_html = self._fetch_channel_html(max_cache_age=15.0)
            if not channel_html:
                return (999999.0, [], [], {}, {})

            now_utc = datetime.datetime.now(datetime.timezone.utc)
            pattern = re.compile(
                r'<div class="tgme_widget_message_wrap[^"]*"[^>]*>.*?'
                r'data-post="GoldMarketKH8888/(\d+)".*?'
                r'<time datetime="([^"]+)".*?'
                r'<div class="tgme_widget_message_(?:text|caption)[^"]*"[^>]*>(.*?)</div>',
                re.DOTALL
            )
            matches = pattern.findall(channel_html)

            ch_elapsed = 999999.0
            ch_latest_clusters = []
            ch_latest_entities = []
            ch_recent_clusters = {}
            ch_recent_entities = {}
            ch_recent_story_texts = []

            if matches:
                last_pid, last_time, last_text = matches[-1]
                try:
                    last_dt = datetime.datetime.fromisoformat(last_time)
                    ch_elapsed = max(0.0, (now_utc - last_dt).total_seconds())
                except Exception:
                    pass
                clean_last = html_module.unescape(re.sub(r'<[^>]+>', ' ', last_text)).strip()
                ch_latest_clusters = GoldNewsFilter.get_news_clusters(clean_last)
                ch_latest_entities = GoldNewsFilter.get_news_entities(clean_last)

                for pid, ptime, ptext in matches:
                    try:
                        p_dt = datetime.datetime.fromisoformat(ptime)
                        p_elapsed = max(0.0, (now_utc - p_dt).total_seconds())
                    except Exception:
                        continue
                    clean_p = html_module.unescape(re.sub(r'<[^>]+>', ' ', ptext)).strip()
                    p_clusters = GoldNewsFilter.get_news_clusters(clean_p)
                    p_entities = GoldNewsFilter.get_news_entities(clean_p)

                    if p_elapsed < 14400.0:  # 4 hours
                        for ent in p_entities:
                            ch_recent_entities[ent] = min(ch_recent_entities.get(ent, 999999.0), p_elapsed)
                    if p_elapsed < 7200.0:   # 2 hours
                        for cl in p_clusters:
                            ch_recent_clusters[cl] = min(ch_recent_clusters.get(cl, 999999.0), p_elapsed)
                    if p_elapsed < 21600.0 and len(clean_p) >= 30:  # 6 hours of recent narrative context
                        ch_recent_story_texts.append(clean_p)

            return (ch_elapsed, ch_latest_clusters, ch_latest_entities, ch_recent_clusters, ch_recent_entities, ch_recent_story_texts)
        except Exception as e:
            logger.debug(f"[Channel Live State Check] {e}")
            return (999999.0, [], [], {}, {}, [])

    def _is_image_already_in_channel(self, photo_bytes: bytes) -> bool:
        """Inspects recently used image hashes and channel feed to strictly guarantee ZERO repetitive images over 24 hours!"""
        if not photo_bytes or len(photo_bytes) < 1000:
            return False
        try:
            import hashlib
            now = time.time()
            img_hash = hashlib.md5(photo_bytes[:4000]).hexdigest()
            last_used = float(database.get_state(f"channel_img_ts_{img_hash}") or "0")
            if (now - last_used) < 86400.0:  # Strict 24 hours
                logger.info(f"[IMAGE REPETITION SHIELD] Image MD5 {img_hash[:8]} was already used {(now - last_used)/3600:.1f}h ago. Rejecting!")
                return True

            dh = database.calculate_image_dhash(photo_bytes)
            if dh and database.is_image_dhash_duplicate(dh, max_age_seconds=86400.0, max_hamming_dist=10):
                logger.info(f"[IMAGE PERCEPTUAL SHIELD] Image visually matches a broadcast within 24h (dHash={dh}). Rejecting!")
                return True

            database.set_state(f"channel_img_ts_{img_hash}", str(now))
            return False
        except Exception as e:
            logger.debug(f"[_is_image_already_in_channel error] {e}")
            return False

    def audit_live_channel_and_heal(self):
        """
        Autonomous Channel Self-Healing & Defect Purge Engine:
        Continuously guards the Telegram Channel (@GoldMarketKH8888):
        1. Auto-Purge (លុបបញ្ហាខុស & លុបជាន់):
           - Prohibited interactive polls (e.g. 📊 លទ្ធផល Signal)
           - Prohibited news countdowns (e.g. 🚨 5 នាទីទៀត)
           - Prohibited trade signals (Entry Zone, TP1, SL)
           - Corrupted broken stubs (< 70 chars without photo/meaning)
           - Multi-post duplicate detection across recent posts (Jaccard similarity >= 0.65)
        2. Auto-Heal In-Place (ប្រព័ន្ធចាប់ខុស & កែរកំហុស):
           - Fixes missing head (prepend country/macro flag if missing)
           - Fixes missing verbs (e.g. នេះពីការ -> នេះបង្ហាញពីការ)
           - Scans recent posts for spelling typos (using sanitize_khmer_spelling)
           - Normalizes excessive spacing, fixes country-verb spacing
           - Sentence-aware character limit enforcement (<= 574 for photo, <= 750 for text)
           - Auto-edits caption or text in-place without deleting the post!
        """
        now = time.time()
        if (now - getattr(self, "_last_channel_audit_ts", 0)) < 3.0:
            return
        self._last_channel_audit_ts = now

        try:
            import html as html_module
            from formatters.khmer_formatter import sanitize_khmer_spelling

            if not hasattr(self, "_healed_posts_cache"):
                self._healed_posts_cache = {}

            channel_html = self._fetch_channel_html(max_cache_age=2.0)
            if not channel_html:
                return

            parts = channel_html.split('<div class="tgme_widget_message_wrap')
            posts = []
            for part in parts[1:]:
                m_id = re.search(r'data-post="GoldMarketKH8888/(\d+)"', part)
                if not m_id:
                    continue
                pid = int(m_id.group(1))

                m_text = re.search(r'<div class="tgme_widget_message_(?:text|caption)[^"]*"[^>]*>(.*?)</div>', part, re.DOTALL)
                clean_html = m_text.group(1) if m_text else ""

                # convert <br> to newline
                cleaned_br = re.sub(r'<br\s*/?>', '\n', clean_html)
                clean_text = html_module.unescape(re.sub(r'<[^>]+>', ' ', cleaned_br)).strip()
                clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)

                m_photos = re.findall(r'background-image:url\(\'([^\']+)\'\)', part)
                real_photos = [p for p in m_photos if 'emoji' not in p]
                photo_url = real_photos[0] if real_photos else None
                has_photo = bool(real_photos)
                has_video = bool(re.search(r'tgme_widget_message_video|tgme_widget_message_roundvideo|<video', part))

                posts.append({
                    "id": pid,
                    "text": clean_text,
                    "raw_html": clean_html,
                    "photo_url": photo_url,
                    "has_photo": has_photo or has_video,
                    "has_video": has_video
                })

            if not posts:
                return

            # --- 1. DEFECT PURGE & MULTI-POST DEDUPLICATION (លុបបញ្ហាខុស & លុបជាន់) ---
            seen_headlines = {}
            for p in list(posts):
                pid = p["id"]
                txt = p["text"]
                has_photo = p["has_photo"]

                # A. Severe defect & prohibited content check (INSTANT AUTO-PURGE)
                is_prohibited = False
                purge_reason = ""
                
                # Check 1: Empty or corrupted stub (< 40 chars)
                if len(txt) < 40 and "ហាងឆេងមាស" not in txt:
                    is_prohibited = True
                    purge_reason = f"Corrupted/Empty Stub ({len(txt)} chars)"
                # Check 2: Prohibited polls
                elif "📊 លទ្ធផល Signal" in txt or "📊 បោះឆ្នោត" in txt:
                    is_prohibited = True
                    purge_reason = "Prohibited Poll"
                # Check 3: Prohibited countdown alerts
                elif "🚨 5 នាទីទៀត" in txt or "🚨 15 នាទីទៀត" in txt or "COUNTDOWN" in txt:
                    is_prohibited = True
                    purge_reason = "Prohibited Countdown Alert"
                # Check 4: Prohibited trade signals
                elif any(sig in txt for sig in ["Entry Zone:", "Stop Loss:", "TP1:", "TP2:"]) and "ហាងឆេងមាស" not in txt:
                    is_prohibited = True
                    purge_reason = "Prohibited Trade Signal"
                # Check 5: Forbidden non-VIP meme emojis
                elif re.search(r'[🚀🔥💥💰🎉🤑💩🤡]', txt):
                    is_prohibited = True
                    purge_reason = "Forbidden Meme Emojis"
                # Check 6: Contradictory war sentiment with positive badge
                elif any(w in txt for w in ['សង្គ្រាម', 'វាយប្រហារ', 'ដ្រូន', 'មីស៊ីល', 'ទាហាន', 'ស្លាប់', 'ផ្ទុះ', 'សមរភូមិ']) and '🔹 ផលវិជ្ជមាន' in txt:
                    is_prohibited = True
                    purge_reason = "Contradictory Positive Sentiment on War/Conflict"
                # Check 7: Gross length violation that exceeds ceiling by > 100 chars
                elif (has_photo and len(txt) > 674) or (not has_photo and len(txt) > 850):
                    is_prohibited = True
                    purge_reason = f"Gross Length Violation ({len(txt)} chars)"

                if is_prohibited:
                    logger.critical(f"[AUTONOMOUS SEVERE ERROR PURGE] Deleting defective post #{pid} ({purge_reason}) from channel!")
                    self.notifier.delete_message(pid)
                    posts = [post for post in posts if post["id"] != pid]
                    continue

                # B. Multi-post Duplicate Check (Jaccard similarity >= 0.60)
                lines = [l.strip() for l in txt.split('\n') if l.strip()]
                if lines and "ហាងឆេងមាស" not in lines[0]:
                    hl = lines[0]
                    norm_tokens = set(re.findall(r'[\u1780-\u17FF]{3,}|[a-zA-Z]{3,}', hl.lower()))
                    if norm_tokens:
                        is_dup = False
                        for prev_pid, prev_tokens in seen_headlines.items():
                            overlap = len(norm_tokens.intersection(prev_tokens))
                            union = len(norm_tokens.union(prev_tokens))
                            jaccard = overlap / union if union else 0
                            if jaccard >= 0.60:
                                logger.critical(f"[AUTONOMOUS DUPLICATE PURGE] Duplicate post #{pid} matches #{prev_pid} (Jaccard {jaccard:.2f}). Deleting immediately!")
                                self.notifier.delete_message(pid)
                                posts = [post for post in posts if post["id"] != pid]
                                is_dup = True
                                break
                        if not is_dup:
                            seen_headlines[pid] = norm_tokens

            # --- 2. AUTO-HEAL IN-PLACE (ប្រព័ន្ធចាប់ខុស & កែរកំហុស) ---
            for p in posts[-15:]:
                pid = p["id"]
                txt = p["text"]
                has_photo = p["has_photo"]
                if not txt:
                    continue

                # Run spelling sanitization
                fixed = sanitize_khmer_spelling(txt)
                # Fix missing verbs (e.g. នេះពីការ -> នេះបង្ហាញពីការ)
                fixed = re.sub(r'(ការសម្រេចចិត្ត|ស្ថានភាព|វិធានការ|សកម្មភាព|របាយការណ៍)នេះ\s*ពីការ', r'\1នេះបង្ហាញពីការ', fixed)
                fixed = re.sub(r'ភាពងុបងុល', 'ភាពប្រែប្រួល', fixed)
                # Normalize excessive spaces
                fixed = re.sub(r'[ \t]{2,}', ' ', fixed)
                fixed = re.sub(r'([🔸🔹🔴🟢🔶])\s{2,}', r'\1 ', fixed)
                # Country-verb spacing
                fixed = re.sub(r'(យេមែន|រុស្ស៊ី|អ៊ុយក្រែន|ចិន|អាមេរិក|បារាំង|អាល្លឺម៉ង់|អ៊ីរ៉ង់|អ៊ីស្រាអែល|តួកគី|ជប៉ុន|កូរ៉េខាងត្បូង|កូរ៉េខាងជើង|តៃវ៉ាន់|កាណាដា|អង់គ្លេស|ឥណ្ឌា)(កំពុង|បាន|ត្រូវបាន|អាច|នឹង|គ្រោង|ប្រកាស)', r'\1 \2', fixed)

                lines = [l.strip() for l in fixed.split('\n') if l.strip()]
                if not lines:
                    continue

                # Strip unwanted non-country emojis (🛢️, 📈, ⚠️, 🚨) from headline but PRESERVE 🌐
                if "ហាងឆេងមាស" not in lines[0]:
                    lines[0] = re.sub(r'^[🛢📈⚠️🚨\ufe0f\s]+', '', lines[0]).strip()
                    # Ensure headline has at least a sovereign flag or country flag
                    if not re.search(r'[\U0001F1E0-\U0001F1FF]{2}|🌐', lines[0]):
                        lines[0] = f"🌐 {lines[0]}"

                # Tail & formatting check: Clean trailing colons, ellipsis, or hanging prepositions in headline
                lines[0] = re.sub(r'[\s\u200B\u200C\u200D\uFEFF\u00A0.,;:៖–—_…]+$', '', lines[0]).strip()
                lines[0] = re.sub(r'\s+(?:នៃ|របស់|និង|ពី|ក្នុង|ដើម្បី|លើ|អំពី)\s*$', '', lines[0]).strip()

                hl_text = lines[0]
                body_blocks = []
                idx = 1
                while idx < len(lines):
                    curr = lines[idx]
                    is_badge = bool(re.match(r'^[🔹🔸🔴🟢🔶]\s*(?:ផលវិជ្ជមាន|ហានិភ័យទីផ្សារ|ផលអវិជ្ជមាន|ហានិភ័យ)[\s៖:]*$', curr))
                    if is_badge and idx + 1 < len(lines):
                        next_line = lines[idx + 1]
                        body_blocks.append(f"{curr}\n{next_line}")
                        idx += 2
                    else:
                        body_blocks.append(curr)
                        idx += 1

                body_and_rest = '\n\n'.join(body_blocks)
                if "ហាងឆេងមាស" not in hl_text and '<b>' not in hl_text:
                    m_hl = re.match(r'^((?:[\U0001F1E6-\U0001F1FF]{2}\s*)+)(.+)$', hl_text)
                    if m_hl:
                        hl_text = f"{m_hl.group(1).strip()} <b>{m_hl.group(2).strip()}</b>"
                    else:
                        hl_text = f"<b>{hl_text}</b>"

                fixed = f"{hl_text}\n\n{body_and_rest}" if body_and_rest else hl_text

                # Sentence-aware Character limit enforcement (<= 574 for photo, <= 750 for text)
                max_allowed = 574 if has_photo else 750
                if len(fixed) > max_allowed:
                    r_paragraphs = fixed.split('\n\n')
                    while len('\n\n'.join(r_paragraphs)) > max_allowed and len(r_paragraphs) > 2:
                        mid = r_paragraphs[1]
                        if '។' in mid:
                            sentences = [s.strip() for s in mid.split('។') if s.strip()]
                            if len(sentences) > 1:
                                r_paragraphs[1] = '។ '.join(sentences[:-1]) + '។'
                            else:
                                r_paragraphs.pop(1)
                        else:
                            r_paragraphs.pop(1)
                    fixed = '\n\n'.join(r_paragraphs)
                    if len(fixed) > max_allowed:
                        last_period = fixed[:max_allowed - 1].rfind('។')
                        if last_period > 200:
                            fixed = fixed[:last_period + 1].strip()

                final_text = fixed

                # Check if text actually differs or if we already healed it
                if self._healed_posts_cache.get(pid) == final_text:
                    continue

                raw_final = html_module.unescape(re.sub(r'<[^>]+>', ' ', final_text)).strip()
                raw_final_collapsed = re.sub(r'\s+', ' ', raw_final)
                raw_curr_collapsed = re.sub(r'\s+', ' ', txt)

                if raw_final_collapsed != raw_curr_collapsed or len(txt) > max_allowed:
                    logger.info(f"[AUTONOMOUS LIVE HEAL] Correcting post #{pid} (length {len(txt)} -> {len(raw_final)})")
                    if has_photo:
                        res = self.notifier.edit_message_caption(pid, final_text, parse_mode="HTML")
                    else:
                        res = self.notifier.edit_message_text(pid, final_text, parse_mode="HTML")

                    if res and res.get("ok"):
                        self._healed_posts_cache[pid] = final_text
                        logger.info(f"[AUTONOMOUS LIVE HEAL] Successfully healed post #{pid} on Telegram channel!")
                    else:
                        self._healed_posts_cache[pid] = final_text
        except Exception as e:
            logger.debug(f"[audit_live_channel_and_heal error] {e}")


    def _is_already_in_telegram_channel(self, title: str, link: str = "", khmer_text: str = "", fresh: bool = False) -> bool:
        """Inspects the public Telegram channel feed to prevent duplicate broadcasts across distributed containers."""
        try:
            import urllib.parse
            import html as html_module
            max_age = 0.0 if fresh else 60.0
            channel_html = self._fetch_channel_html(max_cache_age=max_age)
            if not channel_html:
                return False

            # 1. Exact Link & Article Slug Verification (Bulletproof Match across whole channel feed)
            if link:
                clean_link = link.split("?")[0].rstrip("/")
                if clean_link and (clean_link in channel_html or urllib.parse.unquote(clean_link) in channel_html):
                    return True
                slug = clean_link.split("/")[-1]
                if len(slug) >= 10:
                    if slug.lower() in channel_html.lower() or slug.replace("-", " ").lower() in channel_html.lower():
                        return True

            # 2. Extract Individual Telegram Posts for precise post-by-post comparison
            posts_raw = re.findall(r'<div class="tgme_widget_message_(?:text|caption)[^"]*"[^>]*>(.*?)</div>', channel_html, re.DOTALL)
            if not posts_raw:
                posts_raw = [channel_html]

            BROAD_GEOPOLITICAL = {
                'israel', 'gaza', 'russia', 'ukraine', 'china', 'united', 'states', 'america',
                'iran', 'yemen', 'syria', 'lebanon', 'india', 'japan', 'korea', 'france',
                'germany', 'britain', 'british', 'taiwan', 'today', 'world', 'market', 'report',
                'breaking', 'global', 'first', 'could', 'would', 'after', 'about', 'state'
            }

            title_words = [w for w in re.findall(r'\b[A-Za-z0-9]{4,}\b', title) 
                           if w.lower() not in ('news', 'today', 'live', 'world', 'market', 'report', 'the', 'says', 'with', 'from', 'after', 'gold', 'price', 'rate', 'year', 'time', 'week', 'state', 'states', 'view', 'channel', 'message', 'telegram')]
            
            # Distinctive proper nouns (e.g. Palantir, Gelsinger, Boeing, DeepSeek) excluding broad geopolitical nations
            proper_nouns = [w for w in re.findall(r'\b[A-Z][a-z0-9]{4,}\b', title) if w.lower() not in BROAD_GEOPOLITICAL]

            # Khmer content words excluding standard channel boilerplate template phrases
            KHMER_BOILERPLATE = {'ព្រឹត្តិការណ៍សំខាន់', 'ព្រឹត្តិការណ៍', 'ប្រភពព័ត៌មាន', 'ផលវិជ្ជមាន', 'ផលអវិជ្ជមាន', 'ឥទ្ធិពលវិជ្ជមាន', 'ឥទ្ធិពលអវិជ្ជមាន', 'អព្យាក្រឹត', 'ផលអព្យាក្រឹត'}
            kh_content_words = [kw for kw in re.findall(r'[\u1780-\u17FF]{5,}', khmer_text) if kw not in KHMER_BOILERPLATE] if khmer_text else []

            src_match = re.search(r'ប្រភពព័ត៌មាន\s*\|\s*(?:<[^>]+>)?([^<>\n]+)', khmer_text) if khmer_text else None
            source_in_msg = src_match.group(1).strip() if src_match else ""

            norm_msg = re.sub(r'[\s\W_]+', '', khmer_text).lower() if khmer_text else ""

            # 3. Check each post individually to eliminate cross-post false-positive accumulation
            for post_html in posts_raw:
                post_text = html_module.unescape(re.sub(r'<[^>]+>', ' ', post_html)).strip()
                post_lower = post_text.lower()

                # A. Title keywords match against THIS specific post
                post_matches = sum(1 for w in title_words if w.lower() in post_lower) if title_words else 0
                if len(title_words) >= 4:
                    if post_matches >= 3 and (post_matches / len(title_words)) >= 0.45:
                        return True
                    if post_matches >= 4:
                        return True
                elif len(title_words) in (2, 3):
                    if post_matches >= 2:
                        return True

                # B. Distinctive proper noun in this specific post plus at least one other word
                for pn in proper_nouns:
                    if len(pn) >= 6 and pn.lower() in post_lower:
                        other_word_matches = sum(1 for w in title_words if w.lower() != pn.lower() and w.lower() in post_lower)
                        if other_word_matches >= 1:
                            return True

                # C. Khmer content words match in this specific post
                kh_matches = sum(1 for kw in kh_content_words if kw in post_text) if kh_content_words else 0
                if len(kh_content_words) >= 4:
                    if kh_matches >= 3 and (kh_matches / len(kh_content_words)) >= 0.50:
                        return True
                elif len(kh_content_words) in (2, 3):
                    if kh_matches >= 2 and (kh_matches / len(kh_content_words)) >= 0.60:
                        return True

                # D. Distinctive Publisher / Source match in recent posts
                if source_in_msg and len(source_in_msg) >= 4 and source_in_msg.lower() not in ('reuters', 'bloomberg', 'ap news', 'cnbc', 'bbc'):
                    if source_in_msg.lower() in post_lower and (kh_matches >= 2 or post_matches >= 2):
                        return True

                # E. Substring match for identical or near-identical formatted text
                norm_post = re.sub(r'[\s\W_]+', '', post_text).lower()
                if len(norm_msg) >= 35:
                    for offset in range(0, min(len(norm_msg) - 30, 100), 15):
                        seg = norm_msg[offset:offset+30]
                        if seg in norm_post:
                            return True

            # 4. Macro Cluster Verification in Channel Feed (Prevents cross-container duplicates for single major events)
            cluster = GoldNewsFilter.get_news_cluster(title)
            if cluster == "us_jobs" and re.search(r'29,000|29K|ការងារ|nfp|payroll', channel_html, re.I):
                return True
            if cluster == "inflation" and re.search(r'cpi|អតិផរណា|pce', channel_html, re.I):
                return True
            if cluster == "fed_rates" and re.search(r'fomc|អត្រាការប្រាក់|powell|kevin warsh', channel_html, re.I):
                return True
            if cluster == "middle_east" and re.search(r'យេមែន|យេម៉ែន|ហូទី|yemen|houthi|bab al-mandab', channel_html, re.I) and any(w in title.lower() for w in ["yemen", "houthi", "sanaa", "humanitarian"]):
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
        channel_time_since_last = self._channel_time_since_last_post()
        time_since_last = min(now - last_alert_ts, now - self._last_breaking_sent_ts, channel_time_since_last)
        # Fast-track gate: minimal 3-second safety gap to prevent Telegram flood
        if time_since_last < 3.0:
            return

        # Daily Volume Capping & Moderation Standard:
        # User Directive: ដកការទប់ស្កាត់ព័ត៌មានក្នុងមួយថ្ងៃ១៦ដង អាចឱ្យផ្សាយដោយសេរី (0 = Unlimited) ដើម្បីទាក់ទាញមនុស្សចូល Channel
        today_key = datetime.now(CAMBODIA_TZ).strftime("%Y-%m-%d")
        today_count = int(database.get_state(f"daily_breaking_count_{today_key}") or "0")
        if MAX_DAILY_BREAKING_NEWS > 0 and today_count >= MAX_DAILY_BREAKING_NEWS:
            # Only allow bypass if an extreme Tier-0 crisis occurs
            has_crisis = False
            for test_it in self.news_collector.fetch_latest_news():
                t_low = f"{test_it.get('title', '')} {test_it.get('description', '')}".lower()
                if any(k in t_low for k in ["nuclear", "outbreak of war", "declares war", "martial law", "assassination"]):
                    has_crisis = True
                    break
            if not has_crisis:
                logger.debug(f"[DAILY VOLUME CAP REACHED] {today_count}/{MAX_DAILY_BREAKING_NEWS} posts already sent today ({today_key}). Preserving channel curation.")
                return

        pending = []
        for item in self.news_collector.fetch_latest_news():
            news_id = item["id"]
            title = (item.get("title") or "").strip()
            desc = item.get("description", "")

            # Strict relevance & question/opinion rejection (Zero Sports, Zero Celebrity Gossip)
            if not title or "?" in title or not GoldNewsFilter.is_gold_relevant(title, desc):
                continue

            # Strict High-Importance Filter: Broadcast ONLY critical high-impact news per user directive (ព័ត៌មានដែលសំខាន់ខ្លាំង)
            if not GoldNewsFilter.is_high_importance(title, desc):
                logger.debug(f"[FILTER: NOT HIGH IMPORTANCE] Skipping minor/routine wire item: '{title}'")
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

            # STRICT FRESHNESS SHIELD (Zero Old News Guarantee — ព័ត៌មានថ្មីៗ):
            # Strictly reject stale items older than 45 minutes (2700s) or items with unknown/unverified age.
            MAX_NEWS_AGE = 2700.0  # Strictly 45 minutes maximum for fresh breaking news
            item_ts = self._news_ts(item)
            if item_ts == 0.0 or (now - item_ts) > MAX_NEWS_AGE:
                logger.info(f"[STALE NEWS SHIELD] Dropping old/unverified news '{title}' (Age: {(now - item_ts)/60:.1f}m if item_ts > 0 else 'Unknown').")
                self.news_collector.clear_item(news_id=news_id, link=item.get("link", ""), title=title)
                database.record_news_sent(news_id, title, item.get("source", ""), is_broadcasted=0)
                continue

            pending.append(item)

        if not pending:
            return

        # PRIORITY 5: Breaking Velocity & Multi-Wire Consensus Engine
        from analyzers.breaking_velocity import BreakingVelocityEngine
        pending = BreakingVelocityEngine.prioritize_pending(pending)

        recent_sent_titles = database.get_recent_news_titles(hours=24)
        for it in pending:
            title = it["title"]
            desc = it.get("description", "")

            # Dynamically evaluate Breaking Velocity & Multi-Wire Consensus
            velocity_info = it.get("velocity_eval") or BreakingVelocityEngine.evaluate_velocity(it)
            is_ultra = velocity_info.get("is_ultra_breaking", False)
            required_gap = velocity_info.get("required_gap", BREAKING_ALERT_MIN_GAP)
            bypass_cooldown = velocity_info.get("bypass_cooldown", False)
            wire_sources = velocity_info.get("consensus_sources", [])
            if wire_sources:
                logger.info(f"[MULTI-WIRE CONSENSUS] '{title}' verified across {len(wire_sources)} global wires: {wire_sources}")
            if is_ultra:
                logger.info(f"[BREAKING VELOCITY ULTRA] Crisis/Consensus detected for '{title}'. Required gap: {required_gap:.0f}s. Bypass cooldown: {bypass_cooldown}")

            # Dynamically recalculate gap before evaluating each item
            now = time.time()
            last_alert_ts = float(database.get_state("last_breaking_alert_ts") or "0")
            local_last = max(last_alert_ts, self._last_breaking_sent_ts)
            if local_last > 0:
                time_since_last = now - local_last
            else:
                channel_time_since_last = self._channel_time_since_last_post()
                time_since_last = channel_time_since_last

            if time_since_last < required_gap:
                logger.debug(f"[BREAKING GAP] {time_since_last:.1f}s elapsed < {required_gap}s required. Deferring to next cycle.")
                break

            if database.is_title_already_broadcasted(title):
                self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                continue

            # Live Channel Inspection: Extract latest channel post state directly across multiple posts
            ch_elapsed, ch_latest_clusters, ch_latest_entities, ch_recent_clusters, ch_recent_entities, ch_recent_story_texts = self._get_channel_live_feed_state()
            effective_elapsed = min(time_since_last, ch_elapsed)

            # Macro Multi-Cluster Deduplication & Consecutive Sector Diversity Shield
            clusters = GoldNewsFilter.get_news_clusters(title + " " + desc)
            if clusters:
                CLUSTER_COOLDOWNS = {
                    "us_jobs": 14400.0,       # 4 hours
                    "inflation": 14400.0,     # 4 hours
                    "fed_rates": 7200.0,      # 2 hours
                    "energy_oil": 3600.0,     # 1 hour
                    "tech_ai": 3600.0,        # 1 hour
                    "crypto_assets": 3600.0,  # 1 hour
                    "middle_east": 5400.0,    # 1.5 hours
                    "russia_ukraine": 5400.0, # 1.5 hours
                    "tariffs_trade": 3600.0,  # 1 hour
                }

                # 1. Consecutive Sector Diversity Shield: Never post 2 consecutive articles on the same topic within 30m
                last_cluster = database.get_state("last_broadcasted_cluster") or ""
                last_sent_ts = float(database.get_state("last_breaking_alert_ts") or "0")
                is_consecutive_sector = False
                matched_sec = ""
                if last_cluster and (now - last_sent_ts) < 1800.0 and last_cluster in clusters:
                    is_consecutive_sector = True
                    matched_sec = last_cluster
                # Live Channel Feed fallback: If channel's actual latest post matches any cluster within 30m
                if not is_consecutive_sector and ch_latest_clusters and ch_elapsed < 1800.0:
                    common_cl = [c for c in clusters if c in ch_latest_clusters]
                    if common_cl:
                        is_consecutive_sector = True
                        matched_sec = common_cl[0]

                if is_consecutive_sector and not bypass_cooldown:
                    logger.info(f"[SECTOR DIVERSITY SHIELD] Dropping '{title}' - sector '{matched_sec}' was just broadcasted {effective_elapsed:.0f}s ago. Rotating to preserve variety.")
                    self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                    database.record_news_sent(it["id"], title, it.get("source", ""), is_broadcasted=0)
                    continue
                elif is_consecutive_sector and bypass_cooldown:
                    logger.info(f"[VELOCITY BYPASS] Consecutive sector shield bypassed for high-velocity breaking crisis: '{title}'")

                # 2. Check each matched cluster against cooldown (persistent SQLite + live Telegram feed history)
                is_in_cooldown = False
                blocked_cluster = ""
                for cl in clusters:
                    last_cl_ts = float(database.get_state(f"cluster_last_ts_{cl}") or "0")
                    cd = CLUSTER_COOLDOWNS.get(cl, 3600.0)
                    channel_cl_elapsed = ch_recent_clusters.get(cl, 999999.0)
                    if (now - last_cl_ts) < cd or channel_cl_elapsed < cd or (cl in ch_latest_clusters and ch_elapsed < cd):
                        defcon1_words = ["nuclear", "outbreak of war", "declares war", "martial law", "assassination"]
                        if not bypass_cooldown and not any(dw in (title + " " + desc).lower() for dw in defcon1_words):
                            is_in_cooldown = True
                            blocked_cluster = cl
                            break

                if is_in_cooldown:
                    logger.info(f"[SECTOR COOLDOWN DEDUPLICATION] Dropping '{title}' in cluster '{blocked_cluster}'.")
                    self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                    database.record_news_sent(it["id"], title, it.get("source", ""), is_broadcasted=0)
                    continue

            # Key Leader & Entity Deduplication Shield (Prevents repeating same figure/leader/company)
            entities = GoldNewsFilter.get_news_entities(title + " " + desc)
            if entities:
                # A. Consecutive Entity Diversity: Never post 2 consecutive articles about the same key leader/entity within 1 hour (3600s)
                last_entity = database.get_state("last_broadcasted_entity") or ""
                last_sent_ts = float(database.get_state("last_breaking_alert_ts") or "0")
                is_consecutive_entity = False
                matched_ent_name = ""
                if last_entity and (now - last_sent_ts) < 3600.0 and last_entity in entities:
                    is_consecutive_entity = True
                    matched_ent_name = last_entity
                # Live Channel Feed fallback: If channel's actual latest post features the same entity within 1 hour
                if not is_consecutive_entity and ch_latest_entities and ch_elapsed < 3600.0:
                    common_ent = [e for e in entities if e in ch_latest_entities]
                    if common_ent:
                        is_consecutive_entity = True
                        matched_ent_name = common_ent[0]

                if is_consecutive_entity and not bypass_cooldown:
                    logger.info(f"[ENTITY DIVERSITY SHIELD] Dropping '{title}' - entity '{matched_ent_name}' was just featured {effective_elapsed:.0f}s ago. Rotating to preserve variety.")
                    self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                    database.record_news_sent(it["id"], title, it.get("source", ""), is_broadcasted=0)
                    continue
                elif is_consecutive_entity and bypass_cooldown:
                    logger.info(f"[VELOCITY BYPASS] Consecutive entity shield bypassed for high-velocity breaking crisis: '{title}'")

                # B. Entity Cooldown: Prevent repeating the same key person/entity within 14400s (4 hours - Strict Anti-Fatigue Shield)
                is_entity_in_cooldown = False
                blocked_entity = ""
                for ent in entities:
                    last_ent_ts = float(database.get_state(f"entity_last_ts_{ent}") or "0")
                    channel_ent_elapsed = ch_recent_entities.get(ent, 999999.0)
                    if (now - last_ent_ts) < 14400.0 or channel_ent_elapsed < 14400.0 or (ent in ch_latest_entities and ch_elapsed < 14400.0):
                        defcon1_words = ["nuclear", "outbreak of war", "declares war", "martial law", "assassination"]
                        if not bypass_cooldown and not any(dw in (title + " " + desc).lower() for dw in defcon1_words):
                            is_entity_in_cooldown = True
                            blocked_entity = ent
                            break

                if is_entity_in_cooldown:
                    logger.info(f"[ENTITY COOLDOWN DEDUPLICATION] Dropping '{title}' - entity '{blocked_entity}' was recently featured within 4 hours.")
                    self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                    database.record_news_sent(it["id"], title, it.get("source", ""), is_broadcasted=0)
                    continue

            if GoldNewsFilter.is_duplicate_or_similar(title, recent_sent_titles):
                logger.info(f"[CROSS-FEED DEDUPLICATION] Dropping '{title}' (Similar to recent broadcast).")
                self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                database.record_news_sent(it["id"], title, it.get("source", ""), is_broadcasted=0)
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

            # AI SEMANTIC EVENT DEDUPLICATION SHIELD:
            # Prevents wire agencies reporting on the SAME underlying event with different headlines!
            if SemanticEventDeduplicator and ch_recent_story_texts:
                is_sem_dup, sem_reason = SemanticEventDeduplicator.is_semantic_duplicate(title, desc, ch_recent_story_texts)
                if is_sem_dup:
                    logger.info(f"[SEMANTIC DEDUP SHIELD] Dropping '{title}' - {sem_reason}")
                    self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                    database.record_news_sent(it["id"], title, it.get("source", ""), is_broadcasted=0)
                    continue

            macro_ctx = ""
            try:
                if hasattr(self, "gold_collector") and self.gold_collector:
                    spot = self.gold_collector.get_spot_gold_price()
                    if spot and spot.get("price"):
                        macro_ctx = f"Spot Gold XAU/USD: ${float(spot['price']):,.2f}"
            except Exception:
                pass

            analysis = self.analyzer.analyze_breaking_news(title, desc, macro_context=macro_ctx)
            if not analysis:
                continue

            if isinstance(analysis, dict) and analysis.get("is_clear") is False:
                self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                database.record_news_sent(it["id"], title, it.get("source", ""), is_broadcasted=0)
                continue

            # Direct Khmer Headline Deduplication Shield
            hl_km = (analysis.get("headline_km") or "").strip() if isinstance(analysis, dict) else ""
            recent_kh_headlines = database.get_recent_khmer_headlines(hours=24)
            if hl_km and GoldNewsFilter.is_khmer_duplicate_or_similar(hl_km, recent_kh_headlines):
                logger.info(f"[KHMER HEADLINE DEDUPLICATION] Dropping '{title}' - Khmer headline '{hl_km}' repeats recent story.")
                self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                database.record_news_sent(it["id"], title, it.get("source", ""), is_broadcasted=0, headline_km=hl_km)
                continue

            impact = ""
            if isinstance(analysis, dict):
                impact = (analysis.get("impact") or "").strip()

            is_positive = ("វិជ្ជមាន" in impact or "🔹" in impact) and "អវិជ្ជមាន" not in impact and "ហានិភ័យ" not in impact
            is_negative = "អវិជ្ជមាន" in impact or "ហានិភ័យ" in impact or "🔸" in impact
            is_neutral = "អព្យាក្រឹត" in impact
            if is_neutral or not (is_positive or is_negative):
                logger.info(f"[FILTER: NEUTRAL/UNCLEAR IMPACT] Dropping '{title}' (Impact: '{impact}').")
                self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                database.record_news_sent(it["id"], title, it.get("source", ""), is_broadcasted=0)
                continue

            msg = KhmerFormatter.format_breaking_event_alert(it, analysis)

            # ZERO ENGLISH LEAKAGE GATE: Ensure both headline and body are genuinely translated into Khmer
            # 1. Headline English Leak Check (Strictly reject untranslated words like 'satire', 'video game', 'crisis', etc.)
            headline_latin_words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', hl_km)]
            APPROVED_PROPER_ACRONYMS = {
                'ai', 'fed', 'fomc', 'cpi', 'pce', 'gdp', 'nfp', 'pmi', 'sec', 'etf', 'etfs', 'ecb', 'boj',
                'opec', 'xau', 'usd', 'xauusd', 'dxy', 'btc', 'eth', 'sol', 'usdt', 'usdc', 'imf', 'nato',
                'tsmc', 'asml', 'amd', 'arm', 'byd', 'spacex', 'nasa', 'ceo', 'ipo', 'cds', 'us10y'
            }
            APPROVED_ENTITIES = {
                'trump', 'putin', 'biden', 'musk', 'powell', 'warsh', 'zelenskyy', 'netanyahu',
                'nvidia', 'apple', 'tesla', 'google', 'microsoft', 'meta', 'amazon', 'intel',
                'openai', 'deepseek', 'anthropic', 'huawei', 'tencent', 'alibaba', 'samsung'
            }
            untranslated_words = [
                w for w in headline_latin_words
                if w not in APPROVED_PROPER_ACRONYMS and w not in APPROVED_ENTITIES
            ]
            if untranslated_words:
                logger.warning(f"[REJECTED ENGLISH LEAK IN HEADLINE] Breaking news '{title}' has untranslated words in headline: {untranslated_words}. Dropping from broadcast.")
                self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                database.record_news_sent(it["id"], title, it.get("source", ""), is_broadcasted=0)
                continue

            # 2. Body English Leak Check
            narrative_body = (analysis.get("key_event") or analysis.get("what_happened") or "").strip()
            khmer_count = len(re.findall(r'[\u1780-\u17FF]', narrative_body))
            latin_count = len(re.findall(r'[a-zA-Z]', narrative_body))
            if khmer_count < 20 or (latin_count > 0 and (latin_count / (khmer_count + latin_count)) > 0.40):
                logger.warning(f"[REJECTED ENGLISH LEAK IN BODY] Breaking news '{title}' has untranslated English body (Khmer: {khmer_count}, Latin: {latin_count}). Dropping from broadcast.")
                self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                database.record_news_sent(it["id"], title, it.get("source", ""), is_broadcasted=0)
                continue

            # STRICT SUBSTANTIVE NARRATIVE GATE: Ensure formatted message has genuine, meaningful narrative content (No single-word stubs)
            msg_lines = [l.strip() for l in msg.split('\n') if l.strip()]
            body_lines = [
                l for l in msg_lines 
                if not l.startswith("🔹") 
                and not l.startswith("ផល") 
                and not l.startswith("ឥទ្ធិពល") 
                and not l.startswith("ប្រភពព័ត៌មាន")
            ]
            final_body = " ".join(body_lines).strip()
            final_body_khmer = len(re.findall(r'[\u1780-\u17FF]', final_body))
            GENERIC_STUBS = {"របាយការណ៍", "សេចក្តីរាយការណ៍", "ព័ត៌មាន", "បច្ចុប្បន្នភាព", "ការវិភាគ", "report", "breaking", "news"}
            if final_body_khmer < 35 or len(final_body.split()) < 4 or final_body.lower() in GENERIC_STUBS:
                logger.warning(f"[REJECTED MEANINGLESS STUB] Breaking news '{title}' has no substantive narrative body: '{final_body}'. Dropping from broadcast.")
                self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                database.record_news_sent(it["id"], title, it.get("source", ""), is_broadcasted=0)
                continue

            # Post-Analysis Entity Guard: Check entities in translated Khmer headline & body to catch any unflagged leaders
            post_entities = GoldNewsFilter.get_news_entities(f"{title} {desc} {hl_km} {final_body}")
            if post_entities:
                is_post_entity_blocked = False
                blocked_post_ent = ""
                for ent in post_entities:
                    last_ent_ts = float(database.get_state(f"entity_last_ts_{ent}") or "0")
                    channel_ent_elapsed = ch_recent_entities.get(ent, 999999.0)
                    if (now - last_ent_ts) < 14400.0 or channel_ent_elapsed < 14400.0:  # 4 hours strict cooldown
                        is_post_entity_blocked = True
                        blocked_post_ent = ent
                        break
                if is_post_entity_blocked:
                    logger.info(f"[POST-ANALYSIS ENTITY SHIELD] Dropping '{title}' - entity '{blocked_post_ent}' was recently featured within 4h.")
                    self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                    database.record_news_sent(it["id"], title, it.get("source", ""), is_broadcasted=0)
                    continue
                # Merge entities so all detected entities are locked into cooldown
                for pe in post_entities:
                    if pe not in entities:
                        entities.append(pe)

            # Minimal micro-jitter to prevent concurrency race
            time.sleep(0.05)

            # Re-verify channel feed right before dispatch (with fresh real-time web check)
            if self._is_already_in_telegram_channel(title, it.get("link", ""), khmer_text=msg, fresh=True):
                self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
                database.clear_news_from_data(it["id"], title, it.get("source", ""))
                self._broadcasted_titles_cache.add(title.lower())
                continue

            # Pre-flight channel cooldown check: ensure another container did not just post in the last 60 seconds
            fresh_elapsed = self._channel_time_since_last_post()
            min_post_gap = 20.0 if is_ultra else max(required_gap, 60.0)
            if fresh_elapsed < min_post_gap:
                logger.info(f"[CHANNEL COLLISION PREVENTED] Channel has a post from {fresh_elapsed:.1f}s ago (< {min_post_gap}s required). Deferring.")
                break

            # Lock in-memory and database atomically BEFORE dispatching
            database.clear_news_from_data(it["id"], title, it.get("source", ""), headline_km=hl_km)
            self._broadcasted_titles_cache.add(title.lower())
            database.set_state("last_breaking_alert_ts", str(time.time()))
            self._last_breaking_sent_ts = time.time()
            if clusters:
                for cl in clusters:
                    database.set_state(f"cluster_last_ts_{cl}", str(time.time()))
                database.set_state("last_broadcasted_cluster", clusters[0])
            if entities:
                for ent in entities:
                    database.set_state(f"entity_last_ts_{ent}", str(time.time()))
                database.set_state("last_broadcasted_entity", entities[0])
            self._cached_channel_html = "" # Invalidate channel cache

            # 🎬 PRIORITY 1: High-Importance Video Alert
            video = self._fetch_news_video(it, analysis=analysis)
            video_sent = False
            if video:
                msg_video = KhmerFormatter.format_breaking_event_alert(it, analysis, has_photo=True)
                caption_text = self._truncate_html_caption(msg_video, max_visible_chars=574)
                logger.info(f"[DISPATCHING VIDEO POST] Broadcasting high-importance video news: '{title}'...")
                res_v = self.notifier.send_video(video, caption=caption_text, reply_markup=None, is_ultra_breaking=is_ultra)
                if res_v.get("ok"):
                    video_sent = True
                else:
                    logger.warning("[DISPATCH FALLBACK] send_video failed or was rejected. Seamless fallback to photo/text mode.")

            if not video_sent:
                photo = self._fetch_news_image(it, analysis=analysis)
                if photo:
                    # GATE 1: Strict Zero Repetition & Perceptual Overlap Shield
                    if self._is_image_already_in_channel(photo):
                        logger.info(f"[IMAGE DUPLICATION SHIELD] Candidate photo for '{title}' was already used in recent broadcasts. Falling back to MODE B.")
                        photo = None
                    else:
                        # GATE 2: Supreme AI Multimodal Vision Quality Gate (Worldwide Highest Standard)
                        try:
                            from analyzers.vision_verifier import VisionQualityGate
                            v_res = VisionQualityGate.verify_image(photo, headline=title, summary=it.get("description", ""))
                            if not v_res.get("is_valid", True):
                                logger.warning(
                                    f"[SUPREME AI VISION GATE REJECTED] Image for '{title}': "
                                    f"{v_res.get('reason')} (Subject: {v_res.get('detected_subject')}). Falling back to MODE B (VIP Text Mode)!"
                                )
                                photo = None
                        except Exception as ve:
                            logger.debug(f"[VisionQualityGate error] {ve}")

                res_send = None
                if photo:
                    msg_photo = KhmerFormatter.format_breaking_event_alert(it, analysis, has_photo=True)
                    caption_text = self._truncate_html_caption(msg_photo, max_visible_chars=574)
                    res_send = self.notifier.send_photo(photo, caption=caption_text, reply_markup=None, is_ultra_breaking=is_ultra)
                elif photo is None:
                    # MODE B GUARANTEE: Per user constitutional rule, if no valid photo exists,
                    # broadcast cleanly in MODE B (Clean VIP Text Mode <= 750 characters)
                    logger.info(f"[MODE B ACTIVATED] Broadcasting '{title}' in Clean VIP Text Mode.")
                    msg_text = KhmerFormatter.format_breaking_event_alert(it, analysis, has_photo=False)
                    clean_text = self._truncate_html_caption(msg_text, max_visible_chars=750)
                    res_send = self.notifier.send_message(clean_text, reply_markup=None, is_ultra_breaking=is_ultra)

                if res_send and res_send.get("ok"):
                    new_msg_id = res_send.get("result", {}).get("message_id")
                    if new_msg_id:
                        database.set_state("last_channel_post_id", str(new_msg_id))

            # Increment daily broadcast counter
            today_count = int(database.get_state(f"daily_breaking_count_{today_key}") or "0")
            database.set_state(f"daily_breaking_count_{today_key}", str(today_count + 1))

            # 💥 USER DIRECTIVE: CLEAR FROM DATA IMMEDIATELY AFTER SENDING
            self.news_collector.clear_item(news_id=it["id"], link=it.get("link", ""), title=title)
            database.clear_news_from_data(it["id"], title, it.get("source", ""), headline_km=hl_km)
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

            # 4. Breaking News Alert (Triple Anti-Duplicate Shield)
            self.check_breaking_news()

            # 5. Autonomous Self-Healing Channel Auditor (Auto-purges duplicate messages/images)
            self.audit_live_channel_and_heal()

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
        background_interval = 30  # Responsive background check interval (30s)
        last_breaking_check = 0.0
        breaking_interval = 2.0   # Ultra-fast sub-second breaking news monitor (every 2s)
        last_channel_audit = 0.0
        channel_audit_interval = 2.0  # Ultra-fast 2-second autonomous self-healing audit per user directive
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

                # 3. Autonomous Channel Self-Healing Auditor (Purges duplicates or defective posts in <= 2 seconds!)
                if now - last_channel_audit >= channel_audit_interval:
                    last_channel_audit = now
                    try:
                        self.audit_live_channel_and_heal()
                    except Exception as err:
                        logger.debug(f"Error during channel live audit: {err}")

                # 4. Scheduled & Periodic Tasks Checker (Non-blocking)
                if now - last_background_check >= background_interval:
                    last_background_check = now
                    try:
                        self.check_database_maintenance()
                        self.check_daily_gold_price()
                        background_interval = self.check_economic_events()
                    except Exception as err:
                        logger.error(f"Error during background task check: {err}", exc_info=True)
                        background_interval = 30



                # Micro-sleep to ensure near-zero CPU usage while maintaining instant responsiveness
                time.sleep(0.5)
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

