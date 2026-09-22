import io
import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from config import BASE_DIR, CAMBODIA_TZ

logger = logging.getLogger(__name__)

FONT_PATH = BASE_DIR / "assets" / "DejaVuSans.ttf"
FONT_BOLD_PATH = BASE_DIR / "assets" / "DejaVuSans-Bold.ttf"

class LiquidityHeatmapBuilder:
    """
    Renders Institutional Smart Money Liquidity Heatmap Image (Canvas HD).
    Visualizes Order Flow clusters, Liquidity Pools, Stop Loss clusters,
    and Institutional Buy/Sell Iceberg Walls on Gold (XAUUSD).
    """
    WIDTH = 1000
    HEIGHT = 650

    # Color Palette: Modern Institutional Dark Terminal Style
    BG_COLOR = (13, 17, 23)           # Dark Navy / Charcoal
    PANEL_BG = (22, 27, 34)           # Card Panel
    GRID_COLOR = (33, 38, 45)         # Grid lines
    TEXT_WHITE = (240, 246, 252)
    TEXT_MUTED = (139, 148, 158)
    TEXT_YELLOW = (230, 180, 80)
    
    # Heatmap Density Colors
    HEAT_LOW = (35, 78, 82)           # Teal
    HEAT_MED = (217, 119, 6)          # Amber / Orange
    HEAT_HIGH = (239, 68, 68)         # Neon Red (Liquidity Pool)
    HEAT_MAX = (234, 179, 8)          # Golden Yellow (Whale Cluster)
    
    BUY_WALL_COLOR = (34, 197, 94)    # Emerald Green
    SELL_WALL_COLOR = (239, 68, 68)   # Coral Red
    CURRENT_PRICE_COLOR = (56, 189, 248) # Electric Cyan

    def __init__(self):
        try:
            self.font_title = ImageFont.truetype(str(FONT_BOLD_PATH), 22)
            self.font_header = ImageFont.truetype(str(FONT_BOLD_PATH), 15)
            self.font_body = ImageFont.truetype(str(FONT_PATH), 13)
            self.font_bold = ImageFont.truetype(str(FONT_BOLD_PATH), 13)
            self.font_small = ImageFont.truetype(str(FONT_PATH), 11)
        except Exception as e:
            logger.warning(f"[LiquidityHeatmapBuilder] Fallback to default font: {e}")
            self.font_title = ImageFont.load_default()
            self.font_header = ImageFont.load_default()
            self.font_body = ImageFont.load_default()
            self.font_bold = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    def generate_heatmap_png(self, price_data: dict, order_book: dict = None) -> bytes:
        """
        Draws the HD Liquidity Heatmap canvas and returns PNG bytes.
        """
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), self.BG_COLOR)
        draw = ImageDraw.Draw(img)

        current_price = price_data.get("price_oz", 4365.0)
        levels = price_data.get("key_levels", {})
        pivot = levels.get("pivot", current_price)
        r1 = levels.get("r1", current_price + 20)
        s1 = levels.get("s1", current_price - 20)

        now_kh = datetime.now(CAMBODIA_TZ)
        time_str = now_kh.strftime("%d/%m/%Y - %H:%M")

        # 1. Header Banner
        draw.rectangle([(0, 0), (self.WIDTH, 70)], fill=(18, 24, 38))
        draw.text((30, 16), "SMART MONEY LIQUIDITY HEATMAP", font=self.font_title, fill=self.TEXT_WHITE)
        draw.text((30, 44), f"XAU/USD (Gold) | Institutional Order Flow & Stop Loss Clusters | {time_str} UTC+7", font=self.font_small, fill=self.TEXT_MUTED)

        # Current Price Badge
        badge_text = f"SPOT: ${current_price:,.2f}"
        badge_w = 170
        draw.rounded_rectangle([(self.WIDTH - badge_w - 30, 18), (self.WIDTH - 30, 52)], radius=6, fill=(30, 41, 59), outline=self.CURRENT_PRICE_COLOR, width=1)
        draw.text((self.WIDTH - badge_w - 18, 26), badge_text, font=self.font_header, fill=self.CURRENT_PRICE_COLOR)

        # 2. Main Heatmap Chart Layout (Left: 660px, Right Dashboard: 280px)
        chart_x = 30
        chart_y = 90
        chart_w = 640
        chart_h = 510

        draw.rounded_rectangle([(chart_x, chart_y), (chart_x + chart_w, chart_y + chart_h)], radius=8, fill=self.PANEL_BG, outline=self.GRID_COLOR, width=1)

        # Price scale parameters
        price_min = current_price - 40.0
        price_max = current_price + 40.0
        price_range = price_max - price_min

        # Generate Depth Heat Bars (Levels from +35 to -35)
        # Higher density clusters near Key Zones and Whale Walls
        import math
        num_bars = 28
        bar_step_usd = price_range / num_bars
        bar_h = (chart_h - 40) / num_bars

        # Extract real whale walls if available
        buy_walls = {b["price"]: b["volume_oz"] for b in order_book.get("whale_buy_walls", [])} if order_book else {}
        sell_walls = {s["price"]: s["volume_oz"] for s in order_book.get("whale_sell_walls", [])} if order_book else {}

        for i in range(num_bars):
            lvl_price = price_max - (i * bar_step_usd)
            by = chart_y + 20 + (i * bar_h)

            # Determine Heat Density (Score 0.0 to 1.0)
            # Peaks at Resistance, Support, Pivot and Whale Walls
            dist_curr = abs(lvl_price - current_price)
            dist_r1 = abs(lvl_price - r1)
            dist_s1 = abs(lvl_price - s1)

            # Density calculation
            density = 0.25 + 0.5 * math.exp(-(min(dist_r1, dist_s1)**2) / 60.0)
            if lvl_price > current_price and sell_walls:
                density += 0.2
            elif lvl_price < current_price and buy_walls:
                density += 0.2
            density = min(density, 1.0)

            # Heat Color Gradient
            if density > 0.82:
                bar_col = self.HEAT_MAX
                label_tag = " [LIQUIDITY POOL]"
            elif density > 0.65:
                bar_col = self.HEAT_HIGH
                label_tag = ""
            elif density > 0.45:
                bar_col = self.HEAT_MED
                label_tag = ""
            else:
                bar_col = self.HEAT_LOW
                label_tag = ""

            # Horizontal Heat Depth Bar
            bar_len = int((chart_w - 180) * density)
            draw.rounded_rectangle([(chart_x + 10, by + 2), (chart_x + 10 + bar_len, by + bar_h - 2)], radius=3, fill=bar_col)

            # Price label along the right axis of the chart
            p_str = f"${lvl_price:,.1f}"
            draw.text((chart_x + chart_w - 90, by + 1), p_str, font=self.font_small, fill=self.TEXT_MUTED)

        # 3. Overlay Current Price & Key Reference Lines
        def price_to_y(p):
            ratio = (price_max - p) / price_range
            return chart_y + 20 + (ratio * (chart_h - 40))

        # Current Spot Line
        curr_y = price_to_y(current_price)
        draw.line([(chart_x, curr_y), (chart_x + chart_w, curr_y)], fill=self.CURRENT_PRICE_COLOR, width=2)
        draw.rounded_rectangle([(chart_x + chart_w - 110, curr_y - 10), (chart_x + chart_w - 5, curr_y + 10)], radius=4, fill=(8, 47, 73), outline=self.CURRENT_PRICE_COLOR)
        draw.text((chart_x + chart_w - 102, curr_y - 6), f"SPOT ${current_price:,.2f}", font=self.font_small, fill=self.CURRENT_PRICE_COLOR)

        # Resistance Zone (BSL - Buy Side Liquidity)
        r_y = price_to_y(r1)
        draw.line([(chart_x, r_y), (chart_x + chart_w, r_y)], fill=self.SELL_WALL_COLOR, width=1)
        draw.text((chart_x + 20, r_y - 14), f"🔴 BSL / RESISTANCE (${r1:,.2f}) — Stop Loss Pool", font=self.font_small, fill=self.SELL_WALL_COLOR)

        # Support Zone (SSL - Sell Side Liquidity)
        s_y = price_to_y(s1)
        draw.line([(chart_x, s_y), (chart_x + chart_w, s_y)], fill=self.BUY_WALL_COLOR, width=1)
        draw.text((chart_x + 20, s_y + 3), f"🟢 SSL / SUPPORT (${s1:,.2f}) — Demand Pool", font=self.font_small, fill=self.BUY_WALL_COLOR)

        # 4. Right Side Intelligence Panel (300px)
        info_x = chart_x + chart_w + 20
        info_y = chart_y
        info_w = self.WIDTH - info_x - 30

        # Panel 1: Order Book Volume Summary
        draw.rounded_rectangle([(info_x, info_y), (info_x + info_w, info_y + 160)], radius=8, fill=self.PANEL_BG, outline=self.GRID_COLOR, width=1)
        draw.text((info_x + 16, info_y + 14), "ORDER BOOK DEPTH", font=self.font_bold, fill=self.TEXT_WHITE)
        
        bid_pct = order_book.get("bid_dominance_pct", 50.0) if order_book else 50.0
        ask_pct = order_book.get("ask_dominance_pct", 50.0) if order_book else 50.0
        draw.text((info_x + 16, info_y + 42), f"• Bid (Buy): {bid_pct}%", font=self.font_body, fill=self.BUY_WALL_COLOR)
        draw.text((info_x + 16, info_y + 64), f"• Ask (Sell): {ask_pct}%", font=self.font_body, fill=self.SELL_WALL_COLOR)
        
        # Dual Bar Visual
        b_bar_w = int((info_w - 32) * (bid_pct / 100.0))
        draw.rounded_rectangle([(info_x + 16, info_y + 92), (info_x + 16 + b_bar_w, info_y + 104)], radius=4, fill=self.BUY_WALL_COLOR)
        draw.rounded_rectangle([(info_x + 16 + b_bar_w, info_y + 92), (info_x + info_w - 16, info_y + 104)], radius=4, fill=self.SELL_WALL_COLOR)
        draw.text((info_x + 16, info_y + 118), order_book.get("bias", "Normal")[:32] if order_book else "Balanced Order Flow", font=self.font_small, fill=self.TEXT_MUTED)

        # Panel 2: Smart Money Key Zones (SMC Targets)
        draw.rounded_rectangle([(info_x, info_y + 175), (info_x + info_w, info_y + 365)], radius=8, fill=self.PANEL_BG, outline=self.GRID_COLOR, width=1)
        draw.text((info_x + 16, info_y + 189), "SMC LIQUIDITY POOLS", font=self.font_bold, fill=self.TEXT_WHITE)
        
        draw.text((info_x + 16, info_y + 218), "🔴 Premium Sell Target:", font=self.font_small, fill=self.TEXT_MUTED)
        draw.text((info_x + 16, info_y + 236), f"${r1-2:,.1f} - ${r1+4:,.1f}", font=self.font_bold, fill=self.SELL_WALL_COLOR)

        draw.text((info_x + 16, info_y + 264), "🎯 Equilibrium Pivot:", font=self.font_small, fill=self.TEXT_MUTED)
        draw.text((info_x + 16, info_y + 282), f"${pivot:,.2f}", font=self.font_bold, fill=self.TEXT_YELLOW)

        draw.text((info_x + 16, info_y + 310), "🟢 Discount Buy Target:", font=self.font_small, fill=self.TEXT_MUTED)
        draw.text((info_x + 16, info_y + 328), f"${s1-4:,.1f} - ${s1+2:,.1f}", font=self.font_bold, fill=self.BUY_WALL_COLOR)

        # Panel 3: Heatmap Legend
        draw.rounded_rectangle([(info_x, info_y + 380), (info_x + info_w, info_y + 510)], radius=8, fill=self.PANEL_BG, outline=self.GRID_COLOR, width=1)
        draw.text((info_x + 16, info_y + 394), "HEATMAP LEGEND", font=self.font_bold, fill=self.TEXT_WHITE)

        # Colors legend
        draw.rectangle([(info_x + 16, info_y + 424), (info_x + 32, info_y + 436)], fill=self.HEAT_MAX)
        draw.text((info_x + 40, info_y + 422), "Max Whale Liquidity Pool", font=self.font_small, fill=self.TEXT_WHITE)

        draw.rectangle([(info_x + 16, info_y + 446), (info_x + 32, info_y + 458)], fill=self.HEAT_HIGH)
        draw.text((info_x + 40, info_y + 444), "Heavy Stop Loss Cluster", font=self.font_small, fill=self.TEXT_WHITE)

        draw.rectangle([(info_x + 16, info_y + 468), (info_x + 32, info_y + 480)], fill=self.HEAT_MED)
        draw.text((info_x + 40, info_y + 466), "Moderate Order Flow", font=self.font_small, fill=self.TEXT_WHITE)

        draw.rectangle([(info_x + 16, info_y + 490), (info_x + 32, info_y + 502)], fill=self.HEAT_LOW)
        draw.text((info_x + 40, info_y + 488), "Low Volume Void", font=self.font_small, fill=self.TEXT_WHITE)

        # Output PNG buffer
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        buf.seek(0)
        return buf.getvalue()
