import logging
import requests

logger = logging.getLogger(__name__)

class MarketMacroCorrelation:
    """
    Fetches live market correlation metrics:
    - US Dollar Index (DXY)
    - US 10-Year Treasury Yield (US10Y)
    - SPDR Gold Trust ETF (GLD) Whale Activity
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    def fetch_macro_correlations(self) -> dict:
        dxy = self._fetch_ticker("DX-Y.NYB")
        us10y = self._fetch_ticker("^TNX")
        gld = self._fetch_ticker("GLD")

        return {
            "dxy_price": dxy.get("price", 100.50),
            "dxy_change": dxy.get("change", 0.0),
            "dxy_pct": dxy.get("pct", 0.0),
            "us10y_yield": us10y.get("price", 4.25),
            "us10y_change": us10y.get("change", 0.0),
            "gld_price": gld.get("price", 240.0),
            "gld_pct": gld.get("pct", 0.0),
            "gld_volume": gld.get("volume", 0),
        }

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
