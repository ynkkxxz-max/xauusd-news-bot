import io
import logging
import math
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from config import BASE_DIR, CAMBODIA_TZ

logger = logging.getLogger(__name__)

FONT_PATH = BASE_DIR / "assets" / "DejaVuSans.ttf"
FONT_BOLD_PATH = BASE_DIR / "assets" / "DejaVuSans-Bold.ttf"

class LiquidityHeatmapBuilder:
    """
    Renders Institutional Smart Money Liquidity Heatmap Image (Canvas Ultra HD).
    Visualizes Order Flow clusters, Liquidity Pools, Stop Loss clusters,
    and Institutional Buy/Sell Iceberg Walls on Gold (XAUUSD).
    Engineered with pure vector geometry (no missing emoji glyphs) for 100% crisp typography.
    """
    WIDTH = 1120
    HEIGHT = 700

    # Color Palette: Modern Institutional Dark Terminal Style
    BG_COLOR = (11, 15, 25)            # Deep Space Navy
    HEADER_BG = (17, 24, 39)          # Header Panel
    PANEL_BG = (19, 26, 42)           # Card Panel
    PANEL_BORDER = (37, 47, 69)       # Panel Border
    GRID_COLOR = (30, 41, 59)         # Grid lines
    
    TEXT_WHITE = (248, 250, 252)
    TEXT_MUTED = (148, 163, 184)
    TEXT_DIM = (100, 116, 139)
    TEXT_YELLOW = (250, 204, 21)
    
    # Heatmap Density Colors
    HEAT_LOW = (20, 60, 75)           # Deep Cyan/Teal (Low Void)
    HEAT_MED = (217, 119, 6)          # Amber / Orange (Moderate)
    HEAT_HIGH = (239, 68, 68)         # Vivid Red (Heavy Liquidity / Stop Loss)
    HEAT_MAX = (245, 158, 11)         # Golden Amber (Whale Liquidity Pool)
    
    BUY_WALL_COLOR = (34, 197, 94)    # Emerald Green
    SELL_WALL_COLOR = (244, 63, 94)   # Rose Red
    CURRENT_PRICE_COLOR = (56, 189, 248) # Electric Cyan

    def __init__(self):
        try:
            self.font_title = ImageFont.truetype(str(FONT_BOLD_PATH), 22)
            self.font_header = ImageFont.truetype(str(FONT_BOLD_PATH), 15)
            self.font_body = ImageFont.truetype(str(FONT_PATH), 13)
            self.font_bold = ImageFont.truetype(str(FONT_BOLD_PATH), 13)
            self.font_small = ImageFont.truetype(str(FONT_PATH), 11)
            self.font_tiny = ImageFont.truetype(str(FONT_BOLD_PATH), 10)
        except Exception as e:
            logger.warning(f"[LiquidityHeatmapBuilder] Fallback to default font: {e}")
            self.font_title = ImageFont.load_default()
            self.font_header = ImageFont.load_default()
            self.font_body = ImageFont.load_default()
            self.font_bold = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_tiny = ImageFont.load_default()

    def generate_heatmap_png(self, price_data: dict, order_book: dict = None) -> bytes:
        """
        Draws the Ultra-HD Liquidity Heatmap canvas and returns PNG bytes.
        """
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), self.BG_COLOR)
        draw = ImageDraw.Draw(img)

        current_price = price_data.get("price_oz", 4140.0)
        levels = price_data.get("key_levels", {})
        pivot = levels.get("pivot", current_price)
        r1 = levels.get("r1", current_price + 20.0)
        s1 = levels.get("s1", current_price - 20.0)

        now_kh = datetime.now(CAMBODIA_TZ)
        time_str = now_kh.strftime("%d/%m/%Y - %H:%M")

        # ── 1. Top Header Banner ─────────────────────────────────────────────
        draw.rectangle([(0, 0), (self.WIDTH, 75)], fill=self.HEADER_BG)
        draw.line([(0, 75), (self.WIDTH, 75)], fill=self.PANEL_BORDER, width=1)
        
        # Indicator Dot
        draw.ellipse([(32, 28), (42, 38)], fill=self.CURRENT_PRICE_COLOR)
        draw.text((50, 18), "SMART MONEY LIQUIDITY HEATMAP", font=self.font_title, fill=self.TEXT_WHITE)
        draw.text((50, 46), f"XAU/USD (Gold) | Institutional Order Flow & Stop Loss Clusters | {time_str} UTC+7", font=self.font_small, fill=self.TEXT_MUTED)

        # Top-Right Current Spot Price Badge
        badge_text = f"SPOT: ${current_price:,.2f}"
        badge_w = 180
        badge_h = 40
        badge_x = self.WIDTH - badge_w - 32
        badge_y = 18
        draw.rounded_rectangle([(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)], radius=6, fill=(15, 23, 42), outline=self.CURRENT_PRICE_COLOR, width=2)
        # Spot dot inside badge
        draw.ellipse([(badge_x + 14, badge_y + 15), (badge_x + 22, badge_y + 23)], fill=self.CURRENT_PRICE_COLOR)
        draw.text((badge_x + 30, badge_y + 10), badge_text, font=self.font_header, fill=self.CURRENT_PRICE_COLOR)

        # ── 2. Main Heatmap Chart Layout (Left: 730px, Right Dashboard: 320px) ─
        chart_x = 32
        chart_y = 92
        chart_w = 720
        chart_h = 580

        draw.rounded_rectangle([(chart_x, chart_y), (chart_x + chart_w, chart_y + chart_h)], radius=10, fill=self.PANEL_BG, outline=self.PANEL_BORDER, width=1)

        # Price scale parameters
        price_min = current_price - 40.0
        price_max = current_price + 40.0
        price_range = price_max - price_min

        # Right Axis price column inside chart
        axis_w = 90
        axis_x = chart_x + chart_w - axis_w
        draw.line([(axis_x, chart_y), (axis_x, chart_y + chart_h)], fill=self.GRID_COLOR, width=1)
        draw.rectangle([(axis_x, chart_y + 1), (chart_x + chart_w - 1, chart_y + chart_h - 1)], fill=(15, 20, 32))

        # Generate Depth Heat Bars
        num_bars = 28
        bar_step_usd = price_range / num_bars
        bar_h = (chart_h - 30) / num_bars
        max_bar_width = chart_w - axis_w - 24

        # Extract whale walls
        buy_walls = {b["price"]: b["volume_oz"] for b in order_book.get("whale_buy_walls", [])} if order_book else {}
        sell_walls = {s["price"]: s["volume_oz"] for s in order_book.get("whale_sell_walls", [])} if order_book else {}

        for i in range(num_bars):
            lvl_price = price_max - (i * bar_step_usd)
            by = chart_y + 15 + (i * bar_h)

            # Density Calculation
            dist_curr = abs(lvl_price - current_price)
            dist_r1 = abs(lvl_price - r1)
            dist_s1 = abs(lvl_price - s1)

            density = 0.25 + 0.52 * math.exp(-(min(dist_r1, dist_s1)**2) / 55.0)
            if lvl_price > current_price and sell_walls:
                density += 0.18
            elif lvl_price < current_price and buy_walls:
                density += 0.18
            density = max(0.15, min(density, 1.0))

            # Heat Color Selection
            if density > 0.82:
                bar_col = self.HEAT_MAX
            elif density > 0.64:
                bar_col = self.HEAT_HIGH
            elif density > 0.44:
                bar_col = self.HEAT_MED
            else:
                bar_col = self.HEAT_LOW

            # Draw Depth Bar
            bar_len = int(max_bar_width * density)
            draw.rounded_rectangle([(chart_x + 12, by + 2), (chart_x + 12 + bar_len, by + bar_h - 2)], radius=3, fill=bar_col)

            # Draw Price Tag on the Right Axis
            p_str = f"${lvl_price:,.1f}"
            draw.text((axis_x + 14, by + 1), p_str, font=self.font_small, fill=self.TEXT_DIM)

        # Coordinate helper
        def price_to_y(p):
            ratio = (price_max - p) / price_range
            return chart_y + 15 + (ratio * (chart_h - 30))

        # ── 3. Reference Lines & Labels (BSL, SSL, SPOT) ──────────────────────
        # Resistance Zone (BSL - Buy Side Liquidity)
        r_y = max(chart_y + 20, min(chart_y + chart_h - 20, price_to_y(r1)))
        draw.line([(chart_x, r_y), (axis_x, r_y)], fill=self.SELL_WALL_COLOR, width=2)
        # Background badge pill
        bsl_label = f"BSL / RESISTANCE (${r1:,.2f}) — Stop Loss Pool"
        bsl_badge_w = 345
        draw.rounded_rectangle([(chart_x + 14, r_y - 20), (chart_x + 14 + bsl_badge_w, r_y - 2)], radius=4, fill=(15, 23, 42), outline=self.SELL_WALL_COLOR, width=1)
        # Red vector dot
        draw.ellipse([(chart_x + 22, r_y - 14), (chart_x + 30, r_y - 6)], fill=self.SELL_WALL_COLOR)
        draw.text((chart_x + 36, r_y - 17), bsl_label, font=self.font_small, fill=self.SELL_WALL_COLOR)

        # Support Zone (SSL - Sell Side Liquidity)
        s_y = max(chart_y + 20, min(chart_y + chart_h - 20, price_to_y(s1)))
        draw.line([(chart_x, s_y), (axis_x, s_y)], fill=self.BUY_WALL_COLOR, width=2)
        # Background badge pill
        ssl_label = f"SSL / SUPPORT (${s1:,.2f}) — Demand Pool"
        ssl_badge_w = 320
        draw.rounded_rectangle([(chart_x + 14, s_y + 2), (chart_x + 14 + ssl_badge_w, s_y + 20)], radius=4, fill=(15, 23, 42), outline=self.BUY_WALL_COLOR, width=1)
        # Green vector dot
        draw.ellipse([(chart_x + 22, s_y + 7), (chart_x + 30, s_y + 15)], fill=self.BUY_WALL_COLOR)
        draw.text((chart_x + 36, s_y + 4), ssl_label, font=self.font_small, fill=self.BUY_WALL_COLOR)

        # Spot Price Line
        curr_y = max(chart_y + 20, min(chart_y + chart_h - 20, price_to_y(current_price)))
        draw.line([(chart_x, curr_y), (axis_x, curr_y)], fill=self.CURRENT_PRICE_COLOR, width=2)
        # Spot Price Badge (Positioned inside the chart before axis, avoiding collision)
        spot_tag = f"SPOT ${current_price:,.2f}"
        spot_w = 125
        draw.rounded_rectangle([(axis_x - spot_w - 6, curr_y - 11), (axis_x - 6, curr_y + 11)], radius=4, fill=(8, 47, 73), outline=self.CURRENT_PRICE_COLOR, width=1)
        draw.ellipse([(axis_x - spot_w + 4, curr_y - 4), (axis_x - spot_w + 12, curr_y + 4)], fill=self.CURRENT_PRICE_COLOR)
        draw.text((axis_x - spot_w + 18, curr_y - 7), spot_tag, font=self.font_small, fill=self.CURRENT_PRICE_COLOR)

        # ── 4. Right Side Intelligence Panel (320px) ─────────────────────────
        info_x = chart_x + chart_w + 20
        info_y = chart_y
        info_w = self.WIDTH - info_x - 32

        # ── Panel 1: Order Book Volume Summary ──
        p1_h = 165
        draw.rounded_rectangle([(info_x, info_y), (info_x + info_w, info_y + p1_h)], radius=10, fill=self.PANEL_BG, outline=self.PANEL_BORDER, width=1)
        # Header with indicator
        draw.ellipse([(info_x + 18, info_y + 18), (info_x + 26, info_y + 26)], fill=self.CURRENT_PRICE_COLOR)
        draw.text((info_x + 32, info_y + 14), "ORDER BOOK DEPTH", font=self.font_header, fill=self.TEXT_WHITE)
        
        bid_pct = order_book.get("bid_dominance_pct", 50.0) if order_book else 50.0
        ask_pct = order_book.get("ask_dominance_pct", 50.0) if order_book else 50.0
        
        # Bid dot & Ask dot
        draw.ellipse([(info_x + 18, info_y + 48), (info_x + 26, info_y + 56)], fill=self.BUY_WALL_COLOR)
        draw.text((info_x + 32, info_y + 44), f"Bid (Buy): {bid_pct:.1f}%", font=self.font_body, fill=self.BUY_WALL_COLOR)
        
        draw.ellipse([(info_x + 18, info_y + 72), (info_x + 26, info_y + 80)], fill=self.SELL_WALL_COLOR)
        draw.text((info_x + 32, info_y + 68), f"Ask (Sell): {ask_pct:.1f}%", font=self.font_body, fill=self.SELL_WALL_COLOR)
        
        # Dual Bar Volume Bar
        bar_box_w = info_w - 36
        b_bar_w = int(bar_box_w * (bid_pct / 100.0))
        draw.rounded_rectangle([(info_x + 18, info_y + 98), (info_x + 18 + b_bar_w, info_y + 112)], radius=4, fill=self.BUY_WALL_COLOR)
        draw.rounded_rectangle([(info_x + 18 + b_bar_w, info_y + 98), (info_x + 18 + bar_box_w, info_y + 112)], radius=4, fill=self.SELL_WALL_COLOR)
        
        # Determine clean status without emojis or non-latin glyphs to prevent broken boxes
        if bid_pct >= 58.0:
            status_text = "Strong Buy Pressure"
            status_col = self.BUY_WALL_COLOR
        elif ask_pct >= 58.0:
            status_text = "Strong Sell Pressure"
            status_col = self.SELL_WALL_COLOR
        else:
            status_text = "Balanced Order Flow"
            status_col = self.TEXT_MUTED

        draw.text((info_x + 18, info_y + 128), f"Status: {status_text}", font=self.font_small, fill=status_col)

        # ── Panel 2: Smart Money Key Zones (SMC Targets) ──
        p2_y = info_y + p1_h + 16
        p2_h = 205
        draw.rounded_rectangle([(info_x, p2_y), (info_x + info_w, p2_y + p2_h)], radius=10, fill=self.PANEL_BG, outline=self.PANEL_BORDER, width=1)
        
        draw.ellipse([(info_x + 18, p2_y + 18), (info_x + 26, p2_y + 26)], fill=self.TEXT_YELLOW)
        draw.text((info_x + 32, p2_y + 14), "SMC LIQUIDITY POOLS", font=self.font_header, fill=self.TEXT_WHITE)
        
        # 1. Premium Sell Target
        draw.ellipse([(info_x + 18, p2_y + 50), (info_x + 26, p2_y + 58)], fill=self.SELL_WALL_COLOR)
        draw.text((info_x + 32, p2_y + 46), "Premium Sell Target:", font=self.font_small, fill=self.TEXT_MUTED)
        draw.text((info_x + 32, p2_y + 64), f"${r1-2:,.1f} - ${r1+4:,.1f}", font=self.font_bold, fill=self.SELL_WALL_COLOR)

        # 2. Equilibrium Pivot
        draw.ellipse([(info_x + 18, p2_y + 96), (info_x + 26, p2_y + 104)], fill=self.TEXT_YELLOW)
        draw.text((info_x + 32, p2_y + 92), "Equilibrium Pivot:", font=self.font_small, fill=self.TEXT_MUTED)
        draw.text((info_x + 32, p2_y + 110), f"${pivot:,.2f}", font=self.font_bold, fill=self.TEXT_YELLOW)

        # 3. Discount Buy Target
        draw.ellipse([(info_x + 18, p2_y + 142), (info_x + 26, p2_y + 150)], fill=self.BUY_WALL_COLOR)
        draw.text((info_x + 32, p2_y + 138), "Discount Buy Target:", font=self.font_small, fill=self.TEXT_MUTED)
        draw.text((info_x + 32, p2_y + 156), f"${s1-4:,.1f} - ${s1+2:,.1f}", font=self.font_bold, fill=self.BUY_WALL_COLOR)

        # ── Panel 3: Heatmap Legend ──
        p3_y = p2_y + p2_h + 16
        p3_h = chart_h - (p1_h + 16 + p2_h + 16)
        draw.rounded_rectangle([(info_x, p3_y), (info_x + info_w, p3_y + p3_h)], radius=10, fill=self.PANEL_BG, outline=self.PANEL_BORDER, width=1)
        
        draw.ellipse([(info_x + 18, p3_y + 18), (info_x + 26, p3_y + 26)], fill=self.TEXT_WHITE)
        draw.text((info_x + 32, p3_y + 14), "HEATMAP LEGEND", font=self.font_header, fill=self.TEXT_WHITE)

        # 4 Legend Items
        legends = [
            (self.HEAT_MAX, "Max Whale Liquidity Pool"),
            (self.HEAT_HIGH, "Heavy Stop Loss Cluster"),
            (self.HEAT_MED, "Moderate Order Flow"),
            (self.HEAT_LOW, "Low Volume Void")
        ]
        leg_start_y = p3_y + 44
        leg_spacing = 26
        for idx, (col, lbl) in enumerate(legends):
            ly = leg_start_y + (idx * leg_spacing)
            draw.rounded_rectangle([(info_x + 18, ly + 1), (info_x + 34, ly + 15)], radius=3, fill=col)
            draw.text((info_x + 42, ly), lbl, font=self.font_small, fill=self.TEXT_WHITE)

        # Output PNG buffer
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        buf.seek(0)
        return buf.getvalue()
