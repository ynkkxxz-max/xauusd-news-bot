import logging
import requests

logger = logging.getLogger(__name__)

class CotCollector:
    """
    Fetches official CFTC Commitment of Traders (CoT) data for Gold (XAUUSD / COMEX Gold Futures).
    Tracks Hedge Funds & Commercial Banks (Smart Money) positioning.
    Source: FuturesBench (Direct CFTC Gold Data API).
    """
    URL = "https://futuresbench.com/api/v1/latest.json"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    def fetch_gold_cot(self) -> dict:
        """
        Returns latest CFTC CoT positioning metrics for Gold:
        - report_date
        - net_noncommercial (Hedge Funds / Speculators Net Long/Short contracts)
        - change_noncommercial (Weekly change in Hedge Fund contracts)
        - net_commercial (Producers / Bullion Banks)
        - open_interest (Total outstanding contracts)
        - cot_index_52w (0 to 100% percentile)
        - bias (Smart Money Sentiment: Extreme Bullish, Bullish, Bearish, etc.)
        """
        try:
            resp = requests.get(self.URL, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                gold_mkt = data.get("markets", {}).get("gold")
                if gold_mkt:
                    report_date = gold_mkt.get("report_date", "")
                    net_noncomm = gold_mkt.get("net_noncommercial", 0)
                    chg_noncomm = gold_mkt.get("change_noncommercial", 0)
                    net_comm = gold_mkt.get("net_commercial", 0)
                    oi = gold_mkt.get("open_interest", 0)
                    cot_index = gold_mkt.get("cot_index_52w", 50.0)

                    # Determine institutional sentiment
                    if net_noncomm > 200000:
                        if chg_noncomm > 0:
                            bias_text = "🟢 Strong Bullish (Hedge Funds បន្តសម្រុកទិញបង្កើន Net Long)"
                        else:
                            bias_text = "🟢 Bullish (Hedge Funds កាន់កាប់កុងត្រាទិញច្រើន ប៉ុន្តែកាត់បន្ថយបន្តិច)"
                    elif net_noncomm > 100000:
                        bias_text = "🟡 Moderate Bullish (កម្លាំងទិញស្ថាប័នមានកម្រិតមធ្យម)"
                    else:
                        bias_text = "🔴 Neutral to Bearish (ស្ថាប័នកាត់បន្ថយទំហំកាន់កាប់មាស)"

                    return {
                        "available": True,
                        "report_date": report_date,
                        "net_noncommercial": net_noncomm,
                        "change_noncommercial": chg_noncomm,
                        "net_commercial": net_comm,
                        "open_interest": oi,
                        "cot_index_52w": cot_index,
                        "bias": bias_text
                    }
        except Exception as e:
            logger.warning(f"[CotCollector] Failed to fetch CFTC CoT data: {e}")

        return {"available": False}
