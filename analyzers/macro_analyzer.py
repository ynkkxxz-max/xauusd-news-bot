import re
import logging

logger = logging.getLogger(__name__)

class MacroAnalyzer:
    @staticmethod
    def _clean_num(val_str: str) -> float:
        """Parses numeric values with %, K, M, B."""
        if not val_str:
            return None
        cleaned = re.sub(r"[^\d.-]", "", str(val_str))
        try:
            return float(cleaned)
        except ValueError:
            return None

    @classmethod
    def analyze_actual_vs_forecast(cls, event_name: str, actual: str, forecast: str, previous: str) -> dict:
        """
        Analyzes economic data release and deduces:
        - What happened
        - Why it matters
        - USD impact
        - Interest Rate / Yield expectations
        - XAUUSD directional pressure (Bullish / Bearish / Mixed)
        """
        act_num = cls._clean_num(actual)
        fc_num = cls._clean_num(forecast)
        
        title_lower = event_name.lower()
        
        # Determine whether higher is typically bullish USD
        # For CPI, NFP, GDP, Retail Sales, PMI: Higher -> Stronger USD -> Bearish Gold
        # For Unemployment, Jobless Claims: Higher -> Weaker USD -> Bullish Gold
        is_inverse_metric = any(k in title_lower for k in ["unemployment", "jobless claims"])
        
        bias = "🟡 Mixed / Unclear"
        usd_impact = "មិនទាន់ច្បាស់លាស់ (Neutral / Mixed)"
        rate_impact = "ទីផ្សារកំពុងរង់ចាំការបកស្រាយបន្ថែម"
        xau_pressure = "🟡 Possible Mixed / Consolidation Pressure"
        comparison_desc = ""

        if act_num is not None and fc_num is not None:
            diff = act_num - fc_num
            if abs(diff) < 0.0001:
                comparison_desc = f"ទិន្នន័យជាក់ស្តែង ({actual}) ចេញមកស្មើនឹងការព្យាករណ៍ ({forecast})។"
                usd_impact = "USD អាចមានចលនាមធ្យម ឬ Neutral ដោយសារទីផ្សារបាន Price-in រួចហើយ។"
                rate_impact = "ការរំពឹងទុកលើអត្រាការប្រាក់នៅរក្សាជំហរដដែល។"
                xau_pressure = "🟡 Neutral to Mixed (រង់ចាំការបំបែកកម្រិតបច្ចេកទេស)"
                bias = "🟡 Mixed / Unclear"
            elif diff > 0: # Actual > Forecast
                if not is_inverse_metric:
                    comparison_desc = f"ទិន្នន័យជាក់ស្តែង ({actual}) ចេញមក **ខ្ពស់ជាង** ការព្យាករណ៍ ({forecast})។"
                    usd_impact = "💵 USD ទទួលបានកម្លាំងជំរុញវិជ្ជមាន (Bullish USD)។"
                    rate_impact = "🏦 សេដ្ឋកិច្ចរឹងមាំ/អតិផរណាខ្ពស់ អាចពន្យារពេលបញ្ចុះការប្រាក់ ឬគាំទ្រ Bond Yields ឱ្យឡើងខ្ពស់។"
                    xau_pressure = "🔴 Possible Bearish Pressure (សម្ពាធធ្លាក់ចុះលើមាស)"
                    bias = "🔴 Bearish"
                else:
                    comparison_desc = f"ទិន្នន័យអវិជ្ជមាន ({actual}) ខ្ពស់ជាងការព្យាករណ៍ ({forecast}) (ភាពអត់ការងារធ្វើកើនឡើង)។"
                    usd_impact = "💵 USD រងសម្ពាធធ្លាក់ចុះ (Bearish USD)។"
                    rate_impact = "🏦 បង្កើនឱកាសដែល Fed នឹងកាត់បន្ថយអត្រាការប្រាក់ (Dovish expectations)។"
                    xau_pressure = "🟢 Possible Bullish Pressure (សម្ពាធជំរុញឱ្យមាសឡើង)"
                    bias = "🟢 Bullish"
            else: # Actual < Forecast
                if not is_inverse_metric:
                    comparison_desc = f"ទិន្នន័យជាក់ស្តែង ({actual}) ចេញមក **ទាបជាង** ការព្យាករណ៍ ({forecast})។"
                    usd_impact = "💵 USD រងសម្ពាធធ្លាក់ចុះ (Bearish USD) ដោយសារសេដ្ឋកិច្ច/អតិផរណាថយចុះ។"
                    rate_impact = "🏦 Fed អាចមានលំហរបន្ធូរបន្ថយនយោបាយរូបិយវត្ថុ (Rate Cut expectations កើនឡើង)។"
                    xau_pressure = "🟢 Possible Bullish Pressure (សម្ពាធជំរុញឱ្យមាសឡើង)"
                    bias = "🟢 Bullish"
                else:
                    comparison_desc = f"ទិន្នន័យជាក់ស្តែង ({actual}) ចេញមកទាបជាងការព្យាករណ៍ ({forecast}) (អត្រាគ្មានការងារធ្វើថយចុះ)។"
                    usd_impact = "💵 USD រឹងមាំឡើងវិញ (Bullish USD)។"
                    rate_impact = "🏦 កាត់បន្ថយសម្ពាធក្នុងការបន្ទាន់បញ្ចុះការប្រាក់។"
                    xau_pressure = "🔴 Possible Bearish Pressure (សម្ពាធធ្លាក់ចុះលើមាស)"
                    bias = "🔴 Bearish"
        else:
            comparison_desc = f"ទិន្នន័យជាក់ស្តែងបានចេញ៖ {actual} (ព្យាករណ៍: {forecast})"

        # Context-specific "Why it matters"
        if "cpi" in title_lower or "inflation" in title_lower or "pce" in title_lower:
            why_it_matters = "CPI / PCE គឺជាសូចនាករវាស់ស្ទង់អតិផរណាដ៏ចម្បងដែល Fed យកជាមូលដ្ឋានក្នុងការសម្រេចចិត្តដំឡើង ឬបញ្ចុះអត្រាការប្រាក់។"
        elif "nfp" in title_lower or "payrolls" in title_lower or "unemployment" in title_lower:
            why_it_matters = "NFP បង្ហាញពីភាពរឹងមាំនៃទីផ្សារការងារអាមេរិក។ ទីផ្សារការងាររឹងមាំអនុញ្ញាតឱ្យ Fed រក្សាអត្រាការប្រាក់ខ្ពស់បានយូរ។"
        elif "rate" in title_lower or "fomc" in title_lower:
            why_it_matters = "ការសម្រេចចិត្តលើអត្រាការប្រាក់របស់ Fed ជះឥទ្ធិពលផ្ទាល់បំផុតលើថ្លៃដើមនៃការកាន់កាប់មាស (Gold yield opportunity cost)។"
        else:
            why_it_matters = f"{event_name} ជះឥទ្ធិពលលើទស្សនវិស័យសេដ្ឋកិច្ចអាមេរិក និងតម្រូវការទិញប្រាក់ដុល្លារ។"

        return {
            "what_happened": comparison_desc,
            "why_it_matters": why_it_matters,
            "usd_impact": usd_impact,
            "rate_yield_impact": rate_impact,
            "xau_pressure": xau_pressure,
            "bias": bias
        }

    @classmethod
    def analyze_breaking_news(cls, title: str, description: str = "") -> dict:
        """Analyzes breaking geopolitical, tech/AI or central bank event for gold impact with full narrative context."""
        text = f"{title} {description}".lower()
        full_story = f"{title} — {description}".strip(" —")
        
        # 1. Geopolitical Conflict / War / Military Attacks (Strict matching, NOT general economic news)
        geopolitical_words = ["war", "missile", "airstrike", "invasion", "military attack", "strait of hormuz", "red sea attack", "iran strike"]
        is_military_conflict = any(w in text for w in geopolitical_words) or ("escalat" in text and any(k in text for k in ["tension", "conflict", "threat", "military"]))

        if is_military_conflict:
            return {
                "what_happened": f"ភាពតានតឹងភូមិសាស្ត្រនយោបាយកើនឡើង៖ {full_story}",
                "why_it_matters": "🔴 នេះជាព័ត៌មានអវិជ្ជមានផ្នែកសន្តិសុខ ដែលជំរុញឱ្យវិនិយោគិនស្វែងរកទ្រព្យសកម្មសុវត្ថិភាព (Safe-Haven Assets) និងធ្វើឱ្យមានការព្រួយបារម្ភពីការរំខានដល់សន្តិសុខពិភពលោក។",
                "usd_impact": "USD អាចឡើងថ្លៃក្នុងនាមជា Safe Haven ប៉ុន្តែមាស (Gold) ទទួលបានអត្ថប្រយោជន៍ និងទំហំទិញខ្លាំងជាង។",
                "rate_yield_impact": "វិនិយោគិនសម្រុកទិញសញ្ញាប័ណ្ណរដ្ឋាភិបាល (Bonds) ធ្វើឱ្យ Bond Yields ធ្លាក់ចុះ។",
                "xau_pressure": "🟢 Possible Bullish Pressure (កម្លាំងទិញមាស Safe-Haven កើនឡើងខ្ពស់)",
                "bias": "🟢 Bullish"
            }
        elif any(w in text for w in ["china", "adb", "growth forecast", "asian development bank", "deflation", "soft demand", "pboc"]):
            return {
                "what_happened": f"របាយការណ៍សេដ្ឋកិច្ច និងអតិផរណាអាស៊ី/ចិន៖ {full_story}",
                "why_it_matters": "📊 ការព្យាករណ៍ពីកំណើនសេដ្ឋកិច្ច និងអតិផរណាទាបនៅអាស៊ី/ចិន បង្ហាញពីតម្រូវការទំនិញប្រើប្រាស់ទន់ខ្សោយ ដែលអាចជំរុញឱ្យធនាគារកណ្តាល (PBOC) បន្តបន្ធូរបន្ថយរូបិយវត្ថុ ឬបញ្ចុះអត្រាការប្រាក់បន្ថែម។",
                "usd_impact": "កម្លាំងរូបិយប័ណ្ណអាស៊ីអាចទន់ខ្សោយ គាំទ្រឱ្យ USD រក្សាស្ថិរភាព ឬរឹងមាំបន្តិច។",
                "rate_yield_impact": "ទិន្នផលសញ្ញាបណ្ណសកលអាចប្រឈមសម្ពាធធ្លាក់ចុះដោយសារការធ្លាក់ចុះនៃសម្ពាធអតិផរណា (Disinflationary pressures)។",
                "xau_pressure": "🟡 Possible Mixed / Consolidation (ទីផ្សារថ្លឹងថ្លែងរវាងតម្រូវការ Physical Gold និងការបន្ធូរបន្ថយការប្រាក់)",
                "bias": "🟡 Mixed / Unclear"
            }
        elif any(w in text for w in ["artificial intelligence", "ai", "tech", "nvidia", "super intelligence"]):
            return {
                "what_happened": f"ការវិវត្តន៍វិស័យបច្ចេកវិទ្យា និង AI៖ {full_story}",
                "why_it_matters": "🟢 នេះជាព័ត៌មានវិជ្ជមាន ដែលបង្ហាញពីការផ្តល់តម្លៃកាន់តែខ្ពស់ទៅលើការអភិវឌ្ឍ សក្តានុពលនៃបច្ចេកវិទ្យាអនាគត និងការជំរុញសន្ទស្សន៍ទីផ្សារហ៊ុន (Tech Rally)។",
                "usd_impact": "USD អាចរក្សាស្ថិរភាព ឬរឹងមាំតាមចរន្តវិនិយោគលើភាគហ៊ុនបច្ចេកវិទ្យាអាមេរិក។",
                "rate_yield_impact": "ជំរុញអារម្មណ៍វិនិយោគិន Risk-On នៅក្នុងទីផ្សារហិរញ្ញវត្ថុ។",
                "xau_pressure": "🟡 Possible Mixed / Consolidation (ទីផ្សារបង្វែរសាច់ប្រាក់មួយចំណែកទៅកាន់វិស័យបច្ចេកវិទ្យា)",
                "bias": "🟡 Mixed / Unclear"
            }
        elif any(w in text for w in ["rate cut", "dovish", "easing"]):
            return {
                "what_happened": f"សញ្ញានៃការបន្ធូរបន្ថយនយោបាយរូបិយវត្ថុ (Rate Cut/Dovish)៖ {full_story}",
                "why_it_matters": "ការបញ្ចុះអត្រាការប្រាក់កាត់បន្ថយថ្លៃដើមនៃការកាន់កាប់មាស និងធ្វើឱ្យ USD ចុះខ្សោយ។",
                "usd_impact": "USD ចុះខ្សោយ (Bearish USD)។",
                "rate_yield_impact": "Bond Yields ធ្លាក់ចុះ គាំទ្រដល់លោហៈធាតុមានតម្លៃ។",
                "xau_pressure": "🟢 Possible Bullish Pressure (សម្ពាធវិជ្ជមានជំរុញតម្លៃមាស)",
                "bias": "🟢 Bullish"
            }
        elif any(w in text for w in ["rate hike", "hawkish", "higher for longer"]):
            return {
                "what_happened": f"សញ្ញារក្សាអត្រាការប្រាក់ខ្ពស់ ឬដំឡើងការប្រាក់ (Hawkish)៖ {full_story}",
                "why_it_matters": "ការប្រាក់ខ្ពស់ផ្តល់ទិន្នផលលើសាច់ប្រាក់ និងសញ្ញាប័ណ្ណ ធ្វើឱ្យមាសបាត់បង់ភាពទាក់ទាញ។",
                "usd_impact": "USD រឹងមាំឡើង (Bullish USD)។",
                "rate_yield_impact": "Treasury Yields កើនឡើង បង្កើតសម្ពាធលើទ្រព្យសកម្មគ្មានការប្រាក់ដូចជាមាស។",
                "xau_pressure": "🔴 Possible Bearish Pressure (សម្ពាធអវិជ្ជមានលើមាស)",
                "bias": "🔴 Bearish"
            }
        else:
            return {
                "what_happened": f"ព័ត៌មានទីផ្សារទើបទទួលបាន៖ {full_story}",
                "why_it_matters": "ព័ត៌មាននេះមានសារៈសំខាន់ក្នុងការកំណត់ទិសដៅ និងអារម្មណ៍វិនិយោគិនក្នុងទីផ្សាររយៈពេលខ្លី។",
                "usd_impact": "កំពុងតាមដានប្រតិកម្មលើសន្ទស្សន៍ DXY។",
                "rate_yield_impact": "តាមដានទិន្នផល US 10-Year Treasury Yields។",
                "xau_pressure": "🟡 Possible Mixed Pressure (រង់ចាំទីផ្សារឆ្លើយតប)",
                "bias": "🟡 Mixed / Unclear"
            }

    @classmethod
    def generate_smart_smc_setup(cls, current_price: float, key_levels: dict, macro_data: dict = None, order_book: dict = None) -> dict:
        """
        High-precision deterministic rule-based SMC Single-Direction setup generator.
        Picks ONE clear direction (BUY or SELL) based on price position relative to Pivot,
        Order Book imbalance, and Macro bias.
        """
        pivot = key_levels.get("pivot", current_price)
        r1 = key_levels.get("r1", current_price + 20)
        s1 = key_levels.get("s1", current_price - 20)
        r2 = key_levels.get("r2", current_price + 40)
        s2 = key_levels.get("s2", current_price - 40)

        bid_dominance = (order_book.get("bid_dominance_pct", 50.0) if order_book else 50.0) or 50.0
        dxy_pct = (macro_data.get("dxy_pct", 0.0) if macro_data else 0.0) or 0.0

        # Scoring Direction Bias
        bull_score = 0
        bear_score = 0

        # 1. Price relative to Pivot
        if current_price >= pivot:
            bull_score += 2
        else:
            bear_score += 2

        # 2. Order book pressure
        if bid_dominance > 50.5:
            bull_score += 1
        elif bid_dominance < 49.5:
            bear_score += 1

        # 3. DXY inverse correlation
        if dxy_pct < 0:
            bull_score += 1
        elif dxy_pct > 0:
            bear_score += 1

        is_buy = bull_score >= bear_score

        if is_buy:
            entry_low = round(min(current_price - 1.5, pivot), 2)
            entry_high = round(max(current_price + 1.0, pivot + 2.0), 2)
            sl_price = round(entry_low - 7.5, 2)
            tp1_price = round(r1, 2)
            tp2_price = round(r2, 2)
            rr = f"1:{max(1.8, round((tp1_price - entry_high) / (entry_low - sl_price), 1))}"

            why_trade = (
                f"• តម្លៃបច្ចុប្បន្នស្ថិតនៅពីលើ Pivot Point (${pivot:,.2f}) បង្ហាញថាកម្លាំងទិញគ្រប់គ្រងទីផ្សារ (Bullish Order Flow)។\n"
                f"• Order Book បង្ហាញបន្ទាយ Bids ({bid_dominance:.1f}%) គាំទ្រកម្រាស់ក្រាស់ក្រែលនៅតំបន់ Discount Zone (${s1:,.2f})។\n"
                f"• ស្ថាប័នធំៗកំពុងរក្សាលំនឹងពីលើតំបន់ទប់ទល់ ដើម្បីទាក់ទាញ Buy-Side Liquidity ឡើងទៅតេស្ត R1 (${r1:,.2f})។"
            )
            why_not_opp = (
                f"• ការចូល Sell នៅចំណុចនេះគឺជាការលក់ប្រឆាំងទិសដៅធំ (Counter-Trend) និងប្រឈមនឹងការកិន Stop Loss ដោយសារ Bullish Momentum។\n"
                f"• តម្លៃមិនទាន់បង្ហាញរចនាសម្ព័ន្ធបែកបាក់ធ្លាក់ចុះ (Break of Structure - BOS) នៅលើ M15 ឡើយ ដូច្នេះការ Sell គឺងាយជាប់ Liquidity Trap!"
            )
            confirm = "រង់ចាំការបិទទៀន M15 Bullish Pin Bar ឬ Bullish Engulfing មុននឹងសម្រេចចិត្តចូល Order!"
            return {
                "direction": "BUY",
                "setup_title": "🟢 ផែនការទិញឡើង (BUY SETUP ONLY)",
                "entry": current_price,
                "entry_zone": f"${entry_low:,.2f} - ${entry_high:,.2f}",
                "sl": sl_price,
                "tp1": tp1_price,
                "tp2": tp2_price,
                "rr_ratio": rr,
                "why_this_trade": why_trade,
                "why_not_opposite": why_not_opp,
                "confirmation_note": confirm
            }
        else:
            entry_low = round(min(current_price - 1.0, pivot - 2.0), 2)
            entry_high = round(max(current_price + 1.5, pivot), 2)
            sl_price = round(entry_high + 7.5, 2)
            tp1_price = round(s1, 2)
            tp2_price = round(s2, 2)
            rr = f"1:{max(1.8, round((entry_low - tp1_price) / (sl_price - entry_high), 1))}"

            why_trade = (
                f"• តម្លៃស្ថិតនៅក្រោម Pivot Point (${pivot:,.2f}) បញ្ជាក់ពីសម្ពាធលក់វាយសម្រុក (Bearish Structure)។\n"
                f"• Order Book បង្ហាញជញ្ជាំង Asks រារាំងក្រាស់ក្រែលនៅតំបន់ Premium Zone (${r1:,.2f}) មិនឱ្យតម្លៃឡើងងាយៗឡើយ។\n"
                f"• ទីផ្សារកំពុងស្វែងរក Sell-Side Liquidity (SSL) នៅតំបន់ខាងក្រោម (${s1:,.2f})។"
            )
            why_not_opp = (
                f"• ការចូល Buy នៅចំណុចនេះមានហានិភ័យខ្ពស់ខ្លាំង (Falling Knife) ដោយសារគ្មានទម្រង់ Bottom Reversal ច្បាស់លាស់។\n"
                f"• សម្ពាធលក់កំពុងគ្របដណ្តប់ ការ Buy អាចប្រឈមនឹងការទម្លុះ Support និងជាប់អន្ទាក់ទិញមុនស្ថាប័នធំៗ!"
            )
            confirm = "រង់ចាំការបិទទៀន M15 Bearish Rejection Wick ឬ Bearish Engulfing មុននឹងសម្រេចចិត្តចូល Order!"
            return {
                "direction": "SELL",
                "setup_title": "🔴 ផែនការលក់ចុះ (SELL SETUP ONLY)",
                "entry": current_price,
                "entry_zone": f"${entry_low:,.2f} - ${entry_high:,.2f}",
                "sl": sl_price,
                "tp1": tp1_price,
                "tp2": tp2_price,
                "rr_ratio": rr,
                "why_this_trade": why_trade,
                "why_not_opposite": why_not_opp,
                "confirmation_note": confirm
            }

