from datetime import datetime

class KhmerFormatter:
    @staticmethod
    def format_daily_gold_price(price_data: dict, summary: str = "") -> str:
        """
        Formats daily gold price report in Khmer with Cambodian units:
        - 1 Troy Ounce
        - 1 តម្លឹង
        - 1 ជី
        - 1 ហ៊ុន
        """
        oz = price_data.get("price_oz", 0.0)
        damlung = price_data.get("price_damlung", 0.0)
        chi = price_data.get("price_chi", 0.0)
        hun = price_data.get("price_hun", 0.0)
        chg = price_data.get("change", 0.0)
        pct = price_data.get("change_pct", 0.0)
        date_str = price_data.get("date_str", "")
        time_str = price_data.get("updated_time_str", "07:00")
        
        sign = "+" if chg >= 0 else ""
        icon = "📈" if chg >= 0 else "📉"

        summary_block = f"🧠 <b>ការវិភាគសង្ខេប:</b>\n{summary}\n\n" if summary else ""

        msg = (
            f"🥇 <b>DAILY GOLD PRICE</b>\n\n"
            f"📅 <b>កាលបរិច្ឆេទ:</b> {date_str}\n\n"
            f"🥇 <b>XAUUSD / តម្លៃមាស</b>\n"
            f"• <b>1 តម្លឹង:</b> ${damlung:,.2f}\n"
            f"• <b>1 ជី:</b> ${chi:,.2f}\n"
            f"• <b>1 ហ៊ុន:</b> ${hun:,.2f}\n"
            f"• <b>1 Troy Ounce:</b> ${oz:,.2f}\n\n"
            f"{icon} <b>បម្រែបម្រួលប្រចាំថ្ងៃ:</b> {sign}${chg:,.2f} ({sign}{pct:.2f}%)\n\n"
            f"{summary_block}"
            f"🕐 <b>ធ្វើបច្ចុប្បន្នភាព:</b>\n"
            f"{time_str}\n\n"
            f"🔗 <i>ប្រភព: {price_data.get('source', 'Institutional Spot Gold Feed')}</i>"
        )
        return msg

    @staticmethod
    def format_upcoming_alert(event: dict, minutes_left: int) -> str:
        """Formats upcoming high-impact event alert (e.g. 15m or 5m countdown)."""
        time_str = event.get("release_time_str", "")
        title = event.get("title", "")
        currency = event.get("currency", "USD")
        impact = event.get("impact", "HIGH")
        
        reason = (
            f"{title} អាចជះឥទ្ធិពលខ្លាំងលើកម្លាំងរូបិយប័ណ្ណ USD "
            f"និងការរំពឹងទុកលើអត្រាការប្រាក់របស់ Fed ដែលនឹងធ្វើឱ្យតម្លៃមាស XAUUSD "
            f"មានបម្រែបម្រួលខ្លាំង (High Volatility)។"
        )

        header = f"🚨 <b>UPCOMING HIGH IMPACT NEWS</b>"
        if minutes_left <= 5:
            header = f"🚨 <b>{minutes_left} MINUTES TO NEWS RELEASE!</b>"

        msg = (
            f"{header}\n\n"
            f"🇺🇸 <b>រូបិយប័ណ្ណ:</b> {currency}\n"
            f"📰 <b>ព្រឹត្តិការណ៍:</b> {title}\n\n"
            f"🕐 <b>ម៉ោងចេញផ្សាយ:</b> {time_str}\n\n"
            f"⏳ <b>នៅសល់ពេល:</b> {minutes_left} នាទី\n\n"
            f"🔴 <b>កម្រិតផលប៉ះពាល់:</b> {impact}\n\n"
            f"🥇 <b>XAUUSD:</b>\n"
            f"⚠️ <b>អាចមានការប្រែប្រួលតម្លៃខ្លាំង (High Volatility Possible)</b>\n\n"
            f"🧠 <b>មូលហេតុចម្បង:</b>\n"
            f"{reason}\n\n"
            f"⏳ <b>យុទ្ធសាស្ត្រ:</b> សូមរង់ចាំ Price Action បញ្ជាក់ទិសដៅច្បាស់លាស់មុននឹងធ្វើការជួញដូរ។"
        )
        return msg

    @staticmethod
    def format_actual_release_alert(event: dict, analysis: dict) -> str:
        """Formats immediate flash alert when Actual economic data is released."""
        title = event.get("title", "")
        currency = event.get("currency", "USD")
        actual = event.get("actual", "N/A")
        forecast = event.get("forecast", "N/A")
        previous = event.get("previous", "N/A")
        time_str = event.get("release_time_str", "")
        source = event.get("source", "ForexFactory / Global Economic Calendar")

        msg = (
            f"🚨 <b>FLASH: ទិន្នន័យជាក់ស្តែងបានចេញផ្សាយ (ACTUAL RELEASE)</b>\n\n"
            f"🇺🇸 <b>រូបិយប័ណ្ណ:</b> {currency}\n"
            f"📰 <b>ព្រឹត្តិការណ៍:</b> {title}\n"
            f"🕐 <b>ម៉ោង:</b> {time_str}\n\n"
            f"📊 <b>លទ្ធផលទិន្នន័យ:</b>\n"
            f"• <b>ជាក់ស្តែង (Actual):</b> <code>{actual}</code>\n"
            f"• <b>ការព្យាករណ៍ (Forecast):</b> <code>{forecast}</code>\n"
            f"• <b>ទិន្នន័យមុន (Previous):</b> <code>{previous}</code>\n\n"
            f"🚨 <b>តើមានអ្វីកើតឡើង? (WHAT HAPPENED?):</b>\n"
            f"{analysis['what_happened']}\n\n"
            f"🧠 <b>ហេតុអ្វីវាសំខាន់? (WHY IT MATTERS):</b>\n"
            f"{analysis['why_it_matters']}\n\n"
            f"💵 <b>ផលប៉ះពាល់លើ USD (USD IMPACT):</b>\n"
            f"{analysis['usd_impact']}\n\n"
            f"🏦 <b>ការរំពឹងទុកលើអត្រាការប្រាក់/Yields (RATES & YIELDS):</b>\n"
            f"{analysis['rate_yield_impact']}\n\n"
            f"🥇 <b>សម្ពាធលើ XAUUSD (XAUUSD PRESSURE):</b>\n"
            f"👉 <b>{analysis['xau_pressure']}</b>\n\n"
            f"⚠️ <b>ការប្រែប្រួល (VOLATILITY):</b>\n"
            f"បម្រែបម្រួលខ្ពស់! សូមកុំប្រញាប់ដេញតាមតម្លៃភ្លាមៗ\n\n"
            f"⏳ <b>PRICE ACTION CONFIRMATION:</b>\n"
            f"សូមរង់ចាំទៀន M5 ឬ M15 បិទដើម្បីបញ្ជាក់ពីប្រតិកម្មពិតរបស់ទីផ្សារ។\n\n"
            f"🔗 <i>ប្រភព: {source}</i>"
        )
        return msg

    @staticmethod
    def format_breaking_event_alert(news_item: dict, analysis: dict) -> str:
        """Formats breaking news / major geopolitical or unexpected central bank event alert."""
        title = news_item.get("title", "")

        msg = (
            f"🚨 <b>BREAKING EVENT — ព្រឹត្តិការណ៍ទីផ្សារប្រចាំថ្ងៃ!</b>\n\n"
            f"📰 <b>ចំណងជើង:</b> {title}\n\n"
            f"🚨 <b>តើមានអ្វីកើតឡើង?:</b>\n"
            f"{analysis['what_happened']}\n\n"
            f"🧠 <b>ហេតុអ្វីវាសំខាន់?:</b>\n"
            f"{analysis['why_it_matters']}\n\n"
            f"💵 <b>ផលប៉ះពាល់លើ USD:</b>\n"
            f"{analysis['usd_impact']}\n\n"
            f"🏦 <b>សម្ពាធលើ Yields / Risk Sentiment:</b>\n"
            f"{analysis['rate_yield_impact']}\n\n"
            f"🥇 <b>សម្ពាធលើ XAUUSD:</b>\n"
            f"👉 <b>{analysis['xau_pressure']}</b>"
        )
        return msg
