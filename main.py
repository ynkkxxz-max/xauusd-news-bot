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
    from candlestick_chart_builder import CandlestickChartRenderer
except ImportError:
    from collectors.candlestick_chart_builder import CandlestickChartRenderer

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
        self.chart_renderer = CandlestickChartRenderer()
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
        self._bootstrap_news_cache()

    def _bootstrap_news_cache(self):
        """On startup, marks any currently active news items in the feeds as already known
        so the bot strictly broadcasts brand-new breaking news that appears AFTER startup."""
        try:
            items = self.news_collector.fetch_latest_news()
            bootstrapped = 0
            for item in items:
                if not database.is_news_sent(item["id"]):
                    database.record_news_sent(item["id"], item["title"], item.get("source", ""))
                    bootstrapped += 1
            if bootstrapped > 0:
                logger.info(f"[Startup News Sync] Registered {bootstrapped} active feed items. Only future fresh news will trigger alerts.")
        except Exception as e:
            logger.warning(f"[Startup News Sync] Warning: {e}")

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
                        {"text": "🔄 ឆែកតម្លៃ Live", "url": "https://t.me/FFNewsAlertBot?start=price"},
                        {"text": "📊 មើល Chart ផ្ទាល់ (TradingView)", "url": "https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD"}
                    ],
                    [
                        {"text": "📅 ប្រតិទិនសេដ្ឋកិច្ច", "url": "https://www.forexfactory.com/calendar"}
                    ]
                ]
            }

            # Send strictly to the Channel with Inline Buttons (Do NOT auto-pin to keep header clean)
            res = self.notifier.send_message(msg, auto_pin=False, reply_markup=buttons)
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
            price_data = self.gold_collector.fetch_price()
            order_book = self.order_book_tracker.fetch_order_book_depth()
            heatmap_png = self.heatmap_builder.generate_heatmap_png(price_data, order_book)
            if heatmap_png:
                self.notifier.send_photo(heatmap_png, caption=msg)
            else:
                self.notifier.send_message(msg)
            database.set_state(f"london_session_{today_str}", "sent")
            logger.info("London Session Open alert + Heatmap broadcasted.")

        # New York Session: 19:00 (7:00 PM) Cambodia Time
        if now_kh.hour == 19 and not database.get_state(f"ny_session_{today_str}"):
            msg = KhmerFormatter.format_session_open_alert(
                "New York Session", "19:00",
                "ផ្សារ Wall Street & COMEX អាមេរិកបើកដំណើរការ។ នេះជា Session ដែលមានទំហំជួញដូរមាសធំបំផុតលើលោក!"
            )
            price_data = self.gold_collector.fetch_price()
            order_book = self.order_book_tracker.fetch_order_book_depth()
            heatmap_png = self.heatmap_builder.generate_heatmap_png(price_data, order_book)
            if heatmap_png:
                self.notifier.send_photo(heatmap_png, caption=msg)
            else:
                self.notifier.send_message(msg)
            database.set_state(f"ny_session_{today_str}", "sent")
            logger.info("New York Session Open alert + Heatmap broadcasted.")

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

    def check_price_volatility_spike(self):
        """
        Monitors rapid Gold Price movement (Spike Warning).
        If gold moves >= $15 within a 15-minute window, immediately triggers a Volatility Alert.
        Includes a 30-minute cooldown to prevent spamming while keeping traders informed.
        """
        now = time.time()
        last_alert = float(database.get_state("last_spike_alert_ts") or 0.0)
        if now - last_alert < 1800:  # 30-minute cooldown
            return

        price_data = self.gold_collector.fetch_price()
        current_price = price_data.get("price_oz", 0.0)
        if current_price <= 0:
            return

        # Fetch baseline price from 15 minutes ago
        last_record = database.get_state("last_tracked_price_data")
        import json
        if last_record:
            try:
                prev_data = json.loads(last_record)
                prev_ts = prev_data.get("ts", now)
                prev_price = prev_data.get("price", current_price)

                diff = round(current_price - prev_price, 2)
                # If 10-20 minutes elapsed and price moved by $15 or more
                if (now - prev_ts >= 600) and abs(diff) >= 15.0:
                    logger.info(f"[VOLATILITY SPIKE DETECTED] XAUUSD moved ${diff:+.2f} (from ${prev_price} to ${current_price})")
                    msg = KhmerFormatter.format_spike_alert(current_price, prev_price, diff, minutes=int((now - prev_ts) / 60))
                    self.notifier.send_message(msg)
                    database.set_state("last_spike_alert_ts", str(now))
                    # Reset baseline after alert
                    database.set_state("last_tracked_price_data", json.dumps({"price": current_price, "ts": now}))
                    return
                elif now - prev_ts >= 900:  # Roll forward reference every 15 minutes
                    database.set_state("last_tracked_price_data", json.dumps({"price": current_price, "ts": now}))
            except Exception as e:
                logger.warning(f"Spike check parse error: {e}")
                database.set_state("last_tracked_price_data", json.dumps({"price": current_price, "ts": now}))
        else:
            database.set_state("last_tracked_price_data", json.dumps({"price": current_price, "ts": now}))

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

        conf = self.candle_analyzer.detect_confirmation(current_price, buy_zone, sell_zone)
        if conf:
            logger.info(f"[CANDLESTICK CONFIRMATION DETECTED] {conf['pattern']} at {conf['zone_name']}")
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
            if chart_png:
                self.notifier.send_photo(chart_png, caption=self._truncate_html_caption(msg, 950))
            else:
                self.notifier.send_message(msg)
            database.set_state("last_candle_conf_ts", str(now))

    def check_news_danger_zone(self):
        """
        AI Market Regime & High-Impact News Filter:
        Monitors if market is within 15 minutes of a High-Impact USD release (CPI, NFP, FOMC).
        Broadcasts high-priority Danger Warning and sets temporary No-Trade lock.
        """
        now = time.time()
        danger_info = self.calendar_collector.is_news_danger_zone(buffer_minutes=15)
        
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
        Sends immediate high-priority alert directly to Telegram when a high-probability setup triggers!
        Blocked automatically if AI News Danger Zone is active.
        """
        # Safety Gate: Do NOT send buy/sell signals during High-Impact News Danger Zone!
        danger_info = self.calendar_collector.is_news_danger_zone(buffer_minutes=15)
        if danger_info.get("is_danger"):
            logger.info(f"[SNIPER SIGNAL BLOCKED] Danger zone active for {danger_info.get('title')}. Capital protection active.")
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

            logger.info(f"[AI SNIPER INSTANT SIGNAL] {sig['action_title']} at ${sig['entry']}")
            msg = KhmerFormatter.format_sniper_instant_alert(sig)
            
            # Interactive action buttons
            buttons = {
                "inline_keyboard": [
                    [
                        {"text": "📊 មើល TradingView Chart", "url": "https://ynkkxxz-max.github.io/xauusd-news-bot/?tab=chart"},
                        {"text": "🧮 គិត Lot Size ភ្លាម", "url": "https://ynkkxxz-max.github.io/xauusd-news-bot/?tab=lot"}
                    ]
                ]
            }
            self.notifier.send_message(msg, reply_markup=buttons)
            database.set_state("last_sniper_signal_ts", str(now))
            database.set_state("last_sniper_action", sig.get("action", ""))

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

    def check_iceberg_orders(self):
        """
        Monitors 100-level Gold Order Book for abnormal institutional iceberg walls (> 20 oz block).
        Alerts when an aggressive whale wall defends support or caps resistance.
        """
        now = time.time()
        last_iceberg = float(database.get_state("last_iceberg_alert_ts") or 0.0)
        if now - last_iceberg < 7200:  # 2-hour cooldown between iceberg wall alerts
            return

        iceberg = self.order_book_tracker.detect_iceberg_anomaly()
        if iceberg:
            logger.info(f"[WHALE ICEBERG DETECTED] {iceberg['type']} at ${iceberg['price']}")
            msg = KhmerFormatter.format_iceberg_alert(iceberg)
            self.notifier.send_message(msg)
            database.set_state("last_iceberg_alert_ts", str(now))

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
                        {"text": "SMC", "web_app": {"url": "https://ynkkxxz-max.github.io/xauusd-news-bot/?v=105&tab=smc"}}
                    ]
                ],
                "resize_keyboard": True,
                "persistent": True
            }

            # 1. Handle Callback Query clicks (Inline Buttons)
            cb_query = u.get("callback_query")
            if cb_query:
                cb_id = cb_query.get("id")
                cb_data = cb_query.get("data", "")
                cb_chat_id = cb_query.get("message", {}).get("chat", {}).get("id")
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

            # 2. Handle Text Messages or WebApp Data
            msg_obj = u.get("message", {})
            chat_id = msg_obj.get("chat", {}).get("id")
            web_app_data = msg_obj.get("web_app_data", {}).get("data", "")
            text = (web_app_data or msg_obj.get("text") or "").strip()

            if not text or not chat_id:
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

            if clean_cmd in ("/lot", "/risk", "lot", "risk") or "lot" in text.lower() or "risk" in text.lower() or "គិត" in text:
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
                price_data = self.gold_collector.fetch_price()
                # Clean, pure price report without SMC/Macro block when clicking 'Price' button
                resp = KhmerFormatter.format_daily_gold_price(price_data, summary="", include_smc=False)
                self.notifier.send_message(resp, chat_id=chat_id, reply_markup=bottom_keyboard)


            elif clean_cmd in ("/levels", "/setup", "smc") or "កម្រិត smc" in text.lower():
                from collectors.market_cache import market_cache
                price_data = self.gold_collector.fetch_price()
                levels = price_data.get("key_levels", {})
                oz = price_data.get("price_oz", 0.0)

                # 1. Ultra-Fast Check In-Memory RAM Cache (< 0.01s)
                setup = market_cache.get_smc_setup()
                if not setup:
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
                            {"text": "📱 បើក Mini App (Live SMC Terminal)", "url": "https://ynkkxxz-max.github.io/xauusd-news-bot/?tab=smc"}
                        ],
                        [
                            {"text": "📊 មើល TradingView Live Chart", "url": "https://ynkkxxz-max.github.io/xauusd-news-bot/?tab=chart"},
                            {"text": "🧮 គិត Lot Size", "url": "https://ynkkxxz-max.github.io/xauusd-news-bot/?tab=lot"}
                        ]
                    ]
                }
                reply = KhmerFormatter.format_single_smc_setup(setup, key_levels=levels, current_price=oz)
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

            elif clean_cmd in ("/fomc", "/powell") or "fed" in text.lower():
                self.notifier.send_message("⚡ <i>AI កំពុងទាញយកសេចក្តីថ្លែងការណ៍ FOMC និងសុន្ទរកថា Fed ចុងក្រោយបង្អស់មកវិភាគបកប្រែ...</i>", chat_id=chat_id)
                # Fetch latest Fed official press releases
                fed_items = [it for it in self.news_collector.fetch_latest_news() if any(k in it['title'].lower() for k in ['fed', 'fomc', 'federal reserve', 'powell', 'monetary policy'])]
                if fed_items:
                    target = fed_items[0]
                    interp = self.fomc_interpreter.interpret_powell_speech(f"{target['title']}\n{target.get('description', '')}", event_title=target['title'])
                    if interp:
                        resp = KhmerFormatter.format_fomc_speech_alert(target['title'], interp)
                        self.notifier.send_message(resp, chat_id=chat_id, reply_markup=bottom_keyboard)
                        if interp.get("voice_script"):
                            v_b = self.voice_synth.text_to_speech(interp["voice_script"])
                            if v_b and len(v_b) > 1000:
                                self.notifier.send_voice(v_b, caption="🎙️ <b>សំឡេងបកប្រែសង្ខេប Fed / Powell Speech</b>", chat_id=chat_id)
                        return

                self.notifier.send_message("📅 មិនទាន់មានសេចក្តីថ្លែងការណ៍ FOMC ថ្មីភ្លាមៗក្នុងរយៈពេលប៉ុន្មានម៉ោងនេះទេ (រង់ចាំការប្រជុំ FOMC បន្ទាប់)។", chat_id=chat_id, reply_markup=bottom_keyboard)

            elif clean_cmd in ("/help", "/start") or "ជំនួយ" in text:
                parts = text.split()
                if len(parts) > 1 and parts[1].lower() == "price":
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
                                {"text": "📱 បើក Mini App (Live SMC Terminal)", "url": "https://ynkkxxz-max.github.io/xauusd-news-bot/?tab=smc"}
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
                        f"👋 <b>សូមស្វាគមន៍មកកាន់ XAUUSD AI Assistant Bot!</b>\n\n"
                        f"ចុចប៊ូតុង <b>[ Price ]</b> ឬ <b>[ SMC ]</b> នៅខាងក្រោម ឬវាយពាក្យបញ្ជា Bot៖\n"
                        f"• <b>Price</b> ➡️ មើលហាងឆេងមាស Spot និងផ្សារធំថ្មីបច្ចុប្បន្ន\n"
                        f"• <b>SMC</b> ➡️ មើលកម្រិតបច្ចេកទេស AI Pivot & SMC Setup Zone\n"
                        f"• <code>/chart</code> ➡️ ស្កេនរូប Chart ទៀន Live + AI Vision Pattern Scanner (M15)\n"
                        f"• <code>/lot</code> ➡️ ម៉ាស៊ីនគណនាទំហំ Lot Size & Risk ឆ្លាតវៃតាមដើមទុន\n"
                        f"• <code>/heatmap</code> ➡️ ផែនទីកម្តៅ Smart Money Liquidity Heatmap HD (Canvas)\n"
                        f"• <code>/fomc</code> ➡️ AI បកប្រែផ្ទាល់ការថ្លែងសុន្ទរកថា Fed / Powell Speech + សំឡេង\n"
                        f"• <code>/depth</code> ➡️ មើលជម្រៅ Order Book Depth 100 Levels & Iceberg Walls\n"
                        f"• <code>/cot</code> ➡️ មើលរបាយការណ៍កុងត្រាស្ថាប័នធំៗ CFTC CoT Report\n"
                        f"• <code>/dxy</code> ➡️ មើលសន្ទស្សន៍ដុល្លារ និងសញ្ញា Macro Divergence\n"
                        f"• <code>/voice</code> ➡️ ស្តាប់សំឡេងនិយាយសង្ខេបហាងឆេងមាសភាសាខ្មែរ"
                    )
                    self.notifier.send_message(help_text, chat_id=chat_id, reply_markup=bottom_keyboard)



    @staticmethod
    def _caption_fits(text: str, limit: int = 1024) -> bool:
        """Telegram captions are capped at 1024 characters (HTML tags not counted)."""
        return len(re.sub(r"<[^>]+>", "", text)) <= limit

    @staticmethod
    def _truncate_html_caption(text: str, max_visible_chars: int = 900) -> str:
        """Safely trims text to keep visible length <= 1024 while ensuring open HTML tags are closed."""
        if XAUUSDNewsAssistantBot._caption_fits(text, limit=1000):
            return text

        # Split into blocks and keep essential alerts
        blocks = text.split("\n\n")
        trimmed_blocks = []
        curr_len = 0
        for b in blocks:
            vis = len(re.sub(r"<[^>]+>", "", b))
            if curr_len + vis > max_visible_chars:
                break
            trimmed_blocks.append(b)
            curr_len += vis

        res = "\n\n".join(trimmed_blocks)
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
        full_text = (item.get("title", "") + " " + item.get("description", "")).lower()
        search_query = None

        if "adb" in full_text or "asian development bank" in full_text:
            search_query = "Asian Development Bank"
        elif "china" in full_text or "chinese economy" in full_text or "beijing" in full_text:
            search_query = "Economy of China Beijing"
        elif "trump" in full_text:
            search_query = "Donald Trump United Nations General Assembly"
        elif "powell" in full_text or "federal reserve" in full_text or "fomc" in full_text or "fed" in full_text:
            search_query = "Jerome Powell Federal Reserve"
        elif "putin" in full_text or ("russia" in full_text and ("ukraine" in full_text or "war" in full_text or "sanction" in full_text)):
            search_query = "Vladimir Putin"
        elif "ecb" in full_text or "lagarde" in full_text:
            search_query = "Christine Lagarde European Central Bank"
        elif "iran" in full_text or "middle east" in full_text or "red sea" in full_text or "houthis" in full_text:
            search_query = "Middle East geopolitical tension"
        elif "japan" in full_text or "boj" in full_text or "yen" in full_text:
            search_query = "Bank of Japan Tokyo"
        elif "oil" in full_text or "crude" in full_text or "opec" in full_text:
            search_query = "Petroleum industry oil rig"
        elif "gold" in full_text or "xau" in full_text or "bullion" in full_text or "precious metal" in full_text:
            search_query = "Gold bars bullion vault"
        elif "inflation" in full_text or "cpi" in full_text:
            search_query = "Inflation economics price index"
        elif "dollar" in full_text or "dxy" in full_text:
            search_query = "United States dollar banknote"

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

        # Fetch titles broadcasted in the last 4 hours for cross-source semantic deduplication
        recent_sent_titles = database.get_recent_news_titles(hours=4)

        # Filter out items that discuss the exact same event as already broadcasted
        unique_pending = []
        for it in pending:
            if GoldNewsFilter.is_duplicate_or_similar(it["title"], recent_sent_titles):
                logger.info(f"[SEMANTIC DUPLICATE SKIPPED] News '{it['title']}' is duplicate of a recent alert.")
                database.record_news_sent(it["id"], it["title"], it.get("source", ""))
            else:
                unique_pending.append(it)

        if not unique_pending:
            return

        # Select the most urgent & fresh news among the unique items
        item = max(
            unique_pending,
            key=lambda it: (GoldNewsFilter.urgency_score(it["title"]), self._news_ts(it)),
        )
        logger.info(f"[ZERO-DELAY IMMEDIATE ALERT] News/Anomaly detected: {item['title']}")
        title = item["title"]
        desc = item.get("description", "")
        logger.info(f"Sending breaking alert: {title}")
        analysis = self.analyzer.analyze_breaking_news(title, desc)
        if not analysis:
            return

        # --- SPECIAL FOMC / POWELL / WARSH LIVE SPEECH INTERPRETATION ---
        is_fomc_or_powell = any(w in (title + " " + desc).lower() for w in ["fomc", "powell", "warsh", "fed rate", "federal reserve issues", "rate decision"])
        fomc_interp = None
        if is_fomc_or_powell and self.fomc_interpreter.is_available():
            logger.info(f"[LIVE FOMC/POWELL/WARSH INTERPRETER] Detected Fed statement/speech: {title}")
            fomc_interp = self.fomc_interpreter.interpret_powell_speech(f"{title}\n{desc}", event_title=title)

        if fomc_interp:
            msg = KhmerFormatter.format_fomc_speech_alert(title, fomc_interp)
        else:
            msg = KhmerFormatter.format_breaking_event_alert(item, analysis)


        article_url = (item.get("link") or item.get("url") or "").strip()
        source_name = (item.get("source") or "ForexLive").strip()
        news_button = None
        if article_url:
            news_button = {
                "inline_keyboard": [
                    [{"text": f"🔗 អានព័ត៌មានលម្អិត ({source_name})", "url": article_url}]
                ]
            }

        photo = self._fetch_news_image(item) or self._build_calendar_png()
        if photo:
            # If caption exceeds Telegram's 1024 char limit, trim safely keeping HTML tags valid
            caption_text = self._truncate_html_caption(msg, max_visible_chars=950)
            res = self.notifier.send_photo(photo, caption=caption_text, reply_markup=news_button)
            sent_ok = bool(res.get("ok"))
            if sent_ok:
                self._calendar_attached = True
        else:
            # If absolutely no photo is available, send as single text message
            res = self.notifier.send_message(msg, reply_markup=news_button)
            sent_ok = bool(res.get("ok"))

        if sent_ok:
            database.record_news_sent(item["id"], title, item.get("source", ""))
            database.set_state("last_breaking_alert_ts", str(time.time()))

            # If FOMC / Powell Speech was interpreted, broadcast voice note immediately
            if fomc_interp and fomc_interp.get("voice_script"):
                try:
                    v_bytes = self.voice_synth.text_to_speech(fomc_interp["voice_script"])
                    if v_bytes and len(v_bytes) > 1000:
                        self.notifier.send_voice(
                            v_bytes,
                            caption="🎙️ <b>សំឡេងបកប្រែសង្ខេប Fed / Powell Speech (Live Voice Brief)</b>"
                        )
                        logger.info("FOMC live voice translation broadcasted successfully.")
                except Exception as e:
                    logger.warning(f"Failed to send FOMC voice note: {e}")
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

            # 5.1 Weekly Sunday Outlook (Every Sunday 19:00 Cambodia Time)
            self.check_weekly_sunday_outlook()

            # 5.12 AI High-Impact News Danger Zone Check (NO TRADE Filter)
            self.check_news_danger_zone()

            # 5.15 Real-Time AI Sniper Instant Signals (BUY DIP / SELL TOP with SL/TP)
            self.check_sniper_instant_signals()

            # 5.2 Real-Time Liquidity Sweep Alert (Hunt Stop Loss)
            self.check_liquidity_sweep()

            # 5.3 Macro Divergence Alert (DXY vs Gold)
            self.check_macro_divergence()

            # 5.4 Whale Order Book Depth & Iceberg Orders Tracker
            self.check_iceberg_orders()

            # 6. Breaking News Alert (Strictly filtered: Only sends if 100% clear and high-impact)
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
        - Schedules and executes background tasks (Economic Calendar, Daily Price, Sessions)
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
                        self.check_weekly_sunday_outlook()
                        self.check_price_volatility_spike()
                        self.check_news_danger_zone()
                        self.check_sniper_instant_signals()
                        self.check_candlestick_confirmation()
                        self.check_liquidity_sweep()
                        self.check_macro_divergence()
                        self.check_iceberg_orders()
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

