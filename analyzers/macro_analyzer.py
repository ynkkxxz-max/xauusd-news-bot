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
        
        if any(w in text for w in ["war", "missile", "escalat", "geopolitical", "safe haven", "attack", "iran", "strait of hormuz"]):
            return {
                "what_happened": f"ភាពតានតឹងភូមិសាស្ត្រនយោបាយកើនឡើង៖ {full_story}",
                "why_it_matters": "🔴 នេះជាព័ត៌មានអវិជ្ជមានផ្នែកសន្តិសុខ ដែលជំរុញឱ្យវិនិយោគិនស្វែងរកទ្រព្យសកម្មសុវត្ថិភាព (Safe-Haven Assets) និងធ្វើឱ្យមានការព្រួយបារម្ភពីការរំខានដល់ការផ្គត់ផ្គង់ថាមពលពិភពលោក។",
                "usd_impact": "USD អាចឡើងថ្លៃក្នុងនាមជា Safe Haven ប៉ុន្តែមាស (Gold) ទទួលបានអត្ថប្រយោជន៍ និងទំហំទិញខ្លាំងជាង។",
                "rate_yield_impact": "វិនិយោគិនសម្រុកទិញសញ្ញាប័ណ្ណរដ្ឋាភិបាល (Bonds) ធ្វើឱ្យ Bond Yields ធ្លាក់ចុះ។",
                "xau_pressure": "🟢 Possible Bullish Pressure (កម្លាំងទិញមាស Safe-Haven កើនឡើងខ្ពស់)",
                "bias": "🟢 Bullish"
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
