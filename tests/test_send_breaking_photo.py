from formatters.khmer_formatter import KhmerFormatter
from telegram_notifier import TelegramNotifier
from main import XAUUSDNewsAssistantBot

notifier = TelegramNotifier()
bot = XAUUSDNewsAssistantBot()

news_item = {
    'id': 'test_trump_001',
    'title': 'Donald Trump announces unexpected 25% tariff on foreign steel and aluminum imports, triggering safe-haven demand',
    'source': 'Reuters World News',
    'link': 'https://www.reuters.com/markets/commodities/gold-rises-safe-haven-bids-trade-tensions-2026-09-22/',
    'description': 'Trump tariff announcement boosts bullion as investors seek safety in gold.'
}

analysis = {
    'what_happened': 'លោក ដូណាល់ ត្រាំ បានប្រកាសដាក់ពន្ធគយ ២៥% លើការនាំចូលដែកថែប និងអាលុយមីញ៉ូមភ្លាមៗ ដែលបង្កើនការភ័យខ្លាចនៃសង្គ្រាមពាណិជ្ជកម្មសកល។',
    'why_it_matters': 'ភាពតានតឹងពាណិជ្ជកម្ម និងភូមិសាស្ត្រនយោបាយជំរុញឱ្យវិនិយោគិនទូទាំងពិភពលោកដកដើមទុនចេញពីទ្រព្យសកម្មប្រថុយប្រថាន (Risk-Off) មករកមាស។',
    'usd_impact': 'USD មានចលនាចម្រុះ ប៉ុន្តែរងសម្ពាធអតិផរណារយៈពេលវែង។',
    'rate_yield_impact': 'អត្រាការប្រាក់ Yields ធ្លាក់ចុះដោយសារទីផ្សារបារម្ភពីការថមថយនៃកំណើនសេដ្ឋកិច្ច។',
    'xau_pressure': 'ជំរុញឱ្យតម្លៃមាស XAUUSD ហោះឡើងខ្លាំង (Bullish Spike) ឆ្ពោះទៅកាន់តំបន់ Resistance សំខាន់!'
}

msg = KhmerFormatter.format_breaking_event_alert(news_item, analysis)
photo = bot._fetch_news_image(news_item) or bot._build_calendar_png()

if photo:
    n_link = news_item['link']
    n_src = news_item['source']
    caption_short = (
        "🚨 <b>BREAKING EVENT: Trump Announces 25% Tariff</b>\n\n"
        "• 🥇 <b>សម្ពាធលើ XAUUSD:</b> 👉 🟢 <b>Bullish Spike (ហោះឡើងខ្លាំង)</b>\n"
        f"🔗 <i>ប្រភពព័ត៌មាន: <a href='{n_link}'>{n_src}</a> (ចុចអានបន្ថែម)</i>"
    )
    res_p = notifier.send_photo(photo, caption=caption_short)
    res_m = notifier.send_message(msg)
    print(f"Photo sent: {res_p.get('ok')}, Full Analysis Message sent: {res_m.get('ok')}")
else:
    res = notifier.send_message(msg)
    print(f"Text sent: {res.get('ok')}")
