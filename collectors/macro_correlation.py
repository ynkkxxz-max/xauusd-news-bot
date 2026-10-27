import logging
import requests

logger = logging.getLogger(__name__)

class MarketMacroCorrelation:
    """
    Fetches live market correlation metrics:
    - US Dollar Index (DXY)
    - US 10-Year Treasury Yield (US10Y)
    - SPDR Gold Trust ETF (GLD) Whale Activity
    - Smart Money Macro Divergence Detection
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    def fetch_macro_correlations(self) -> dict:
        try:
            from collectors.market_cache import market_cache
            cached = market_cache.get_macro()
            if cached:
                return cached
        except Exception:
            market_cache = None

        dxy = self._fetch_ticker("DX-Y.NYB")
        us10y = self._fetch_ticker("^TNX")
        gld = self._fetch_ticker("GLD")

        res = {
            "dxy_price": dxy.get("price", 100.50),
            "dxy_change": dxy.get("change", 0.0),
            "dxy_pct": dxy.get("pct", 0.0),
            "us10y_yield": us10y.get("price", 4.25),
            "us10y_change": us10y.get("change", 0.0),
            "gld_price": gld.get("price", 240.0),
            "gld_pct": gld.get("pct", 0.0),
            "gld_volume": gld.get("volume", 0),
        }
        if market_cache:
            market_cache.set_macro(res)
        return res

    def _fetch_ticker(self, symbol: str) -> dict:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
            resp = requests.get(url, headers=self.headers, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                meta = data["chart"]["result"][0]["meta"]
                price = float(meta.get("regularMarketPrice") or 0.0)
                prev = float(meta.get("previousClose") or meta.get("chartPreviousClose") or price)
                change = round(price - prev, 3)
                pct = round((change / prev) * 100, 2) if prev else 0.0
                volume = meta.get("regularMarketVolume", 0)
                return {"price": price, "change": change, "pct": pct, "volume": volume}
        except Exception as e:
            logger.warning(f"Error fetching ticker {symbol}: {e}")
        return {"price": 0.0, "change": 0.0, "pct": 0.0, "volume": 0}

    def detect_divergence(self, gold_price: float, gold_change_pct: float) -> dict:
        """
        Detects Institutional Divergence between Gold and US Dollar (DXY):
        - Classic correlation is strongly inverse (~ -0.85).
        - Bullish Divergence: DXY pushes higher (+0.25% or more) BUT Gold refuses to fall (up or flat >= +0.15%).
          Indicates aggressive Smart Money accumulation of gold despite dollar strength.
        - Bearish Divergence: DXY slides lower (-0.25% or more) BUT Gold fails to rally (down or flat <= -0.15%).
          Indicates institutional distribution / lack of gold buyers despite dollar weakness.
        """
        try:
            macro = self.fetch_macro_correlations()
            dxy_pct = macro.get("dxy_pct", 0.0)
            dxy_price = macro.get("dxy_price", 100.0)
            us10y_yield = macro.get("us10y_yield", 4.0)

            # Bullish Divergence: USD Strong, yet Gold is Stronger
            if dxy_pct >= 0.25 and gold_change_pct >= 0.15:
                return {
                    "type": "BULLISH_DIVERGENCE",
                    "title": "BULLISH MACRO DIVERGENCE (មាសរឹងមាំទប់ទល់នឹង USD)",
                    "gold_price": round(gold_price, 2),
                    "gold_pct": round(gold_change_pct, 2),
                    "dxy_price": round(dxy_price, 2),
                    "dxy_pct": round(dxy_pct, 2),
                    "us10y_yield": round(us10y_yield, 2),
                    "bias": "🟢 Bullish (សញ្ញាទិញឡើងខ្លាំង)",
                    "desc": "ទោះបីជាសន្ទស្សន៍ប្រាក់ដុល្លារ DXY កំពុងកើនឡើងក៏ដោយ ក៏មាសមិនព្រមធ្លាក់ចុះ និងបន្តកើនឡើងស្របគ្នា។ នេះជាសញ្ញាបញ្ជាក់ថាស្ថាប័នធំៗ (Smart Money / Central Banks) កំពុងសម្រុកទិញមាសយ៉ាងសម្បើម!"
                }

            # Bearish Divergence: USD Weak, yet Gold fails to rally
            if dxy_pct <= -0.25 and gold_change_pct <= -0.15:
                return {
                    "type": "BEARISH_DIVERGENCE",
                    "title": "BEARISH MACRO DIVERGENCE (មាសទន់ខ្សោយទោះបី USD ធ្លាក់)",
                    "gold_price": round(gold_price, 2),
                    "gold_pct": round(gold_change_pct, 2),
                    "dxy_price": round(dxy_price, 2),
                    "dxy_pct": round(dxy_pct, 2),
                    "us10y_yield": round(us10y_yield, 2),
                    "bias": "🔴 Bearish (សញ្ញាប្រុងប្រយ័ត្នធ្លាក់ចុះ)",
                    "desc": "ទោះបីជាសន្ទស្សន៍ប្រាក់ដុល្លារ DXY បានធ្លាក់ចុះខ្សោយក៏ដោយ ក៏មាសមិនអាចទាញយកផលប្រយោជន៍ដើម្បីឡើងថ្លៃបានដែរ។ នេះបង្ហាញពីការខ្វះកម្លាំងទិញពីស្ថាប័ន ឬមានការលក់ចេញលាក់មុខ (Distribution)!"
                }
        except Exception as e:
            logger.warning(f"Error detecting divergence: {e}")

        return None
