import time
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from collectors.gold_price import GoldPriceCollector
from collectors.tradingview_chart import TradingViewChartBuilder
from analyzers.fallback_analyzers import AnalyzerChain, build_fallback_analyzers
from analyzers.gemini_analyzer import GeminiAnalyzer
from formatters.khmer_formatter import KhmerFormatter
from telegram_notifier import TelegramNotifier
from main import XAUUSDNewsAssistantBot

print("==================================================")
print("🚀 RUNNING FULL TELEGRAM CHANNEL TEST BROADCAST")
print("==================================================")

notifier = TelegramNotifier()
gold_collector = GoldPriceCollector()
analyzer = AnalyzerChain([GeminiAnalyzer()] + build_fallback_analyzers())
bot = XAUUSDNewsAssistantBot()

# Clean up older test messages in channel to avoid confusion
base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
for mid in range(120, 132):
    try:
        requests.post(f"{base_url}/deleteMessage", json={"chat_id": TELEGRAM_CHAT_ID, "message_id": mid}, timeout=5)
    except Exception:
        pass

# -------------------------------------------------------------------------
# 1. 07:00 AM Daily Gold Price Broadcast (Auto-Pinned with Inline Buttons)
# -------------------------------------------------------------------------
print("\n[1/6] Sending 07:00 AM Daily Gold Price Report (Auto-Pinned)...")
price_data = gold_collector.fetch_price()
summary = analyzer.summarize_daily_price(price_data)
msg_price = KhmerFormatter.format_daily_gold_price(price_data, summary=summary)
buttons = {
    "inline_keyboard": [
        [
            {"text": "📊 មើល Chart ផ្ទាល់ (TradingView)", "url": "https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD"},
            {"text": "📅 ប្រតិទិនសេដ្ឋកិច្ច", "url": "https://www.forexfactory.com/calendar"}
        ]
    ]
}
res_1 = notifier.send_message(msg_price, auto_pin=False, reply_markup=buttons)
print(f"-> Daily Gold Price sent & pinned: {res_1.get('ok')}, ID: {res_1.get('result', {}).get('message_id')}")
time.sleep(3)

# -------------------------------------------------------------------------
# 2. 14:00 London Session Open Alert
# -------------------------------------------------------------------------
print("\n[2/6] Sending 14:00 London Session Open Alert...")
msg_london = KhmerFormatter.format_session_open_alert(
    "London Session", "14:00",
    "ធនាគារអឺរ៉ុប និងចក្រភពអង់គ្លេសចាប់ផ្តើមជួញដូរ។ សាច់ប្រាក់ងាយស្រួល (Liquidity) ចាក់ចូលទីផ្សារមាសយ៉ាងច្រើន!"
)
res_2 = notifier.send_message(msg_london)
print(f"-> London Session sent: {res_2.get('ok')}, ID: {res_2.get('result', {}).get('message_id')}")
time.sleep(3)

# -------------------------------------------------------------------------
# 3. 19:00 New York Session Open Alert
# -------------------------------------------------------------------------
print("\n[3/6] Sending 19:00 New York Session Open Alert...")
msg_ny = KhmerFormatter.format_session_open_alert(
    "New York Session", "19:00",
    "ផ្សារ Wall Street & COMEX អាមេរិកបើកដំណើរការ។ នេះជា Session ដែលមានទំហំជួញដូរមាសធំបំផុតលើលោក!"
)
res_3 = notifier.send_message(msg_ny)
print(f"-> New York Session sent: {res_3.get('ok')}, ID: {res_3.get('result', {}).get('message_id')}")
time.sleep(3)

# -------------------------------------------------------------------------
# 4. 15-Minute / 5-Minute Economic Calendar Countdown Alert
# -------------------------------------------------------------------------
print("\n[4/6] Sending Upcoming High-Impact Economic Countdown Alert...")
ev_upcoming = {
    "title": "Core CPI (MoM) — សន្ទស្សន៍ថ្លៃទំនិញប្រើប្រាស់ស្នូល",
    "currency": "USD",
    "impact": "HIGH",
    "release_time_str": "19:30",
    "forecast": "0.3%",
    "previous": "0.2%"
}
msg_upcoming = KhmerFormatter.format_upcoming_alert(ev_upcoming, minutes_left=15)
res_4 = notifier.send_message(msg_upcoming)
print(f"-> Upcoming Countdown Alert sent: {res_4.get('ok')}, ID: {res_4.get('result', {}).get('message_id')}")
time.sleep(3)

