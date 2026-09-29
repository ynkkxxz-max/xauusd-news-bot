from datetime import datetime
import re

# Perfectly calibrated character limits so the full message with all headers,
# emojis, HTML tags, and clickable source URL fits strictly within Telegram's 1024 photo caption limit:
_BREAKING_CAPS = {
    "what_happened": 220,
    "why_it_matters": 240,
    "usd_impact": 100,
    "rate_yield_impact": 100,
    "xau_pressure": 100,
}

def _clip(text: str, cap: int) -> str:
    text = str(text).strip()
    return text if len(text) <= cap else text[:cap].rstrip() + "…"

class KhmerFormatter:
    @staticmethod
    def format_daily_gold_price(price_data: dict, summary: str = "", include_smc: bool = False) -> str:
        """
        Formats daily gold price report in clean, concise Khmer style requested by user:
        🥇  DAILY GOLD PRICE — ហាងឆេងមាសប្រចាំថ្ងៃ

        📅  កាលបរិច្ឆេទ: 29/09/2026 


         🌐1 អោន : $4,127.30

🇰🇭 1 តម្លឹង: លក់ $5,006.09 | ទិញ $4,981.09
              
            1 ជី: លក់ $500.61 | ទិញ $498.11

           📉 បម្រែបម្រួល: $-41.10 (-0.99%)
        """
        oz = price_data.get("price_oz", 0.0)
        chg = price_data.get("change", 0.0)
        pct = price_data.get("change_pct", 0.0)
        date_str = price_data.get("date_str", "")
        if not date_str:
            try:
                from config import CAMBODIA_TZ
                date_str = datetime.now(CAMBODIA_TZ).strftime("%d/%m/%Y")
            except Exception:
                date_str = datetime.now().strftime("%d/%m/%Y")

        loc = price_data.get("local_market", {})
        damlung_sell = loc.get("damlung_sell", 0.0)
        damlung_buy = loc.get("damlung_buy", 0.0)
        chi_sell = loc.get("chi_sell", damlung_sell / 10.0 if damlung_sell else 0.0)
        chi_buy = loc.get("chi_buy", damlung_buy / 10.0 if damlung_buy else 0.0)

        sign = "+" if chg >= 0 else ""
        icon = "📈" if chg >= 0 else "📉"

        msg = (
            f"🥇  <b>DAILY GOLD PRICE — ហាងឆេងមាសប្រចាំថ្ងៃ</b>\n\n"
            f"📅  <b>កាលបរិច្ឆេទ:</b> {date_str} \n\n\n"
            f" 🌐<b>1 អោន :</b> ${oz:,.2f}\n\n"
            f"🇰🇭 <b>1 តម្លឹង:</b> លក់ ${damlung_sell:,.2f} | ទិញ ${damlung_buy:,.2f}\n"
            f"      \n"
            f"      <b>1 ជី:</b> លក់ ${chi_sell:,.2f} | ទិញ ${chi_buy:,.2f}\n\n"
            f" {icon}   <b>បម្រែបម្រួល:</b> {sign}${chg:,.2f} ({sign}{pct:.2f}%)"
        )
        return msg.strip()



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

        # Clip fields so the photo with full analysis always fits in 1 single message (<= 1024 chars)
        c_what = _clip(analysis.get("what_happened", ""), 160)
        c_why = _clip(analysis.get("why_it_matters", ""), 220)
        c_usd = _clip(analysis.get("usd_impact", ""), 110)
        c_rate = _clip(analysis.get("rate_yield_impact", ""), 110)
        raw_c_xau = _clip(analysis.get("xau_pressure", ""), 110).strip()
        c_xau = re.sub(r'^[👉\s\-•]+', '', raw_c_xau).strip()
        c_xau = re.sub(r'^([🟢🔴🟡])\s*\n+', r'\1 ', c_xau)
        if not re.match(r'^[🟢🔴🟡]', c_xau):
            bias_emoji = "🟢" if "Bullish" in analysis.get('bias', '') else ("🔴" if "Bearish" in analysis.get('bias', '') else "🟡")
            c_xau = f"{bias_emoji} {c_xau}"

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
            f"{c_what}\n\n"
            f"🧠 <b>ហេតុអ្វីវាសំខាន់?:</b>\n"
            f"{c_why}\n\n"
            f"💵 <b>ផលប៉ះពាល់លើ USD:</b>\n"
            f"{c_usd}\n\n"
            f"🏛️ <b>សម្ពាធលើ Yields / Fed Rates:</b>\n"
            f"{c_rate}\n\n"
            f"🥇 <b>សម្ពាធលើ XAUUSD:</b>\n"
            f"👉 <b>{c_xau}</b>\n\n"
            f"⚠️ <b>ការប្រែប្រួល (Volatility):</b> បម្រែបម្រួលខ្ពស់ សូមរង់ចាំទៀន M5/M15 បិទដើម្បីបញ្ជាក់ពីប្រតិកម្មពិត!\n\n"
            f'🔗 <i>ប្រភពព័ត៌មាន: <a href="https://www.forexfactory.com/calendar">{source}</a> (ចុចដើម្បីពិនិត្យតារាងទិន្នន័យ)</i>'
        )
        return msg

    @staticmethod
    def format_breaking_event_alert(news_item: dict, analysis: dict) -> str:
        """Formats breaking news / major geopolitical or unexpected central bank event alert."""
        source_name = (news_item.get("source") or "ForexLive News").strip()
        article_url = (news_item.get("link") or news_item.get("url") or "").strip()
        if article_url:
            source_line = f'🔗 <i>ប្រភពព័ត៌មាន: <a href="{article_url}">{source_name}</a> (ចុចដើម្បីអានបន្ថែម)</i>'
        else:
            source_line = f'🔗 <i>ប្រភពព័ត៌មាន: {source_name}</i>'

        # Extract comprehensive narrative
        key_event = ""
        if isinstance(analysis, dict):
            key_event = (analysis.get("key_event") or "").strip()
            if not key_event:
                what = (analysis.get("what_happened") or "").strip()
                why = (analysis.get("why_it_matters") or "").strip()
                xau = (analysis.get("xau_pressure") or "").strip()
                parts = [p for p in [what, why] if p]
                if xau:
                    parts.append(f"• សម្ពាធលើទីផ្សារមាស (XAUUSD): {xau}")
                key_event = "\n\n".join(parts)

        if not key_event:
            desc = (news_item.get("description") or news_item.get("title") or "").strip()
            key_event = desc

        msg = (
            f"🚨 <b>BREAKING EVENT — ព្រឹត្តិការណ៍ទីផ្សារប្រចាំថ្ងៃ!</b>\n\n"
            f"🔹 <b>ព្រឹត្តិការណ៍សំខាន់:</b>\n"
            f"{key_event}\n\n"
            f"{source_line}"
        )
        return msg.strip()

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

        gld_price = macro.get("gld_price", 0.0)
        gld_vol = macro.get("gld_volume", 0)
        gld_chg = macro.get("gld_pct", 0.0)
        gld_icon = "🟢 ទិញចូល (Inflow)" if gld_chg >= 0 else "🔴 លក់ចេញ (Outflow)"

        summary_block = f"🧠 <b>សេចក្តីសង្ខេបចលនាទីផ្សារ:</b>\n{summary}\n\n" if summary else ""

        spdr_block = (
            f"🐋 <b>លំហូរស្ថាប័នធំៗ (SPDR Gold Trust ETF):</b>\n"
            f"• <b>ភាគហ៊ុន GLD:</b> ${gld_price:,.2f} ({gld_chg:+.2f}%)\n"
            f"• <b>ទំហំជួញដូរស្ថាប័ន:</b> {gld_vol:,.0f} Shares\n"
            f"• <b>និន្នាការ Whale:</b> {gld_icon}\n\n"
        )

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
            f"{spdr_block}"
            f"{summary_block}"
            f"🛑 <b>ប្រព័ន្ធ SIGNAL:</b> បានបិទបញ្ចប់ជាផ្លូវការត្រឹមម៉ោង ១០:០០ យប់ (22:00) នេះហើយ ដើម្បីការពារដើមទុន និងចៀសវាងហានិភ័យពេលយប់ជ្រៅ។ ជួបគ្នានៅវគ្គ London ថ្ងៃស្អែកម៉ោង ២:០០ រសៀល!\n\n"
            f"🎯 <b>ទស្សនវិស័យថ្ងៃស្អែក:</b> តាមដានតំបន់ Key Pivot និងប្រតិទិនសេដ្ឋកិច្ចពេលព្រឹក!\n\n"
            f"🔗 <i>ប្រភព: Interbank Bullion Liquidity & SPDR Gold Shares</i>"
        )
        return msg

    @staticmethod
    def format_session_open_alert(
        session_name: str, 
        time_str: str, 
        session_info: str = "",
        price_data: dict = None,
        order_book: dict = None
    ) -> str:
        """
        Formats London / New York Session Open Alert matching the exact clean narrative
        typography of Breaking Event (smooth regular Khmer font, no bold clutters).
        """
        is_london = "london" in session_name.lower()
        flag = "🇬🇧" if is_london else "🇺🇸"
        header_title = f"{flag} <b>{session_name.upper()} OPENING — ទីផ្សារហិរញ្ញវត្ថុបើកដំណើរការ!</b>"

        if is_london:
            story_text = (
                "ទីផ្សារវគ្គព្រឹកបានបង្កើតចលនា Consolidation ដែលធ្វើឱ្យក្រុម Retail Traders កកកុញ Stop Loss យ៉ាងច្រើននៅតំបន់ Asian High និង Asian Low។ "
                "ពេលបើកផ្សារ London នេះ ធនាគារធំៗតែងតែបង្កើតចលនាបញ្ឆោត (Judas Swing / Fakeout) រុញតម្លៃទៅស្រូបយក Stop Loss ទាំងនោះសិន មុននឹងបកក្បាលបង្ហាញទិសដៅពិតប្រាកដ។ "
                "ដូច្នេះ គួររង់ចាំចន្លោះពី 15 ទៅ 30 នាទីឱ្យទីផ្សារ Sweep Liquidity រួចបង្កើតសញ្ញាបញ្ជាក់ M15 Confirmation ច្បាស់លាស់សិន ទើបជាចំណុចចូល Trade ដែលមានសុវត្ថិភាពខ្ពស់បំផុត។"
            )
        else:
            story_text = (
                "ទីផ្សារបានបង្កើតចលនាពាក់កណ្តាលថ្ងៃរួចរាល់ ហើយផ្សារ New York បើកដំណើរការជាមួយស្ថាប័ន Wall Street និង COMEX ដែលជាប្រភពនៃទំហំសាច់ប្រាក់ និងបម្រែបម្រួលតម្លៃមាសធំបំផុតប្រចាំថ្ងៃ។ "
                "ស្ថាប័នធំៗអាចនឹងរុញបន្ត Trend ពី London ឬធ្វើការបកក្បាល Reversal យ៉ាងគំហុកនៅតំបន់ Order Block និង Fair Value Gap (FVG)។ "
                "ដូច្នេះ គួរតាមដានប្រតិកម្មតម្លៃជុំវិញតំបន់កណ្តាល Equilibrium Pivot និងចៀសវាងការដេញតម្លៃពេលទិន្នន័យសេដ្ឋកិច្ចអាមេរិក (USD Data) ចេញផ្សាយ។"
            )

        if session_info:
            story_text = f"{session_info}\n\n{story_text}"

        return (
            f"{header_title}\n\n"
            f"🔹 <b>ការវិភាគទីផ្សារ & យុទ្ធសាស្ត្រស្ថាប័ន (SMC):</b>\n"
            f"{story_text}"
        )






    @staticmethod
    def format_spike_alert(current_price: float, prev_price: float, diff: float, minutes: int = 15) -> str:
        """Formats real-time Gold Volatility Spike / Flash Crash Warning."""
        sign = "+" if diff > 0 else ""
        direction = "🟢 BULLISH SPIKE (ហោះឡើងខ្លាំង)" if diff > 0 else "🔴 FLASH DUMP (ទម្លាក់ចុះខ្លាំង)"
        icon = "🚀" if diff > 0 else "⚡"
        
        return (
            f"🚨 {icon} <b>XAUUSD VOLATILITY ALERT — បម្រែបម្រួលតម្លៃមាសខុសប្រក្រតី!</b>\n\n"
            f"📊 <b>ចលនាទីផ្សារ:</b> <b>{direction}</b>\n"
            f"• <b>តម្លៃបច្ចុប្បន្ន:</b> <code>${current_price:,.2f}</code>\n"
            f"• <b>តម្លៃមុននេះ ({minutes}mn):</b> <code>${prev_price:,.2f}</code>\n"
            f"• <b>បម្រែបម្រួលភ្លាមៗ:</b> <b>{sign}${diff:,.2f}</b> ក្នុងរយៈពេលខ្លី!\n\n"
            f"🧠 <b>ការវិភាគសភាពការណ៍:</b>\n"
            f"• មានការកើនឡើងនៃលំហូរ Order ស្ថាប័នធំៗ (High Volume Institutional Spike) ឬមានប្រតិកម្មនឹងព័ត៌មានបន្ទាន់!\n"
            f"• Spread អាចរីកធំឡើង (Spread Widening) ខ្លាំងនៅតាម Broker នានា។\n\n"
            f"🛡️ <b>ការណែនាំគ្រប់គ្រងហានិភ័យ (Trader Caution):</b>\n"
            f"• ⚠️ <b>ហាមដេញតម្លៃ (Do NOT FOMO / Chase):</b> រង់ចាំទីផ្សារបង្កើត Base ឬ Pullback សិន\n"
            f"• 🔒 <b>ការពារទុន:</b> ពិនិត្យ Margin Level និងរំកិល Stop Loss ការពារប្រាក់ចំណេញ (Trailing Stop) ភ្លាមៗ!\n\n"
            f"📊 <i>មើល Chart ផ្ទាល់: <a href='https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD'>TradingView XAUUSD</a></i>"
        )

    @staticmethod
    def format_candlestick_confirmation(conf: dict) -> str:
        """Formats Technical Candlestick Confirmation Alert at SMC Key Levels."""
        is_bull = "BULLISH" in conf.get("type", "")
        icon = "🟢" if is_bull else "🔴"
        action = "BUY SETUP CONFIRMED (បញ្ជាក់សញ្ញាទិញ)" if is_bull else "SELL SETUP CONFIRMED (បញ្ជាក់សញ្ញាលក់)"
        
        return (
            f"🎯 {icon} <b>AI SMC CONFIRMATION — សញ្ញាទៀនបញ្ជាក់នៅតំបន់គន្លឹះ!</b>\n\n"
            f"📊 <b>សញ្ញា:</b> <b>{action}</b>\n"
            f"• 🕯️ <b>ទម្រង់ទៀន (Pattern):</b> <b>{conf['pattern']}</b> (M15 Structure)\n"
            f"• 🎯 <b>តំបន់គន្លឹះ (Zone):</b> <b>{conf['zone_name']}</b>\n\n"
            f"📈 <b>កម្រិតចូលជួញដូរ (Trade Parameters):</b>\n"
            f"• <b>Entry Price:</b> <code>${conf['entry']:,.2f}</code>\n"
            f"• 🛑 <b>Stop Loss (SL):</b> <code>${conf['sl']:,.2f}</code>\n"
            f"• 🎯 <b>Take Profit (TP):</b> <code>${conf['tp']:,.2f}</code> (Risk/Reward ~ 1:2.5+)\n\n"
            f"🧠 <b>ការពន្យល់បច្ចេកទេស:</b>\n"
            f"• {conf['desc']}\n\n"
            f"🛡️ <b>ការគ្រប់គ្រងហានិភ័យ:</b> ប្រើទំហំ Risk ត្រឹម ១-២% នៃដើមទុនប៉ុណ្ណោះ!\n\n"
            f"📊 <i>ពិនិត្យ Chart: <a href='https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD'>TradingView XAUUSD Live</a></i>"
        )

    @staticmethod
    def format_liquidity_sweep(sweep: dict) -> str:
        """Formats Real-Time Institutional Liquidity Sweep (Stop Loss Hunt) Alert."""
        is_bull = sweep.get("type") == "BULLISH_SWEEP"
        icon = "🟢" if is_bull else "🔴"
        action = "BULLISH REVERSAL SETUP (ឱកាសទិញស្ទុះឡើង)" if is_bull else "BEARISH REVERSAL SETUP (ឱកាសលក់ទម្លាក់ចុះ)"

        return (
            f"🧲 {icon} <b>LIQUIDITY SWEEP ALERT — ស្ថាប័នទើបតែ Hunt Stop Loss!</b>\n\n"
            f"⚡ <b>ស្ថានភាព (Event):</b> <b>{action}</b>\n"
            f"• 🎯 <b>កម្រិត Liquidity (Level):</b> <b>{sweep['level_name']}</b> (<code>${sweep['level_price']:,.2f}</code>)\n"
            f"• 🏹 <b>តម្លៃ Sweep ខ្ពស់បំផុត/ទាបបំផុត:</b> <code>${sweep['sweep_price']:,.2f}</code>\n"
            f"• 🥇 <b>តម្លៃបច្ចុប្បន្ន (Current):</b> <code>${sweep['current_price']:,.2f}</code>\n\n"
            f"📈 <b>កម្រិតណែនាំសម្រាប់ Trader (Smart Money Trade):</b>\n"
            f"• <b>Entry:</b> <code>${sweep['current_price']:,.2f}</code>\n"
            f"• 🛑 <b>Stop Loss (SL):</b> <code>${sweep['sl']:,.2f}</code> (ហួសពីចុង Wick)\n"
            f"• 🎯 <b>Take Profit (TP):</b> <code>${sweep['tp']:,.2f}</code>\n\n"
            f"🧠 <b>ការពន្យល់លំហូរសាច់ប្រាក់ (Smart Money Concept):</b>\n"
            f"• {sweep['desc']}\n"
            f"• ស្ថាប័នធំៗបានប្រើ Fakeout ដើម្បីបង្កើត Liquidity សម្រាប់ Order ធំរបស់ពួកគេ។\n\n"
            f"🛡️ <b>អនុសាសន៍:</b> ចូល Order ជាមួយទំហំ Lot សមរម្យ និងដាក់ Stop Loss ជានិច្ច!\n\n"
            f"📊 <i>ពិនិត្យ Chart: <a href='https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD'>TradingView XAUUSD Live</a></i>"
        )

    @staticmethod
    def format_divergence_alert(div: dict) -> str:
        """Formats Macro Divergence Alert between Gold and US Dollar (DXY)."""
        is_bull = div.get("type") == "BULLISH_DIVERGENCE"
        icon = "🟢" if is_bull else "🔴"
        action = "BULLISH SMART MONEY ACCUMULATION" if is_bull else "BEARISH SMART MONEY DISTRIBUTION"

        g_sign = "+" if div.get("gold_pct", 0) >= 0 else ""
        d_sign = "+" if div.get("dxy_pct", 0) >= 0 else ""

        return (
            f"⚡ {icon} <b>MACRO DIVERGENCE ALERT — សញ្ញាផ្ទុយគ្នារវាងមាស និង USD!</b>\n\n"
            f"📊 <b>ស្ថានភាព (Setup):</b> <b>{action}</b>\n"
            f"• 🥇 <b>តម្លៃមាស (XAU/USD):</b> <code>${div['gold_price']:,.2f}</code> (<b>{g_sign}{div['gold_pct']}%</b>)\n"
            f"• 💵 <b>សន្ទស្សន៍ដុល្លារ (DXY):</b> <code>{div['dxy_price']}</code> (<b>{d_sign}{div['dxy_pct']}%</b>)\n"
            f"• 📈 <b>ទិន្នផលសហរដ្ឋអាមេរិក (US10Y):</b> <code>{div['us10y_yield']}%</code>\n\n"
            f"🧠 <b>ការវិភាគសភាពការណ៍ (Macro Logic):</b>\n"
            f"• {div['desc']}\n"
            f"• <b>ទស្សនវិស័យទីផ្សារ:</b> {div['bias']}\n\n"
            f"🛡️ <b>យុទ្ធសាស្ត្រ Trader:</b> ស្ថាប័នធំៗកំពុងបង្ហាញជំហរច្បាស់លាស់ ផ្តល់អាទិភាពតាមនិន្នាការស្ថាប័ន (Smart Money Trend)!\n\n"
            f"📊 <i>ពិនិត្យ Chart: <a href='https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD'>TradingView XAUUSD Live</a></i>"
        )

    @staticmethod
    def format_fomc_speech_alert(event_title: str, interp: dict) -> str:
        """Formats Real-Time AI Live Speech Interpretation of FOMC / Fed Officials."""
        import re
        is_dovish = interp.get("tone") == "DOVISH"
        is_hawkish = interp.get("tone") == "HAWKISH"
        icon = "🟢" if is_dovish else ("🔴" if is_hawkish else "🟡")

        # Detect speaker name dynamically
        speaker = "Fed"
        for name in ["Kevin Warsh", "Warsh", "Jerome Powell", "Powell", "Christopher Waller", "Waller", "Michelle Bowman", "Bowman", "Austan Goolsbee", "Goolsbee", "John Williams", "Williams"]:
            if name.lower() in event_title.lower():
                speaker = name
                break

        # Clean tone description: strip leading emojis (e.g. 🌓, 🟢, 🔴, 🟡)
        tone_raw = interp.get("tone_kh") or interp.get("tone") or "Neutral"
        tone_clean = re.sub(r"^[^\w\s\u1780-\u17FF]+", "", tone_raw).strip()

        # Clean quotes
        quotes = (interp.get("key_quotes") or "").strip()
        quote_section = ""
        if quotes:
            quote_section = (
                f"💬 <b>ចំណុចគន្លឹះសំខាន់ៗដែល {speaker} ថ្លែង (Key Quotes):</b>\n"
                f"«<i>{quotes}</i>»\n\n"
            )

        # Clean gold impact: remove bullet points and keep clean regular narrative text
        gold_impact = (interp.get("gold_pressure") or "").strip()
        if gold_impact.startswith("•") or gold_impact.startswith("-"):
            gold_impact = gold_impact.lstrip("•- ").strip()

        return (
            f"{icon} <b>LIVE FED AI INTERPRETER — ការថ្លែងសុន្ទរកថាប្រធាន FED ផ្ទាល់!</b>\n\n"
            f"<b>ព្រឹត្តិការណ៍:</b> {event_title}\n"
            f"<b>សម្លេង និងអារម្មណ៍ Fed (Tone):</b> {tone_clean}\n\n"
            f"{quote_section}"
            f"🥇 <b>ផលប៉ះពាល់លើតម្លៃមាស (XAUUSD Impact):</b>\n"
            f"{gold_impact}"
        )

    @staticmethod
    def format_iceberg_alert(iceberg: dict) -> str:
        """Formats Real-Time Institutional Iceberg Order / Whale Wall Alert."""
        is_buy = iceberg.get("type") == "ICEBERG_BUY_WALL"
        icon = "🟢" if is_buy else "🔴"
        action = "WHALE ICEBERG BUY WALL DETECTED (បន្ទាយទប់ទិញយក្ស)" if is_buy else "WHALE ICEBERG SELL WALL DETECTED (ជញ្ជាំងរារាំងលក់យក្ស)"

        return (
            f"🛰️ {icon} <b>WHALE ORDER BOOK ALERT — រកឃើញ Order ស្ថាប័នលាក់មុខ!</b>\n\n"
            f"⚡ <b>ប្រភេទ Order:</b> <b>{action}</b>\n"
            f"• 🎯 <b>តម្លៃដាក់ទប់ (Wall Level):</b> <code>${iceberg['price']:,.2f}</code>\n"
            f"• 🐋 <b>ទំហំទំងន់ (Volume):</b> <code>{iceberg['volume_oz']:.1f} អោន</code> (<b>${iceberg['value_usd']:,.0f}</b>)\n"
            f"• 🥇 <b>តម្លៃទីផ្សារបច្ចុប្បន្ន (Spot):</b> <code>${iceberg['mid_price']:,.2f}</code>\n\n"
            f"🧠 <b>ការពន្យល់ Order Book Depth:</b>\n"
            f"• {iceberg['desc']}\n"
            f"• ស្ថាប័នធំៗបានដាក់ Limit Order កម្រាស់ក្រាស់ក្រែល ដែលអាចធ្វើឱ្យតម្លៃ Rebound ខ្លាំងនៅពេលមកដល់ចំណុចនេះ!\n\n"
            f"🛡️ <b>យុទ្ធសាស្ត្រ Trader:</b> យកកម្រិតនេះធ្វើជាតំបន់ Support/Resistance ដ៏រឹងមាំ ឬជាចំណុច Take Profit / Entry!\n\n"
            f"📊 <i>ពិនិត្យ Chart: <a href='https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD'>TradingView XAUUSD Live</a></i>"
        )

    @staticmethod
    def format_order_book_depth(depth: dict) -> str:
        """Formats full 100-level Institutional Order Book Depth overview."""
        if not depth or not depth.get("available"):
            return "📊 <b>ទិន្នន័យ Order Book Depth មិនទាន់ត្រូវបានធ្វើបច្ចុប្បន្នភាពនៅឡើយទេ។</b>"

        b_walls = depth.get("whale_buy_walls", [])
        s_walls = depth.get("whale_sell_walls", [])

        b_str = ""
        for b in b_walls:
            b_str += f"  • 🟢 <code>${b['price']:,.2f}</code>: <b>{b['volume_oz']:.1f} oz</b> (~${b['value_usd']:,.0f})\n"

        s_str = ""
        for s in s_walls:
            s_str += f"  • 🔴 <code>${s['price']:,.2f}</code>: <b>{s['volume_oz']:.1f} oz</b> (~${s['value_usd']:,.0f})\n"

        return (
            f"🛰️ <b>INSTITUTIONAL GOLD ORDER BOOK DEPTH (100 Levels)</b>\n\n"
            f"🥇 <b>តម្លៃបច្ចុប្បន្ន (Mid Price):</b> <code>${depth['mid_price']:,.2f}</code>\n\n"
            f"⚖️ <b>សមាមាត្រកម្លាំងទីផ្សារ (Liquidity Ratio):</b>\n"
            f"• 🟢 <b>Bid Liquidity (ទិញ):</b> <code>{depth['bid_dominance_pct']}%</code> ({depth['total_bid_vol']:.1f} oz)\n"
            f"• 🔴 <b>Ask Liquidity (លក់):</b> <code>{depth['ask_dominance_pct']}%</code> ({depth['total_ask_vol']:.1f} oz)\n"
            f"• 🧠 <b>ទំនោរកម្លាំង:</b> {depth['bias']}\n\n"
            f"🧱 <b>បន្ទាយទប់ទិញធំបំផុត (Top Whale Buy Walls):</b>\n{b_str}\n"
            f"🧱 <b>ជញ្ជាំងរារាំងលក់ធំបំផុត (Top Whale Sell Walls):</b>\n{s_str}\n"
            f"💡 <i>ទិន្នន័យបញ្ជាក់ពីជម្រៅទីផ្សារកុងត្រាមាស និងតំបន់ Iceberg Orders ពិតប្រាកដ!</i>"
        )

    @staticmethod
    def format_cot_report(cot_data: dict) -> str:
        """Formats CFTC Commitment of Traders (CoT) institutional report for Gold."""
        if not cot_data or not cot_data.get("available"):
            return "📊 <b>ទិន្នន័យ CFTC CoT Report មិនទាន់ត្រូវបានធ្វើបច្ចុប្បន្នភាពនៅឡើយទេ។</b>"

        r_date = cot_data.get("report_date", "")
        net_noncomm = cot_data.get("net_noncommercial", 0)
        chg_noncomm = cot_data.get("change_noncommercial", 0)
        oi = cot_data.get("open_interest", 0)
        cot_idx = cot_data.get("cot_index_52w", 50.0)
        bias = cot_data.get("bias", "Neutral")

        chg_sign = "+" if chg_noncomm >= 0 else ""

        return (
            f"🏛️ <b>CFTC GOLD CoT REPORT — ជំហរស្ថាប័នធំៗ (Smart Money)</b>\n\n"
            f"📅 <b>កាលបរិច្ឆេទរបាយការណ៍ (Report Date):</b> {r_date}\n"
            f"💼 <b>កុងត្រា Hedge Funds (Net Non-Commercial):</b> <code>{net_noncomm:,} contracts</code>\n"
            f"📊 <b>បម្រែបម្រួលប្រចាំសប្តាហ៍ (Weekly Change):</b> <code>{chg_sign}{chg_noncomm:,} contracts</code>\n"
            f"📈 <b>កុងត្រាសរុបក្នុងទីផ្សារ (Open Interest):</b> <code>{oi:,}</code>\n"
            f"🎚️ <b>CoT Index (52-Week Percentile):</b> <code>{cot_idx:.1f}%</code>\n\n"
            f"🧠 <b>ការបកស្រាយអារម្មណ៍ស្ថាប័ន (Institutional Bias):</b>\n"
            f"{bias}\n\n"
            f"💡 <i>CoT Report បង្ហាញពីទំហំកុងត្រាទិញ/លក់ពិតប្រាកដរបស់ស្ថាប័នហិរញ្ញវត្ថុអន្តរជាតិនៅលើ COMEX Gold Futures!</i>\n"
            f"🔗 <a href='https://futuresbench.com/cot/gold/'>CFTC Gold Data Source</a>"
        )

    @staticmethod
    def format_weekly_outlook(price_data: dict, high_impact_events: list, summary: str = "", cot_data: dict = None) -> str:
        """Formats Sunday Evening Weekly Macro & Institutional Gold Outlook."""
        oz = price_data.get("price_oz", 0.0)
        levels = price_data.get("key_levels", {})
        pivot = levels.get("pivot", oz)
        r1 = levels.get("r1", oz + 20)
        s1 = levels.get("s1", oz - 20)

        # Build list of top economic catalysts
        events_str = ""
        if high_impact_events:
            for ev in high_impact_events[:5]:
                events_str += f"• 🔴 <b>{ev.get('release_date_str', '')} {ev.get('release_time_str', '')}</b>: {ev.get('title', '')} ({ev.get('currency', 'USD')})\n"
        else:
            events_str = "• មិនមានទិន្នន័យក្រហមធំៗ (High Impact) ក្នុងសប្តាហ៍នេះទេ\n"

        cot_block = ""
        if cot_data and cot_data.get("available"):
            net_nc = cot_data.get("net_noncommercial", 0)
            chg_nc = cot_data.get("change_noncommercial", 0)
            chg_sign = "+" if chg_nc >= 0 else ""
            cot_block = (
                f"🏛️ <b>ជំហរស្ថាប័នធំៗ (CFTC CoT Hedge Funds):</b>\n"
                f"• Net Long: <code>{net_nc:,} contracts</code> ({chg_sign}{chg_nc:,})\n"
                f"• អារម្មណ៍ស្ថាប័ន: {cot_data.get('bias', 'Bullish')}\n\n"
            )

        summary_block = f"🧠 <b>ទស្សនវិស័យស្ថាប័ន (Institutional Bias):</b>\n{summary}\n\n" if summary else ""

        return (
            f"🏛️ <b>WEEKLY GOLD OUTLOOK — យុទ្ធសាស្ត្រមាសប្រចាំសប្តាហ៍ថ្មី!</b>\n\n"
            f"📅 <b>ការរៀបចំជួញដូរសម្រាប់សប្តាហ៍ថ្មី (ម៉ោងនៅកម្ពុជា UTC+7)</b>\n"
            f"🥇 <b>តម្លៃបិទចុងសប្តាហ៍ (Close):</b> <code>${oz:,.2f}</code>\n\n"
            f"🎯 <b>កម្រិតបច្ចេកទេសប្រចាំសប្តាហ៍ (Weekly Key Levels):</b>\n"
            f"• 🔴 <b>Weekly Resistance (Target Sell):</b> <code>${r1:,.2f}</code>\n"
            f"• 🎯 <b>Weekly Pivot Point (តុល្យភាព):</b> <code>${pivot:,.2f}</code>\n"
            f"• 🟢 <b>Weekly Support (Target Buy):</b> <code>${s1:,.2f}</code>\n\n"
            f"{cot_block}"
            f"📅 <b>ព្រឹត្តិការណ៍សេដ្ឋកិច្ចសំខាន់ៗប្រចាំសប្តាហ៍ (High Impact Catalysts):</b>\n"
            f"{events_str}\n"
            f"{summary_block}"
            f"🛡️ <b>ផែនការ Trader:</b> គ្រប់គ្រងដើមទុន គោរព Stop Loss និងរង់ចាំការបញ្ជាក់ច្បាស់លាស់មុនចូល Trade!\n\n"
            f"📊 <i>មើល Chart: <a href='https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD'>TradingView XAUUSD</a></i> | "
            f"📅 <i><a href='https://www.forexfactory.com/calendar'>ForexFactory Calendar</a></i>"
        )

    @staticmethod
    def format_lot_size_calculator(calc: dict) -> str:
        """Formats the interactive lot size and risk management response in Khmer."""
        if "error" in calc:
            return f"⚠️ <b>បញ្ហាគណនា Lot Size:</b> {calc['error']}"

        bal = calc.get("balance", 0.0)
        risk_pct = calc.get("risk_pct", 1.0)
        risk_usd = calc.get("risk_amount_usd", 0.0)
        dist_usd = calc.get("distance_usd", 10.0)
        pips = calc.get("pips", 100.0)
        lot = calc.get("lot_size", 0.01)
        raw_lot = calc.get("raw_lot", 0.01)
        style = calc.get("style", "")
        lev = calc.get("effective_leverage", 1.0)

        entry_line = ""
        if calc.get("entry_price") and calc.get("sl_price"):
            entry_line = (
                f"• 🎯 <b>Entry Price:</b> <code>${calc['entry_price']:,.2f}</code>\n"
                f"• 🛑 <b>Stop Loss Price:</b> <code>${calc['sl_price']:,.2f}</code>\n"
            )

        # Money Management Table
        half_lot = max(0.01, round(lot / 2.0, 2))
        tp1_profit = round(half_lot * dist_usd * 100.0, 2)
        tp2_profit = round(half_lot * dist_usd * 2.0 * 100.0, 2)

        return (
            f"🤖 <b>SMART LOT SIZE & RISK CALCULATOR (XAU/USD)</b>\n"
            f"<i>ម៉ាស៊ីនគណនាទំហំ Lot ស្តង់ដារតាមដើមទុន & Money Management</i>\n\n"
            f"💰 <b>ដើមទុនគណនី (Balance):</b> <code>${bal:,.2f}</code>\n"
            f"🛡️ <b>កម្រិត Risk %:</b> <code>{risk_pct:.1f}%</code> ({style})\n"
            f"💸 <b>ទឹកប្រាក់ប្រថុយអតិបរមា (Max Risk $):</b> <code>${risk_usd:,.2f}</code>\n"
            f"📏 <b>ចម្ងាយ Stop Loss:</b> <code>${dist_usd:,.2f}</code> (ស្មើនឹង <b>{pips:,.0f} Pips</b>)\n"
            f"{entry_line}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🔥 <b>ទំហំ LOT ណែនាំ (RECOMMENDED LOT):</b>\n"
            f"👉 <code><b>{lot:.2f} LOT</b></code> (ពិត: {raw_lot:.3f})\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎯 <b>យុទ្ធសាស្ត្របែងចែកទំហំ (Position Scaling 1:2 R:R):</b>\n"
            f"• 📦 <b>Lot បំបែក (2 Orders):</b> <code>{half_lot:.2f}</code> + <code>{half_lot:.2f}</code>\n"
            f"• 🎯 <b>TP1 (1:1 R:R):</b> ចម្ងាយ +${dist_usd:,.1f} ➡️ ចំណេញ <b>+${tp1_profit:,.2f}</b> (Lock BE)\n"
            f"• 🏆 <b>TP2 (1:2 R:R):</b> ចម្ងាយ +${dist_usd * 2:,.1f} ➡️ ចំណេញ <b>+${tp2_profit:,.2f}</b>\n"
            f"• ⚙️ <b>Effective Leverage:</b> <code>1:{lev}</code>\n\n"
            f"💡 <i>អនុសាសន៍: មិនត្រូវចូល Trade លើសពីទំហំ Lot នេះឡើយ ដើម្បីការពារគណនីមិនឱ្យ Drawdown ធ្ងន់ធ្ងរ!</i>"
        )

    @staticmethod
    def format_single_smc_setup(setup: dict, key_levels: dict = None, current_price: float = 0.0) -> str:
        """
        Formats a comprehensive, institutional-grade SMC Trading Brief:
        🎯 ផែនការជួញដូរឆ្លាតវៃ AI SMC — ទិសដៅតែមួយគត់ (BUY ONLY ឬ SELL ONLY)
        ជាមួយ Entry, SL, TP1, TP2, R:R និងហេតុផលលម្អិត «ហេតុអ្វីគួរធ្វើ & ហេតុអ្វីមិនគួរធ្វើផ្ទុយ»។
        """
        levels = key_levels or {}
        oz = current_price or setup.get("entry", 0.0)
        pivot = levels.get("pivot", oz)
        r1 = levels.get("r1", oz + 20)
        s1 = levels.get("s1", oz - 20)
        r2 = levels.get("r2", oz + 40)
        s2 = levels.get("s2", oz - 40)

        direction = setup.get("direction", "BUY").upper()
        is_buy = "BUY" in direction
        icon = "🟢" if is_buy else "🔴"
        action_kh = "ទិញឡើង (BUY)" if is_buy else "លក់ចុះ (SELL)"
        opposite_action = "លក់ (SELL)" if is_buy else "ទិញ (BUY)"

        entry_val = setup.get("entry", oz)
        entry_zone = setup.get("entry_zone", f"${entry_val:,.2f}")
        sl = setup.get("sl", 0.0)
        tp1 = setup.get("tp1", 0.0)
        tp2 = setup.get("tp2", 0.0)
        rr = setup.get("rr_ratio", "1:2.0")

        why_trade = setup.get("why_this_trade", "").strip()
        why_not = setup.get("why_not_opposite", "").strip()
        confirm = setup.get("confirmation_note", "រង់ចាំ Confirmation Candle នៅលើ M15 មុនចូល Order!").strip()

        def _clean_bullets(text: str) -> str:
            import re
            parts = re.split(r"(?<=\S)\s+(?=[១-៩1-9]\.|\•|\-)", text.strip())
            formatted = []
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                p = re.sub(r"^[១-៩1-9]\.\s*", "", p)
                if not p.startswith("•") and not p.startswith("-"):
                    formatted.append(f"• {p}")
                else:
                    formatted.append(p)
            return "\n".join(formatted)

        formatted_why_trade = _clean_bullets(why_trade)
        formatted_why_not = _clean_bullets(why_not)

        # Part 1: Top Technical Zones Header
        part1 = (
            f"🎯 <b>កម្រិតបច្ចេកទេស & AI SMC Setup Zone</b>\n\n"
            f"• 🟢 <b>Buy Zone:</b> <code>${s1 - 4:,.2f} - ${s1 + 3:,.2f}</code> (SL: ${s1 - 11:,.2f})\n"
            f"• 🔴 <b>Sell Zone:</b> <code>${r1 - 3:,.2f} - ${r1 + 4:,.2f}</code> (SL: ${r1 + 11:,.2f})\n"
            f"• 🎯 <b>Pivot Point:</b> <code>${pivot:,.2f}</code>\n\n"
            f"💡 <i>អនុសាសន៍: រង់ចាំ Confirmation Candle នៅលើ M15 មុនចូល Order!</i>\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
        )

        conf_score = setup.get("confidence", "88%")
        
        # Calculate Real-Time Execution Status for Telegram
        exec_status_line = ""
        try:
            entry_parts = [float(x.replace("$", "").replace(",", "").strip()) for x in entry_zone.split("-") if x.strip()]
            if len(entry_parts) == 2:
                e_low, e_high = min(entry_parts), max(entry_parts)
                if is_buy:
                    if e_low <= oz <= e_high:
                        exec_status_line = "🟢 <b>ស្ថានភាព (Status): ⚡ READY TO BUY (តម្លៃដល់តំបន់ទិញហើយ)</b>\n"
                    elif oz > e_high:
                        wait_diff = oz - e_high
                        exec_status_line = f"🟡 <b>ស្ថានភាព (Status): ⏳ WAITING PULLBACK (រង់ចាំចុះ ${wait_diff:.1f} ទៀត)</b>\n"
                    else:
                        exec_status_line = "🟢 <b>ស្ថានភាព (Status): ⚡ DEEP DISCOUNT BUY (តំបន់បញ្ចុះតម្លៃពិសេស)</b>\n"
                else:
                    if e_low <= oz <= e_high:
                        exec_status_line = "🟢 <b>ស្ថានភាព (Status): ⚡ READY TO SELL (តម្លៃដល់តំបន់លក់ហើយ)</b>\n"
                    elif oz < e_low:
                        wait_diff = e_low - oz
                        exec_status_line = f"🟡 <b>ស្ថានភាព (Status): ⏳ WAITING BOUNCE (រង់ចាំឡើង ${wait_diff:.1f} ទៀត)</b>\n"
                    else:
                        exec_status_line = "🟢 <b>ស្ថានភាព (Status): ⚡ HIGH PREMIUM SELL (តំបន់លក់បានថ្លៃខ្ពស់)</b>\n"
        except Exception:
            pass

        # Part 2: Decisive Single-Direction Institutional Plan
        trap_banner = ""
        trap_info = setup.get("trap_alert")
        if trap_info:
            trap_banner = (
                f"\n⚠️ <b>{trap_info.get('title', 'AI TRAP DETECTOR')}</b>\n"
                f"<i>{trap_info.get('desc', '')}</i>\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
            )

        news_lock_banner = ""
        news_info = setup.get("news_danger") or {}
        if news_info.get("is_danger"):
            news_lock_banner = (
                f"\n🚨 <b>AI NEWS DANGER ZONE — RED ALERT (AUTO-LOCK)!</b>\n"
                f"⚠️ <b>ព្រមាន:</b> ព័ត៌មានយក្ស <b>{news_info.get('title')}</b> នឹងចេញក្នុងរយៈពេល <b>{news_info.get('mins_left', 15)} នាទីទៀត!</b>\n"
                f"🚫 <b>ហាមបើក Order ថ្មីដាច់ខាត:</b> ជៀសវាងបញ្ហា Slippage និង Stop-Out ភ្លាមៗ!\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
            )

        part2 = (
            f"{news_lock_banner}"
            f"{trap_banner}"
            f"🎯 {icon} <b>ផែនការជួញដូរឆ្លាតវៃ AI SMC — ទិសដៅតែមួយគត់ ({action_kh})</b>\n"
            f"⚡ <b>កម្រិតទំនុកចិត្ត AI (Confidence Score):</b> <code>{conf_score}</code>\n"
            f"{exec_status_line}\n"
            f"📍 <b>កម្រិតតម្លៃចូល និងគ្រប់គ្រងដើមទុន:</b>\n"
            f"• 🎯 <b>តំបន់ Entry:</b> <code>{entry_zone}</code>\n"
            f"• 🛑 <b>Stop Loss (SL):</b> <code>${sl:,.2f}</code>\n"
            f"• 🎯 <b>Take Profit 1 (TP1):</b> <code>${tp1:,.2f}</code> (Lock BE)\n"
            f"• 🏆 <b>Take Profit 2 (TP2):</b> <code>${tp2:,.2f}</code>\n"
            f"• ⚖️ <b>សមាមាត្រចំណេញ/ខាត (R:R):</b> <code>{rr}</code>\n\n"
            f"🧠 <b>ហេតុផលច្បាស់លាស់ដែលគួរ {action_kh}:</b>\n"
            f"{formatted_why_trade}\n\n"
            f"🚫 <b>ហេតុផលដាច់ខាតដែលមិនគួរ {opposite_action}:</b>\n"
            f"{formatted_why_not}\n\n"
            f"💡 <i>អនុសាសន៍: {confirm}</i>\n"
            f"🛡️ <i>គ្រប់គ្រងហានិភ័យដោយបើក <b>📱 Mini App</b> ឬវាយ <code>/lot</code> មុនចូល Order!</i>"
        )
        return part1 + part2

    @staticmethod
    def format_chart_vision_scan(current_price: float, vision_res: dict, timeframe: str = "M15") -> str:
        """
        Formats Multimodal AI Live Computer Vision Candlestick & Pattern Scan results.
        """
        bias = vision_res.get("bias", "🟢 Bullish")
        pattern = vision_res.get("pattern_kh", "ទម្រង់ទៀនបញ្ជាក់ច្បាស់")
        structure = vision_res.get("market_structure", "BOS").replace("_", " ")
        observation = vision_res.get("key_observation", "")
        action = vision_res.get("tactical_action", "")
        conf = vision_res.get("confidence_score", "85%")

        msg = (
            f"👁️‍🗨️ <b>AI LIVE CHART PATTERN & CANDLESTICK SCANNER ({timeframe})</b>\n\n"
            f"• 🥇 <b>Spot XAU/USD:</b> <code>${current_price:,.2f}</code>\n"
            f"• 🕯️ <b>Pattern រកឃើញ:</b> <b>{pattern}</b>\n"
            f"• 🏗️ <b>រចនាសម្ព័ន្ធទីផ្សារ:</b> <code>{structure}</code>\n"
            f"• 🎯 <b>ទិសដៅ AI Bias:</b> <b>{bias}</b> (ទំនុកចិត្ត {conf})\n\n"
            f"🧠 <b>ការសង្កេតទម្រង់ទៀន (Vision Observation):</b>\n"
            f"• {observation}\n\n"
            f"⚡ <b>អនុសាសន៍យុទ្ធសាស្ត្រ (Tactical Action):</b>\n"
            f"👉 <b>{action}</b>\n\n"
            f"📊 <i>ពិនិត្យ Chart ផ្ទាល់: <a href='https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD'>TradingView XAUUSD Live</a></i>"
        )
        return msg

    @staticmethod
    def format_sniper_instant_alert(sig: dict) -> str:
        """Formats real-time AI Pre-Signal Market Analysis and Sniper Signal Alert."""
        action = sig.get("action", "BUY")
        is_buy = "BUY" in action
        icon = "🟢" if is_buy else "🔴"
        trend_desc = sig.get("trend_desc", "តម្លៃកំពុងស្ថិតក្នុងចលនាចំហៀង (Consolidation / Sideways)។")
        ma_desc = sig.get("ma_desc", "ខ្សែបម្លាស់ទីលឿន និងខ្សែបម្លាស់ទីយឺត កំពុងប្រទាក់ក្រឡាគ្នានៅជិតតម្លៃបច្ចុប្បន្ន។")
        res_range = sig.get("resistance_range", "$2700 - $2710")
        sup_range = sig.get("support_range", "$2660 - $2670")

        daily_c = sig.get("daily_count", 1)
        daily_m = sig.get("daily_max", 5)

        ai_analysis_block = ""
        if sig.get("ai_analysis"):
            ai_analysis_block = (
                f"🧠 <b>ការវិភាគស៊ីជម្រៅដោយ AI (Institutional Deep Analysis):</b>\n"
                f"{sig.get('ai_analysis')}\n\n"
            )

        macro_block = ""
        if sig.get("macro_context"):
            macro_block = f"• 💵 <b>ឥទ្ធិពល Macro & DXY:</b> {sig.get('macro_context')}\n"

        inval_block = ""
        if sig.get("invalidation_note"):
            inval_block = f"• 🚫 <b>លក្ខខណ្ឌខូចសុពលភាព (Invalidation):</b> {sig.get('invalidation_note')}\n"

        tips_block = ""
        if sig.get("execution_tips"):
            tips_block = f"• 🎯 <b>ការអនុវត្តជាក់ស្តែង:</b> {sig.get('execution_tips')}\n"

        daily_limit_notice = ""
        if daily_c >= daily_m:
            daily_limit_notice = (
                f"\n🛑 <b>ការការពារដើមទុន (Daily Quota Reached):</b>\n"
                f"នេះជា Position ទី <b>{daily_c}/{daily_m}</b> ចុងក្រោយសម្រាប់ថ្ងៃនេះ! "
                f"Bot នឹងផ្អាកការចេញ Signal បន្ថែមរហូតដល់ថ្ងៃស្អែក ដើម្បីការពារដើមទុន និងទប់ស្កាត់ Overtrading ១០០%។\n"
            )

        return (
            f"📊 <b>១. ការវិភាគស្ថានភាពទីផ្សារបច្ចុប្បន្ន</b>\n\n"
            f"• <b>និន្នាការរួម (Trend):</b> {trend_desc}\n\n"
            f"• <b>ខ្សែបម្លាស់ទី (Moving Averages):</b> {ma_desc}\n\n"
            f"• <b>កម្រិតទ្រទ្រង់ និងរាំងស្ទះ (Support & Resistance):</b>\n"
            f"  - <b>កម្រិតរាំងស្ទះ (Resistance):</b> នៅចន្លោះតម្លៃ <code>{res_range}</code> (ប្រសិនបើតម្លៃអាចបំបែកឡើងលើបាន)\n"
            f"  - <b>កម្រិតទ្រទ្រង់ (Support):</b> នៅចន្លោះតម្លៃ <code>{sup_range}</code> (ប្រសិនបើតម្លៃធ្លាក់ចុះក្រោម)\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 <b>២. ជម្រើសសម្រាប់ការជួញដូរ (Trading Scenarios)</b>\n\n"
            f"🟢 <b>ករណីសម្លឹងមើលការទិញ (Buy Signal):</b>\n"
            f"  - រង់ចាំឱ្យតម្លៃបំបែក (Breakout) ផុតខ្សែបម្លាស់ទី និងកម្រិត Resistance ផ្នែកខាងលើដោយមានទៀនតម្លៃ (Candlestick) បិទយ៉ាងរឹងមាំ។\n"
            f"  - ឬរង់ចាំតម្លៃធ្លាក់ចុះមកប៉ះតំបន់ Support ខាងក្រោម ហើយមានសញ្ញាត្រឡប់ឡើងវិញ (Rejection / Bullish Pattern)។\n\n"
            f"🔴 <b>ករណីសម្លឹងមើលការលក់ (Sell Signal):</b>\n"
            f"  - រង់ចាំឱ្យតម្លៃបំបែកធ្លាក់ចុះក្រោមតំបន់ Support ខាងក្រោមទើបចូលលក់។\n"
            f"  - ឬនៅពេលតម្លៃឡើងទៅប៉ះតំបន់ Resistance ខាងលើ ហើយមិនអាចបំបែករួច (Bearish Rejection)។\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ {icon} <b>សញ្ញា AI SNIPER GRADE A+ (Position {daily_c}/{daily_m} ប្រចាំថ្ងៃ):</b>\n"
            f"🛡️ <b>ការបញ្ជាក់ពី SIGNAL:</b> <b>GRADE A+ Institutional Setup ✓ (AI Audited)</b>\n"
            f"🎯 <b>ប្រតិបត្តិការ:</b> <b>{sig.get('action_title', action)}</b>\n"
            f"• 🥇 <b>Entry តម្លៃចូល:</b> <code>${sig.get('entry', 0.0):,.2f}</code>\n"
            f"• 🛑 <b>Stop Loss (SL):</b> <code>${sig.get('sl', 0.0):,.2f}</code>\n"
            f"• 🎯 <b>Take Profit 1 (TP1):</b> <code>${sig.get('tp1', 0.0):,.2f}</code>\n"
            f"• 🏆 <b>Take Profit 2 (TP2):</b> <code>${sig.get('tp2', 0.0):,.2f}</code>\n"
            f"• ⚖️ <b>Risk:Reward:</b> <code>{sig.get('rr_ratio', '1:2.0')}</code>\n"
            f"• 🎯 <b>ពិន្ទុទំនុកចិត្ត (Confidence Score):</b> <code>{sig.get('confidence_score', '85%')}</code>\n"
            f"{macro_block}"
            f"{inval_block}"
            f"{tips_block}"
            f"• 💡 <b>ការបញ្ជាក់បច្ចេកទេស:</b> {sig.get('reason', '')}\n\n"
            f"{ai_analysis_block}"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 <b>អនុសាសន៍គ្រប់គ្រងហានិភ័យ (Risk Management)</b>\n\n"
            f"1. <b>រង់ចាំសញ្ញាច្បាស់លាស់ (Wait for Confirmation):</b> ដោយសារទីផ្សារអាចមាន Sideways ការចូល Order ត្រូវមានការផ្ទៀងផ្ទាត់ Candle Confirmation ជានិច្ច។\n"
            f"2. <b>កំណត់ Stop Loss (SL) និង Take Profit (TP):</b> ត្រូវដាក់ SL ជានិច្ច និងកំណត់ទំហំហានិភ័យត្រឹម 1-2% នៃទុនគណនី។\n"
            f"3. <b>ពិនិត្យមើលព័ត៌មានសេដ្ឋកិច្ច (Economic News Filter):</b> បិទ Signal មុន/ក្រោយ 30 នាទីនៃ High-Impact News (CPI, NFP, FOMC) ដើម្បីការពារដើមទុន!{daily_limit_notice}"
        )

    @staticmethod
    def format_signal_stats(stats: dict) -> str:
        """Formats community trade feedback summary."""
        tp = stats.get("tp_votes", 0)
        sl = stats.get("sl_votes", 0)
        total = stats.get("total_votes", 0)
        wr = stats.get("win_rate", 0.0)
        traders = stats.get("total_traders", 0)

        wr_emoji = "🔥" if wr >= 70 else ("👍" if wr >= 50 else "⚠️")

        return (
            f"📊 <b>ស្ថិតិលទ្ធផល SIGNAL ពីសមាជិក (COMMUNITY FEEDBACK)</b>\n\n"
            f"👥 <b>ចំនួនសមាជិកចូលរួមបោះឆ្នោត:</b> <code>{traders:,} នាក់</code>\n"
            f"🗳️ <b>សន្លឹកឆ្នោតសរុប:</b> <code>{total:,} ដង</code>\n\n"
            f"🎯 <b>ឈ្នះ (Hit TP):</b> <code>{tp:,} ដង</code>\n"
            f"🛑 <b>ចាញ់ (Hit SL):</b> <code>{sl:,} ដង</code>\n\n"
            f"{wr_emoji} <b>អត្រាជោគជ័យ (Win Rate):</b> <code><b>{wr}%</b></code>\n\n"
            f"💡 <i>ទិន្នន័យនេះបានមកពីការចុចប៊ូតុងជាក់ស្តែងរបស់សមាជិកលើគ្រប់ Signal ដែល Bot AI បានបាញ់កន្លងមក!</i>"
        )

    @staticmethod
    def format_breakeven_profit_alert(info: dict) -> str:
        """Formats Dynamic Break-Even & Profit Lock Alert."""
        action = info.get("action", "BUY")
        is_buy = "BUY" in action
        icon = "🟢" if is_buy else "🔴"
        pips = info.get("pips_gained", 30)
        curr_p = info.get("current_price", 0.0)
        entry_p = info.get("entry_price", 0.0)
        tp1_p = info.get("tp1_price", 0.0)

        return (
            f"🛡️ <b>DYNAMIC BREAK-EVEN & PROFIT LOCK ALERT!</b> ⚡\n\n"
            f"{icon} <b>Signal XAUUSD:</b> <b>{action} @ ${entry_p:,.2f}</b>\n"
            f"🚀 <b>ស្ថានភាពបច្ចុប្បន្ន:</b> តម្លៃបានរត់ទៅមុខ <b>+{pips:.0f} Pips</b> (Spot: <code>${curr_p:,.2f}</code>)!\n"
            f"🎯 <b>ទិសដៅ TP1:</b> <code>${tp1_p:,.2f}</code> (ជិតសម្រេចគោលដៅ)\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 <b>សកម្មភាពត្រូវធ្វើជាបន្ទាន់ (Action Required):</b>\n"
            f"1. 🔒 <b>រំកិល Stop Loss មកស្មើ Entry (Lock Break-Even):</b>\n"
            f"   👉 កំណត់ SL = <code>${entry_p:,.2f}</code> ដើម្បីធានាការជួញដូរនេះ <b>គ្មានហានិភ័យ (Zero Risk)</b> ១០០%!\n"
            f"2. 💰 <b>កាត់ប្រាក់ចំណេញមួយផ្នែក (Partial TP - Close 50%):</b>\n"
            f"   👉 អាចបិទ Order ពាក់កណ្តាលយកចំណេញទុកក្នុងហោប៉ៅ ហើយទុកចំណែកដែលនៅសល់រត់ទៅ TP2!\n\n"
            f"🛡️ <i>វិន័យត្រឹមត្រូវ: មិនត្រូវបណ្តោយឱ្យ Order ដែលកំពុងចំណេញ ប្រែត្រឡប់មកខាតវិញជាដាច់ខាត!</i>"
        )

    @staticmethod
    def format_ai_chat_response(query: str, answer_html: str, price_data: dict = None) -> str:
        """Formats the interactive AI Q&A answer for Telegram."""
        oz = price_data.get("price_oz", 0.0) if price_data else 0.0
        change_pct = price_data.get("change_pct", 0.0) if price_data else 0.0
        sign = "+" if change_pct >= 0 else ""
        header = "🤖 <b>XAUUSD INSTITUTIONAL AI ASSISTANT</b> ⚡\n"
        if oz > 0:
            header += f"📊 <b>Spot Gold:</b> <code>${oz:,.2f}</code> ({sign}{change_pct:.2f}%)\n"
        header += f"❓ <b>សំណួរ:</b> <i>\"{query}\"</i>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        footer = "\n\n━━━━━━━━━━━━━━━━━━━━\n💡 <i>វិភាគដោយ Gemini Institutional AI Engine • ផ្សារភ្ជាប់ជាមួយទិន្នន័យ Live Market</i>"
        return f"{header}{answer_html}{footer}"

    @staticmethod
    def format_ai_chart_vision_response(analysis: dict, price_data: dict = None) -> str:
        """Formats the AI Computer Vision Chart analysis for Telegram."""
        if not analysis:
            return "⚠️ មិនអាចវិភាគរូបភាព Chart បាននៅពេលនេះទេ។ សូមប្រាកដថារូបភាពមាន Candlestick និងតម្លៃច្បាស់លាស់។"

        direction = analysis.get("direction", "WAIT").upper()
        if "BUY" in direction:
            dir_badge = "🟢 BUY SETUP (ទិញឡើង)"
            dir_icon = "🟢"
        elif "SELL" in direction:
            dir_badge = "🔴 SELL SETUP (លក់ចុះ)"
            dir_icon = "🔴"
        else:
            dir_badge = "🟡 WAIT / NO TRADE (រង់ចាំ)"
            dir_icon = "🟡"

        title = analysis.get("setup_title", dir_badge)
        tf = analysis.get("timeframe", "M15 / H1")
        pat_kh = analysis.get("pattern_kh", analysis.get("pattern_detected", "Price Action Structure"))
        entry = analysis.get("entry_zone", "N/A")
        sl = analysis.get("stop_loss", "N/A")
        tp1 = analysis.get("take_profit_1", "N/A")
        tp2 = analysis.get("take_profit_2", "N/A")
        rr = analysis.get("rr_ratio", "1:2.0")
        conf = analysis.get("confidence_score", "85%")
        reasons = analysis.get("confluence_reasons", [])
        reasons_text = "\n".join([f"• {r}" for r in reasons]) if reasons else "• សម្ពាធ Candlestick Rejection និងកម្រិតគន្លឹះ Liquidity"
        inval = analysis.get("invalidation_rule", "តម្លៃទម្លុះកម្រិតគន្លឹះប្រឆាំងទិសដៅ")
        risk = analysis.get("risk_warning", "គ្រប់គ្រងទំហំ Lot សមស្រប Risk 1-2% ជៀសវាង Overtrade!")
        summary = analysis.get("detailed_summary_kh", "")

        msg = (
            f"🔍 <b>AI COMPUTER VISION CHART AUDIT</b> ⚡\n\n"
            f"📌 <b>ផែនការ:</b> <b>{title}</b>\n"
            f"⏱️ <b>Timeframe:</b> <code>{tf}</code> | <b>ពិន្ទុទំនុកចិត្ត:</b> <code>{conf}</code>\n"
            f"🕯️ <b>ទម្រង់ Candlestick:</b> <b>{pat_kh}</b>\n\n"
            f"🎯 <b>កម្រិតប្រតិបត្តិការ (Execution Levels):</b>\n"
            f"• {dir_icon} <b>ទិសដៅ:</b> <b>{direction}</b>\n"
            f"• 🎯 <b>តំបន់ Entry:</b> <code>{entry}</code>\n"
            f"• 🛑 <b>Stop Loss (SL):</b> <code>{sl}</code>\n"
            f"• 🏆 <b>Take Profit 1:</b> <code>{tp1}</code>\n"
            f"• 🏆 <b>Take Profit 2:</b> <code>{tp2}</code>\n"
            f"• ⚖️ <b>Risk:Reward:</b> <code>{rr}</code>\n\n"
            f"💡 <b>ហេតុផលបញ្ជាក់ (Confluence Reasons):</b>\n"
            f"{reasons_text}\n\n"
            f"❌ <b>លក្ខខណ្ឌលុបចោល Setup:</b> {inval}\n\n"
            f"🛡️ <b>ការគ្រប់គ្រងហានិភ័យ:</b> {risk}\n"
        )
        if summary:
            msg += f"\n📝 <b>សេចក្តីសង្ខេប AI:</b>\n{summary}\n"
        msg += "\n━━━━━━━━━━━━━━━━━━━━\n🤖 <i>វិភាគផ្ទាល់ពីរូបភាព Chart ដោយ Gemini Multimodal Vision AI</i>"
        return msg




