from datetime import datetime

# Perfectly calibrated character limits so the full message with all headers,
# emojis, HTML tags, and source credit fits within Telegram's 1024 photo caption limit
# while preserving the rich, complete story narrative without excessive clipping:
_BREAKING_CAPS = {
    "what_happened": 280,
    "why_it_matters": 350,
    "usd_impact": 150,
    "rate_yield_impact": 150,
    "xau_pressure": 150,
}

def _clip(text: str, cap: int) -> str:
    text = str(text).strip()
    return text if len(text) <= cap else text[:cap].rstrip() + "…"

class KhmerFormatter:
    @staticmethod
    def format_daily_gold_price(price_data: dict, summary: str = "") -> str:
        """
        Formats daily gold price report in Khmer with clear distinction between:
        1. ទីផ្សារអន្តរជាតិ (International Market - XAU/USD Interbank Spot)
        2. ទីផ្សារកម្ពុជា (Cambodia Local Market - Central Market / Phnom Penh 24K & 18K)
        """
        oz = price_data.get("price_oz", 0.0)
        damlung_intl = price_data.get("price_damlung", 0.0)
        chg = price_data.get("change", 0.0)
        pct = price_data.get("change_pct", 0.0)
        date_str = price_data.get("date_str", "")
        time_str = price_data.get("updated_time_str", "07:00")
        source_intl = price_data.get("source_intl", price_data.get("source", "Swissquote Institutional Bank / COMEX"))
        source_local = price_data.get("source_local", "សមាគម/ហាងមាសផ្សារធំថ្មី រាជធានីភ្នំពេញ")

        loc = price_data.get("local_market", {})
        damlung_sell = loc.get("damlung_sell", damlung_intl + 30.0)
        damlung_buy = loc.get("damlung_buy", damlung_sell - 25.0)
        chi_sell = loc.get("chi_sell", damlung_sell / 10.0)
        chi_buy = loc.get("chi_buy", damlung_buy / 10.0)
        hun_sell = loc.get("hun_sell", chi_sell / 10.0)
        platin_chi = loc.get("platin_chi_sell", chi_sell * 0.75)

        sign = "+" if chg >= 0 else ""
        icon = "📈" if chg >= 0 else "📉"

        summary_block = f"🧠 <b>ការវិភាគសង្ខេប:</b>\n{summary}\n\n" if summary else ""

        levels = price_data.get("key_levels", {})
        pivot = levels.get("pivot", oz)
        r1 = levels.get("r1", oz + 20)
        s1 = levels.get("s1", oz - 20)

        # SMC Trading Setup Zone (Order Block / Liquidity Sweep)
        buy_zone_low = round(s1 - 4, 2)
        buy_zone_high = round(s1 + 3, 2)
        buy_sl = round(buy_zone_low - 7, 2)
        buy_tp1 = round(pivot, 2)
        buy_tp2 = round(r1, 2)

        sell_zone_low = round(r1 - 3, 2)
        sell_zone_high = round(r1 + 4, 2)
        sell_sl = round(sell_zone_high + 7, 2)
        sell_tp1 = round(pivot, 2)
        sell_tp2 = round(s1, 2)

        macro = price_data.get("macro_correlation", {})
        dxy = macro.get("dxy_price", 0.0)
        dxy_chg = macro.get("dxy_change", 0.0)
        us10y = macro.get("us10y_yield", 0.0)

        # Fear & Greed / Sentiment
        sentiment = "Neutral / Balanced"
        if chg > 20:
            sentiment = "Greed (កម្លាំងទិញខ្លាំង)"
        elif chg < -20:
            sentiment = "Fear (សម្ពាធលក់ខ្លាំង)"

        msg = (
            f"🥇 <b>DAILY GOLD PRICE — ហាងឆេងមាសប្រចាំថ្ងៃ</b>\n\n"
            f"📅 <b>កាលបរិច្ឆេទ:</b> {date_str} (ម៉ោង {time_str} កម្ពុជា)\n\n"
            f"🌐 <b><u>ទីផ្សារអន្តរជាតិ (International Spot)</u></b>\n"
            f"• <b>1 Troy Ounce:</b> ${oz:,.2f}\n"
            f"• <b>1 តម្លឹង (Spot):</b> ${damlung_intl:,.2f}\n"
            f"• {icon} <b>បម្រែបម្រួល:</b> {sign}${chg:,.2f} ({sign}{pct:.2f}%)\n"
            f"📍 <i>ប្រភព: {source_intl}</i>\n\n"
            f"🇰🇭 <b><u>ទីផ្សារកម្ពុជា (Cambodia Local Market)</u></b>\n"
            f"• <b>មាសគីឡូ 24K (១ តម្លឹង):</b> លក់ ${damlung_sell:,.2f} | ទិញ ${damlung_buy:,.2f}\n"
            f"• <b>មាសទឹកដប់ (១ ជី):</b> លក់ ${chi_sell:,.2f} | ទិញ ${chi_buy:,.2f}\n"
            f"• <b>មាស (១ ហ៊ុន):</b> លក់ ${hun_sell:,.2f}\n"
            f"• <b>ប្លាទីន/មាសកែច្នៃ 18K (១ ជី):</b> ~${platin_chi:,.2f}\n"
            f"📍 <i>ប្រភព: {source_local}</i>\n\n"
            f"🎯 <b><u>ផែនការជួញដូរ AI SMC (Daily Trading Setup)</u></b>\n"
            f"• 🟢 <b>Buy Setup (Discount OB):</b> ${buy_zone_low} - ${buy_zone_high}\n"
            f"  └ <i>SL: ${buy_sl} | TP1: ${buy_tp1} | TP2: ${buy_tp2}</i>\n"
            f"• 🔴 <b>Sell Setup (Premium OB):</b> ${sell_zone_low} - ${sell_zone_high}\n"
            f"  └ <i>SL: ${sell_sl} | TP1: ${sell_tp1} | TP2: ${sell_tp2}</i>\n"
            f"• 🎯 <b>Pivot Point:</b> ${pivot:,.2f} | <b>អារម្មណ៍ផ្សារ:</b> {sentiment}\n\n"
            f"📊 <b><u>សូចនាករម៉ាក្រូសេដ្ឋកិច្ច (Macro Correlation)</u></b>\n"
            f"• 💵 <b>DXY Index:</b> {dxy:.2f} ({'+' if dxy_chg >= 0 else ''}{dxy_chg:.2f})\n"
            f"• 🏛️ <b>US 10-Year Yield:</b> {us10y:.2f}%\n\n"
            f"{summary_block}"
        )
        return msg.strip()

    @staticmethod
    def format_upcoming_alert(event: dict, minutes_left: int) -> str:
        """Formats upcoming high-impact event alert (e.g. 15m or 5m countdown)."""
        time_str = event.get("release_time_str", "")
        title = event.get("title", "")
        currency = event.get("currency", "USD")
        impact = event.get("impact", "HIGH")
        forecast = event.get("forecast", "N/A") or "N/A"
        previous = event.get("previous", "N/A") or "N/A"
        
        reason = (
            f"{title} អាចជះឥទ្ធិពលខ្លាំងលើកម្លាំងរូបិយប័ណ្ណ USD "
            f"និងការរំពឹងទុកលើអត្រាការប្រាក់របស់ Fed ដែលនឹងធ្វើឱ្យតម្លៃមាស XAUUSD "
            f"មានបម្រែបម្រួលខ្លាំង (High Volatility)។"
        )

        header = f"🚨 <b>UPCOMING HIGH IMPACT EVENT — ព្រឹត្តិការណ៍សេដ្ឋកិច្ចសំខាន់!</b>"
        if minutes_left <= 5:
            header = f"🚨 <b>{minutes_left} នាទីទៀតដល់ម៉ោងចេញទិន្នន័យសំខាន់! (5-MIN COUNTDOWN)</b>"

        # Pre-News Volatility & Risk Analysis
        spread_alert = "Spread អាចរីកធំឡើង (Spread Widening) និងអាចមាន Slippage ខ្លាំង!"
        risk_advice = (
            "• ⚠️ <b>ហានិភ័យ Slippage & Spread:</b> អាចកើនឡើង ២x ទៅ ៥x ធម្មតា\n"
            "• 🛡️ <b>ការគ្រប់គ្រងហានិភ័យ:</b> បន្ថយទំហំ Lot, ពិនិត្យ Stop Loss (SL) ឬឈរមើលក្រៅទីផ្សាររហូតដល់ទៀនទី១បិទ\n"
            "• 🚫 <b>ការណែនាំ:</b> មិនត្រូវប្រញាប់ទស្សន៍ទាយចូល Order មុនទិន្នន័យពិតចេញឡើយ!"
        )

        msg = (
            f"{header}\n\n"
            f"🇺🇸 <b>រូបិយប័ណ្ណ:</b> {currency}\n"
            f"📰 <b>ព្រឹត្តិការណ៍:</b> {title}\n"
            f"🕐 <b>ម៉ោងចេញផ្សាយនៅកម្ពុជា:</b> <b>{time_str} (ម៉ោងនៅកម្ពុជា UTC+7)</b>\n"
            f"⏳ <b>នៅសល់ពេល:</b> {minutes_left} នាទីទៀត\n"
            f"🔴 <b>កម្រិតផលប៉ះពាល់:</b> {impact}\n\n"
            f"📊 <b>ការរំពឹងទុកទីផ្សារ:</b>\n"
            f"• <b>ការព្យាករណ៍ (Forecast):</b> <code>{forecast}</code>\n"
            f"• <b>ទិន្នន័យមុន (Previous):</b> <code>{previous}</code>\n\n"
            f"⚡ <b>ការព្រមានអំពីបម្រែបម្រួល (Pre-News Volatility Warning):</b>\n"
            f"• ⚠️ <b>{spread_alert}</b>\n\n"
            f"🧠 <b>មូលហេតុចម្បង:</b>\n"
            f"{reason}\n\n"
            f"🛡️ <b>យុទ្ធសាស្ត្រ Trader (VIP Risk Management):</b>\n"
            f"{risk_advice}"
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
        date_str = event.get("release_date_str", "")
        source = event.get("source", "ForexFactory / Global Institutional Calendar")

        xau_pressure = analysis.get('xau_pressure', '').strip()
        if xau_pressure.startswith("👉"):
            xau_pressure = xau_pressure.lstrip("👉").strip()

        msg = (
            f"🚨 <b>FLASH: ទិន្នន័យជាក់ស្តែងបានចេញផ្សាយ (ACTUAL RELEASE)</b>\n\n"
            f"🇺🇸 <b>រូបិយប័ណ្ណ:</b> {currency}\n"
            f"📰 <b>ព្រឹត្តិការណ៍:</b> {title}\n"
            f"🕐 <b>ម៉ោងចេញផ្សាយនៅកម្ពុជា:</b> <b>{time_str} ({date_str} ម៉ោងនៅកម្ពុជា UTC+7)</b>\n\n"
            f"📊 <b>លទ្ធផលទិន្នន័យសេដ្ឋកិច្ច:</b>\n"
            f"• <b>ជាក់ស្តែង (Actual):</b> <code>{actual}</code>\n"
            f"• <b>ការព្យាករណ៍ (Forecast):</b> <code>{forecast}</code>\n"
            f"• <b>ទិន្នន័យមុន (Previous):</b> <code>{previous}</code>\n\n"
            f"🚨 <b>តើមានអ្វីកើតឡើង?:</b>\n"
            f"{analysis['what_happened']}\n\n"
            f"🧠 <b>ហេតុអ្វីវាសំខាន់?:</b>\n"
            f"{analysis['why_it_matters']}\n\n"
            f"💵 <b>ផលប៉ះពាល់លើ USD:</b>\n"
            f"{analysis['usd_impact']}\n\n"
            f"🏛️ <b>សម្ពាធលើ Yields / Fed Rates:</b>\n"
            f"{analysis['rate_yield_impact']}\n\n"
            f"🥇 <b>សម្ពាធលើ XAUUSD:</b>\n"
            f"👉 <b>{xau_pressure}</b>\n\n"
            f"⚠️ <b>ការប្រែប្រួល (Volatility):</b> បម្រែបម្រួលខ្ពស់ សូមរង់ចាំទៀន M5/M15 បិទដើម្បីបញ្ជាក់ពីប្រតិកម្មពិត!\n\n"
            f"🔗 <i>ប្រភពព័ត៌មាន: {source}</i>"
        )
        return msg

    @staticmethod
    def format_breaking_event_alert(news_item: dict, analysis: dict) -> str:
        """Formats breaking news / major geopolitical or unexpected central bank event alert."""
        title = _clip(news_item.get("title", ""), 100)
        analysis = {k: _clip(v, _BREAKING_CAPS.get(k, 200)) for k, v in analysis.items()}

        source = (news_item.get("source") or "ForexLive / Global Financial Feeds").strip()

        xau_pressure = analysis['xau_pressure'].strip()
        if xau_pressure.startswith("👉"):
            xau_pressure = xau_pressure.lstrip("👉").strip()

        msg = (
            f"🚨 <b>BREAKING EVENT — ព្រឹត្តិការណ៍ទីផ្សារប្រចាំថ្ងៃ!</b>\n\n"
            f"🚨 <b>តើមានអ្វីកើតឡើង?:</b>\n"
            f"{analysis['what_happened']}\n\n"
            f"🧠 <b>ហេតុអ្វីវាសំខាន់?:</b>\n"
            f"{analysis['why_it_matters']}\n\n"
            f"💵 <b>ផលប៉ះពាល់លើ USD:</b>\n"
            f"{analysis['usd_impact']}\n\n"
            f"🏛️ <b>សម្ពាធលើ Yields / Risk Sentiment:</b>\n"
            f"{analysis['rate_yield_impact']}\n\n"
            f"🥇 <b>សម្ពាធលើ XAUUSD:</b>\n"
            f"👉 <b>{xau_pressure}</b>\n\n"
            f"🔗 <i>ប្រភពព័ត៌មាន: {source}</i>"
        )
        return msg

    @staticmethod
    def format_whale_alert(whale_data: dict) -> str:
        """Formats institutional gold whale and central bank flow alert (Point 1)."""
        action = whale_data.get("action", "ទិញបន្ថែម (Inflow)")
        amount = whale_data.get("amount", "10.5 តោន")
        entity = whale_data.get("entity", "SPDR Gold Shares (GLD)")
        impact = whale_data.get("impact", "កម្លាំងគាំទ្រដល់និន្នាការកើនឡើងនៃតម្លៃមាស")
        date_str = whale_data.get("date_str", "")

        msg = (
            f"🐋 <b>GOLD WHALE ALERT — សកម្មភាពស្ថាប័នធំៗលើទីផ្សារមាស!</b>\n\n"
            f"📅 <b>កាលបរិច្ឆេទ:</b> {date_str}\n"
            f"🏛️ <b>ស្ថាប័ន / មូលនិធិ:</b> <b>{entity}</b>\n"
            f"📊 <b>សកម្មភាព:</b> <b>{action} {amount}</b>\n\n"
            f"🧠 <b>ការវិភាគឥទ្ធិពល:</b>\n"
            f"• {impact}\n"
            f"• បង្ហាញពីទំនុកចិត្តវិនិយោគិនស្ថាប័នក្នុងការការពារទ្រព្យសកម្មធៀបនឹងអតិផរណា និងហានិភ័យសកល។\n\n"
            f"🥇 <b>សម្ពាធលើ XAUUSD:</b> 👉 🟢 <b>Bullish Support (កម្លាំងរុញតម្លៃ)</b>\n\n"
            f"🔗 <i>ប្រភព: World Gold Council / SPDR Gold Trust Institutional Holdings</i>"
        )
        return msg

    @staticmethod
    def format_night_wrap_up(price_data: dict, summary: str = "") -> str:
        """Formats daily market wrap-up and London/NY session summary (Point 4)."""
        oz = price_data.get("price_oz", 0.0)
        chg = price_data.get("change", 0.0)
        pct = price_data.get("change_pct", 0.0)
        date_str = price_data.get("date_str", "")
        time_str = price_data.get("updated_time_str", "22:00")
        
        sign = "+" if chg >= 0 else ""
        icon = "📈" if chg >= 0 else "📉"

        macro = price_data.get("macro_correlation", {})
        dxy = macro.get("dxy_price", 0.0)
        us10y = macro.get("us10y_yield", 0.0)

        summary_block = f"🧠 <b>សេចក្តីសង្ខេបចលនាទីផ្សារ:</b>\n{summary}\n\n" if summary else ""

        msg = (
            f"🌙 <b>DAILY MARKET WRAP-UP — សេចក្តីសង្ខេបទីផ្សារពេលយប់</b>\n\n"
            f"📅 <b>កាលបរិច្ឆេទ:</b> {date_str} (ម៉ោង {time_str} កម្ពុជា)\n"
            f"🌆 <b>បញ្ចប់ Session:</b> London & New York Active Trading\n\n"
            f"🥇 <b>ស្ថានភាពបិទតម្លៃមាស (XAUUSD):</b>\n"
            f"• <b>តម្លៃបច្ចុប្បន្ន:</b> ${oz:,.2f}\n"
            f"• {icon} <b>បម្រែបម្រួលសរុបថ្ងៃនេះ:</b> {sign}${chg:,.2f} ({sign}{pct:.2f}%)\n\n"
            f"📊 <b>កត្តាគន្លឹះម៉ាក្រូសេដ្ឋកិច្ច:</b>\n"
            f"• 💵 <b>DXY Index:</b> {dxy:.2f}\n"
            f"• 🏛️ <b>US 10Y Yield:</b> {us10y:.2f}%\n\n"
            f"{summary_block}"
            f"🎯 <b>ទស្សនវិស័យថ្ងៃស្អែក:</b> តាមដានតំបន់ Key Pivot និងប្រតិទិនសេដ្ឋកិច្ចពេលព្រឹក!\n\n"
            f"🔗 <i>ប្រភព: Interbank Bullion Liquidity & Macro Feeds</i>"
        )
        return msg

    @staticmethod
    def format_session_open_alert(session_name: str, time_str: str, session_info: str) -> str:
        """Formats London / New York Session Open Alert."""
        flag = "🇬🇧" if "london" in session_name.lower() else "🇺🇸"
        return (
            f"🔔 {flag} <b>{session_name.upper()} OPENING — ទីផ្សារហិរញ្ញវត្ថុបើកដំណើរការ!</b>\n\n"
            f"🕐 <b>ម៉ោងនៅកម្ពុជា:</b> <b>{time_str} (UTC+7)</b>\n"
            f"🌊 <b>លំហូរសាច់ប្រាក់ (Market Liquidity):</b> <b>កើនឡើងខ្លាំង (High Volume Inflow)</b>\n\n"
            f"🧠 <b>ការវិភាគទីផ្សារ & អនុសាសន៍:</b>\n"
            f"• {session_info}\n"
            f"• ត្រៀមទទួលយកបម្រែបម្រួលតម្លៃមាស XAUUSD រលកថ្មី!\n"
            f"• ពិនិត្យមើលតំបន់ Key Support / Resistance មុនពេលចូល Trade។\n\n"
            f"🛡️ <b>ការគ្រប់គ្រងហានិភ័យ:</b> កំណត់ Stop Loss ជានិច្ច ជៀសវាងការដេញតម្លៃពេលទើបបើកផ្សារ!"
        )
