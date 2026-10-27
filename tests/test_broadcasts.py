import sys
import os
from main import XAUUSDNewsAssistantBot, KhmerFormatter

bot = XAUUSDNewsAssistantBot()

print('=== 1. Testing Heatmap Broadcast ===')
price_data = bot.gold_collector.fetch_price()
order_book = bot.order_book_tracker.fetch_order_book_depth()
heatmap_png = bot.heatmap_builder.generate_heatmap_png(price_data, order_book)
spot = price_data.get('price_oz', 0.0)
caption = (
    f"🧠 <b>SMART MONEY ORDER FLOW HEATMAP (XAU/USD)</b>\n\n"
    f"• 🥇 <b>Current Spot:</b> <code>${spot:,.2f}</code>\n"
    f"• 🔴 <b>BSL (Buy Side Liquidity):</b> តំបន់ Stop Loss Clusters (ខាងលើ)\n"
    f"• 🟢 <b>SSL (Sell Side Liquidity):</b> តំបន់ Stop Loss Clusters (ខាងក្រោម)\n"
    f"• 📊 <b>Depth Imbalance:</b> Bids 53.2% vs Asks 46.8%\n"
    f"• ⚖️ <b>ស្ថានភាព:</b> Bullish Liquidity Absorption"
)
res1 = bot.notifier.send_photo(heatmap_png, caption=caption)
print("Heatmap Result:", res1.get("ok"))

print('=== 2. Testing Breaking News with ADB Image & Link ===')
item = {
    'id': 'test_adb_news_002',
    'title': 'ADB maintains Developing Asia growth forecast at 5.0% for 2026',
    'description': 'The Asian Development Bank kept its economic growth outlook for developing Asia at 5.0% in 2026 as regional exports remain resilient amid global interest rate cuts.',
    'source': 'Reuters',
    'url': 'https://www.reuters.com/markets/asia/adb-forecast-2026',
    'link': 'https://www.reuters.com/markets/asia/adb-forecast-2026',
    'impact': 'MEDIUM'
}
analysis = bot.analyzer.analyze_breaking_news(item['title'], item['description'])
msg = KhmerFormatter.format_breaking_event_alert(item, analysis)
photo = bot._fetch_news_image(item)
news_button = {
    "inline_keyboard": [
        [{"text": f"🔗 អានព័ត៌មានលម្អិត ({item.get('source')})", "url": item["url"]}]
    ]
}
caption_text = bot._truncate_html_caption(msg, max_visible_chars=950)
if photo:
    res2 = bot.notifier.send_photo(photo, caption=caption_text, reply_markup=news_button)
else:
    res2 = bot.notifier.send_message(msg, reply_markup=news_button)
print("Breaking News Result:", res2.get("ok"))

print('=== 3. Testing FOMC Powell Speech Interpretation & Voice Note ===')
title = 'Fed Chair Powell Signals Prudent Pace on Interest Rate Reductions'
desc = 'Federal Reserve Chair Jerome Powell stated that the US economy continues to show resilient growth and the Fed is prepared to recalibrate its policy path depending on incoming inflation data.'
fomc_interp = bot.fomc_interpreter.interpret_powell_speech(f"{title}\n{desc}", event_title=title)
fomc_msg = KhmerFormatter.format_fomc_speech_alert(title, fomc_interp)
res3 = bot.notifier.send_message(fomc_msg)
print("FOMC Alert Result:", res3.get("ok"))

if fomc_interp and fomc_interp.get("voice_script"):
    v_bytes = bot.voice_synth.text_to_speech(fomc_interp["voice_script"])
    if v_bytes and len(v_bytes) > 1000:
        res_voice = bot.notifier.send_voice(v_bytes, caption="🎙️ <b>សំឡេងបកប្រែសង្ខេប Fed / Powell Speech (Live Voice Brief)</b>")
        print("Voice Note Result:", res_voice.get("ok"))

print('=== ALL BROADCAST TESTS COMPLETED ===')
