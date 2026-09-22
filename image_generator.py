import io
import logging

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class ForexFactoryImageGenerator:
    @staticmethod
    def is_available() -> bool:
        return PIL_AVAILABLE

    @staticmethod
    def generate_snapshot_card(currencies: dict, today_events: list, gold_price: float):
        """
        Generates a sleek ForexFactory-styled dark theme graphic card.
        Returns bytes if Pillow is available, else None.
        """
        if not PIL_AVAILABLE:
            return None

        try:
            width = 800
            height = 480
            bg_color = (20, 26, 36) # Dark navy ForexFactory theme
            card_bg = (30, 41, 59)
            text_white = (255, 255, 255)
            text_gray = (156, 163, 175)
            color_green = (34, 197, 94)
            color_red = (239, 68, 68)
            color_gold = (234, 179, 8)

            img = Image.new("RGB", (width, height), color=bg_color)
            draw = ImageDraw.Draw(img)

            # Header banner
            draw.rectangle([(0, 0), (width, 50)], fill=(15, 23, 42))
            draw.text((20, 15), "FOREX FACTORY  |  XAUUSD MARKET SNAPSHOT", fill=color_gold)

            # Majors Currency boxes
            cur_keys = list(currencies.keys())[:4]
            box_width = 175
            for i, pair in enumerate(cur_keys):
                x = 20 + i * (box_width + 15)
                y = 70
                draw.rectangle([(x, y), (x + box_width, y + 90)], fill=card_bg)
                draw.text((x + 15, y + 10), pair, fill=text_white)
                
                data = currencies[pair]
                price = str(data.get("price", "N/A"))
                pct = data.get("change_pct", 0.0)
                color = color_green if pct >= 0 else color_red
                sign = "+" if pct >= 0 else ""

                draw.text((x + 15, y + 38), price, fill=text_white)
                draw.text((x + 15, y + 62), f"{sign}{pct:.2f}%", fill=color)

            # Gold Spot Banner
            draw.rectangle([(20, 180), (width - 20, 235)], fill=(39, 39, 42))
            draw.text((35, 195), "🥇 SPOT GOLD (XAU/USD):", fill=color_gold)
            draw.text((260, 193), f"${gold_price:,.2f}", fill=(255, 255, 255))

            # Calendar Section Header
            draw.text((20, 255), "📅 TODAY'S ECONOMIC HIGHLIGHTS (ForexFactory):", fill=text_white)

            # Draw up to 4 events
            y_pos = 285
            events_to_show = today_events[:4] if today_events else []
            if not events_to_show:
                draw.text((35, y_pos), "No high-impact events scheduled for the rest of today.", fill=text_gray)
            else:
                for ev in events_to_show:
                    title = ev.get("title", "")[:42]
                    country = ev.get("country", "USD")
                    time_kh = ev.get("time_kh", "")
                    actual = ev.get("actual") or "Pending"
                    impact = ev.get("impact", "")

                    impact_color = color_red if impact == "High" else (249, 115, 22)
                    draw.rectangle([(20, y_pos), (width - 20, y_pos + 38)], fill=card_bg)
                    
                    # Impact indicator dot
                    draw.ellipse([(35, y_pos + 12), (45, y_pos + 22)], fill=impact_color)
                    draw.text((55, y_pos + 10), f"[{country}] {title}", fill=text_white)
                    draw.text((520, y_pos + 10), f"Time: {time_kh}", fill=text_gray)
                    draw.text((680, y_pos + 10), f"Act: {actual}", fill=color_gold if actual != "Pending" else text_gray)

                    y_pos += 45

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        except Exception as e:
            logger.warning(f"[ForexFactoryImageGenerator] Failed rendering image card: {e}")
            return None
