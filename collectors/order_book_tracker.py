import logging
import requests

logger = logging.getLogger(__name__)

class OrderBookDepthTracker:
    """
    Tracks Real-Time Gold Order Book Depth & Institutional Iceberg Orders.
    Analyzes live institutional Bid/Ask depth, liquidity walls, and stealth blocks
    on physical gold-backed reserves (PAXG/USDT institutional gold liquidity feed).
    """
    DEPTH_URL = "https://api.binance.com/api/v3/depth?symbol=PAXGUSDT&limit=100"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    def fetch_order_book_depth(self) -> dict:
        """
        Fetches full 100-level order book and extracts:
        - Total Bid Volume vs Total Ask Volume (Liquidity Ratio)
        - Institutional Iceberg Buy Walls (Support Clusters)
        - Institutional Iceberg Sell Walls (Resistance Clusters)
        - Order Book Imbalance (Bid/Ask Pressure)
        """
        try:
            from collectors.market_cache import market_cache
            cached = market_cache.get_order_book()
            if cached:
                return cached
        except Exception:
            market_cache = None

        try:
            resp = requests.get(self.DEPTH_URL, headers=self.headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                bids = data.get("bids", [])
                asks = data.get("asks", [])

                if not bids or not asks:
                    return {"available": False}

                total_bid_vol = sum(float(b[1]) for b in bids)
                total_ask_vol = sum(float(a[1]) for a in asks)
                current_mid = (float(bids[0][0]) + float(asks[0][0])) / 2.0

                # Calculate Buy/Ask Imbalance Ratio (0 to 100%)
                total_liquidity = total_bid_vol + total_ask_vol or 0.001
                bid_dominance_pct = round((total_bid_vol / total_liquidity) * 100, 1)
                ask_dominance_pct = round((total_ask_vol / total_liquidity) * 100, 1)

                # Identify Top 3 Institutional Whale Walls (Icebergs)
                whale_bids = sorted(bids, key=lambda x: float(x[1]), reverse=True)[:3]
                whale_asks = sorted(asks, key=lambda x: float(x[1]), reverse=True)[:3]

                parsed_whale_bids = [
                    {
                        "price": round(float(p), 2),
                        "volume_oz": round(float(v), 2),
                        "value_usd": round(float(p) * float(v), 0)
                    }
                    for p, v in whale_bids
                ]

                parsed_whale_asks = [
                    {
                        "price": round(float(p), 2),
                        "volume_oz": round(float(v), 2),
                        "value_usd": round(float(p) * float(v), 0)
                    }
                    for p, v in whale_asks
                ]

                # Determine Pressure Bias
                if bid_dominance_pct >= 58.0:
                    bias = "🟢 Strong Institutional Buy Pressure (ជញ្ជាំងទិញរឹងមាំខ្លាំង)"
                elif ask_dominance_pct >= 58.0:
                    bias = "🔴 Strong Institutional Sell Pressure (ជញ្ជាំងលក់ដាក់គាបពីលើ)"
                else:
                    bias = "⚖️ Balanced Depth (តុល្យភាពកម្លាំងទិញ និងលក់)"

                res = {
                    "available": True,
                    "mid_price": round(current_mid, 2),
                    "total_bid_vol": round(total_bid_vol, 2),
                    "total_ask_vol": round(total_ask_vol, 2),
                    "bid_dominance_pct": bid_dominance_pct,
                    "ask_dominance_pct": ask_dominance_pct,
                    "whale_buy_walls": parsed_whale_bids,
                    "whale_sell_walls": parsed_whale_asks,
                    "bias": bias
                }
                if market_cache:
                    market_cache.set_order_book(res)
                return res

        except Exception as e:
            logger.warning(f"[OrderBookDepthTracker] Error fetching order book: {e}")

        return {"available": False}

    def detect_iceberg_anomaly(self) -> dict:
        """
        Detects exceptional institutional iceberg walls:
        Triggers when a single price level holds abnormally high volume (> 20 oz / ~$90,000+)
        representing a massive institutional block or stealth absorption.
        """
        depth = self.fetch_order_book_depth()
        if not depth.get("available"):
            return None

        # Check top buy wall
        buy_walls = depth.get("whale_buy_walls", [])
        if buy_walls and buy_walls[0]["volume_oz"] >= 20.0:
            top_b = buy_walls[0]
            return {
                "type": "ICEBERG_BUY_WALL",
                "price": top_b["price"],
                "volume_oz": top_b["volume_oz"],
                "value_usd": top_b["value_usd"],
                "mid_price": depth["mid_price"],
                "bid_dominance": depth["bid_dominance_pct"],
                "desc": f"ស្ថាប័នធំៗបានដាក់ទប់ Order ទិញយក្ស (Iceberg Buy Wall) ចំនួន {top_b['volume_oz']:.1f} អោន (តម្លៃជាង ${top_b['value_usd']:,.0f}) នៅកម្រិត ${top_b['price']:,.2f}! កម្រិតនេះដើរតួជាបន្ទាយការពារទប់មិនឱ្យធ្លាក់ (Strong Support Wall)!"
            }

        # Check top sell wall
        sell_walls = depth.get("whale_sell_walls", [])
        if sell_walls and sell_walls[0]["volume_oz"] >= 20.0:
            top_s = sell_walls[0]
            return {
                "type": "ICEBERG_SELL_WALL",
                "price": top_s["price"],
                "volume_oz": top_s["volume_oz"],
                "value_usd": top_s["value_usd"],
                "mid_price": depth["mid_price"],
                "ask_dominance": depth["ask_dominance_pct"],
                "desc": f"ស្ថាប័នធំៗបានដាក់ទប់ Order លក់យក្ស (Iceberg Sell Wall) ចំនួន {top_s['volume_oz']:.1f} អោន (តម្លៃជាង ${top_s['value_usd']:,.0f}) នៅកម្រិត ${top_s['price']:,.2f}! កម្រិតនេះដើរតួជាជញ្ជាំងដែកថែបរារាំងការឡើងបន្ត (Heavy Resistance Wall)!"
            }

        return None