# -------------------------------------------------------------------------
# 5. Immediate Actual Data Release (Flash Alert with TradingView Chart)
# -------------------------------------------------------------------------
print("\n[5/6] Sending Actual Data Release Flash Alert (Chart + Khmer Analysis as ONE message)...")
ev_actual = {
    "title": "US Non-Farm Payrolls (NFP) — ចំនួនការងារមិនមែនកសិកម្ម",
    "currency": "USD",
    "impact": "HIGH",
    "release_time_str": "19:30",
    "release_date_str": "23/09/2026",
    "forecast": "150K",
    "previous": "142K",
    "actual": "215K"
}
analysis_actual = analyzer.analyze_actual_vs_forecast(
    ev_actual["title"], "215K", ev_actual["forecast"], ev_actual["previous"]
)
msg_actual = KhmerFormatter.format_actual_release_alert(ev_actual, analysis_actual)

chart_builder = TradingViewChartBuilder()
chart_png = chart_builder.build_chart_image(
    event_title="US NFP (Actual: 215K vs Forecast: 150K)",
    bias=analysis_actual.get("bias", "Bearish"),
    target_desc="USD កើនឡើងខ្លាំង សម្ពាធធ្លាក់ចុះលើមាស"
)

if chart_png:
    caption_text = msg_actual
    if len(caption_text) > 1024:
        caption_text = caption_text[:1000] + "..."
    res_5 = notifier.send_photo(chart_png, caption=caption_text)
else:
    res_5 = notifier.send_message(msg_actual)
print(f"-> Actual Flash Alert (with Chart) sent: {res_5.get('ok')}, ID: {res_5.get('result', {}).get('message_id')}")
time.sleep(3)

# -------------------------------------------------------------------------
# 6. High-Impact Breaking News Alert (Photo + Analysis as ONE message)
# -------------------------------------------------------------------------
print("\n[6/6] Sending Breaking News Alert (Real Photo + Clickable Link as ONE message)...")
news_item = {
    "id": "test_trump_final_01",
    "title": "Donald Trump announces unexpected 25% tariff on foreign steel and aluminum imports, triggering safe-haven demand",
    "source": "Reuters World News",
    "link": "https://www.reuters.com/markets/commodities/gold-rises-safe-haven-bids-trade-tensions-2026-09-22/",
    "description": "Trump tariff announcement boosts bullion as investors seek safety in gold."
}
analysis_breaking = {
    "what_happened": "លោក ដូណាល់ ត្រាំ បានប្រកាសដាក់ពន្ធគយ ២៥% លើការនាំចូលដែកថែប និងអាលុយមីញ៉ូមភ្លាមៗ ដែលបង្កើនការភ័យខ្លាចនៃសង្គ្រាមពាណិជ្ជកម្មសកល។",
    "why_it_matters": "ភាពតានតឹងពាណិជ្ជកម្ម និងភូមិសាស្ត្រនយោបាយជំរុញឱ្យវិនិយោគិនទូទាំងពិភពលោកដកដើមទុនចេញពីទ្រព្យសកម្មប្រថុយប្រថាន (Risk-Off) មករកមាស។",
    "usd_impact": "USD មានចលនាចម្រុះ ប៉ុន្តែរងសម្ពាធអតិផរណារយៈពេលវែង។",
    "rate_yield_impact": "អត្រាការប្រាក់ Yields ធ្លាក់ចុះដោយសារទីផ្សារបារម្ភពីការថមថយនៃកំណើនសេដ្ឋកិច្ច។",
    "xau_pressure": "ជំរុញឱ្យតម្លៃមាស XAUUSD ហោះឡើងខ្លាំង (Bullish Spike) ឆ្ពោះទៅកាន់តំបន់ Resistance សំខាន់!"
}
msg_breaking = KhmerFormatter.format_breaking_event_alert(news_item, analysis_breaking)
photo_breaking = bot._fetch_news_image(news_item) or bot._build_calendar_png()

if photo_breaking:
    caption_text = msg_breaking
    if len(caption_text) > 1024:
        caption_text = caption_text[:1000] + "..."
    res_6 = notifier.send_photo(photo_breaking, caption=caption_text)
else:
    res_6 = notifier.send_message(msg_breaking)
print(f"-> Breaking News (Photo + Text) sent: {res_6.get('ok')}, ID: {res_6.get('result', {}).get('message_id')}")

# -------------------------------------------------------------------------
# 7. 22:00 Daily Market Wrap-Up Alert
# -------------------------------------------------------------------------
print("\n[7/7] Sending 22:00 Daily Market Wrap-Up...")
msg_wrap = KhmerFormatter.format_night_wrap_up(price_data, summary=summary)
res_7 = notifier.send_message(msg_wrap)
print(f"-> Night Wrap-Up sent: {res_7.get('ok')}, ID: {res_7.get('result', {}).get('message_id')}")

print("\n==================================================")
print("✅ ALL 7 MESSAGE TYPES SUCCESSFULLY SENT TO TELEGRAM!")
print("==================================================")
