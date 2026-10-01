# -*- coding: utf-8 -*-
"""
Daily Gold Price Graphic Card Builder (Ultra HD HTML5/Canvas).
Renders high-resolution 1080x1080 graphic card featuring:
- 3D Gold Title: "ហាងឆេងមាស" and Subtitle "តម្លៃមាសថ្ងៃនេះ"
- 3 Clean White Rounded Pill Cards:
  1. តម្លឹង:  $X,XXX
  2. ជី:     $XXX
  3. អោន:   $X,XXX
- Dynamic Date/Time Footer: "ថ្ងៃ DD/MM/YYYY   ម៉ោង 07:00 ព្រឹក"
- Authentic Gold Bullion and Glowing Candlesticks Background
"""

import base64
import logging
import os
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import BASE_DIR, CAMBODIA_TZ, DAMLUNG_TO_OZ_RATIO

logger = logging.getLogger(__name__)

class DailyGoldPriceCardBuilder:
    def __init__(self):
        self.edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
        self._bg_b64 = None
        self._load_background()

    def _load_background(self):
        bg_files = [
            BASE_DIR / "gold_bars_raw.jpg",
            BASE_DIR / "gold_fx_photoreal_bars.png",
            BASE_DIR / "xauusd_channel_wallpaper.jpg"
        ]
        for f in bg_files:
            if f.exists():
                try:
                    with open(f, "rb") as bf:
                        self._bg_b64 = base64.b64encode(bf.read()).decode("utf-8")
                        logger.info(f"[DailyGoldPriceCardBuilder] Background loaded from {f.name}")
                        break
                except Exception as e:
                    logger.debug(f"Failed to load background image {f}: {e}")

    def _find_browser(self) -> Optional[str]:
        import shutil
        for cmd in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "msedge"]:
            found = shutil.which(cmd)
            if found:
                return found
        for p in self.edge_paths + [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium"
        ]:
            if os.path.exists(p):
                return p
        return None

    def build_card_png(self, price_data: dict) -> Optional[bytes]:
        """
        Renders an ultra-luxurious 1080x1080 PNG graphic card with dynamic live prices.
        """
        try:
            # 1. Extract and calculate prices
            oz_price = float(price_data.get("price_oz") or 0.0)
            if oz_price <= 0:
                oz_price = 4152.0

            loc = price_data.get("local_market") or {}
            damlung_price = price_data.get("damlung_sell") or loc.get("damlung_sell")
            if not damlung_price:
                damlung_price = price_data.get("price_damlung")
            if not damlung_price:
                damlung_price = oz_price * DAMLUNG_TO_OZ_RATIO
            damlung_price = float(damlung_price)

            chi_price = price_data.get("chi_sell") or loc.get("chi_sell")
            if not chi_price:
                chi_price = damlung_price / 10.0
            chi_price = float(chi_price)

            # Round prices to match clean display
            damlung_str = f"${round(damlung_price):,}"
            chi_str = f"${round(chi_price):,}"
            oz_str = f"${round(oz_price):,}"

            # 2. Extract date
            now_kh = datetime.now(CAMBODIA_TZ)
            date_str = price_data.get("date_str") or now_kh.strftime("%d/%m/%Y")
            footer_str = f"ថ្ងៃ {date_str}   ម៉ោង 07:00 ព្រឹក"

            # 3. Build HTML
            bg_data_url = f"data:image/jpeg;base64,{self._bg_b64}" if self._bg_b64 else ""

            html_content = f"""<!DOCTYPE html>
<html lang="km">
<head>
  <meta charset="UTF-8">
  <title>Daily Gold Price Card</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Kantumruy+Pro:wght@600;700;800&family=Koulen&family=Outfit:wght@700;800;900&display=swap" rel="stylesheet">
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      width: 1080px;
      height: 1080px;
      overflow: hidden;
      background: #080c14;
      font-family: 'Kantumruy Pro', sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
    }}

    .bg-image {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: url('{bg_data_url}') center/cover no-repeat;
      filter: brightness(0.95) contrast(1.18) saturate(1.3);
      z-index: 1;
    }}
    .bg-darkener {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: radial-gradient(circle at center, rgba(10, 14, 24, 0.3) 0%, rgba(4, 6, 10, 0.85) 100%);
      z-index: 2;
    }}

    .main-card {{
      position: relative;
      z-index: 10;
      width: 950px;
      height: 950px;
      background: rgba(12, 17, 26, 0.78);
      border-radius: 56px;
      border: 2px solid rgba(255, 215, 0, 0.6);
      box-shadow: 
        0 40px 100px rgba(0, 0, 0, 0.92),
        0 0 60px rgba(245, 158, 11, 0.28),
        inset 0 1px 2px rgba(255, 255, 255, 0.35);
      backdrop-filter: blur(28px) saturate(180%);
      padding: 50px 50px 60px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 38px;
    }}

    .header-box {{
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
    }}
    .header-title {{
      font-family: 'Koulen', sans-serif;
      font-size: 110px;
      line-height: 1.0;
      letter-spacing: 2px;
      color: #ffd700;
      background: linear-gradient(180deg, #ffffff 0%, #fff2a3 25%, #ffd700 55%, #e6a800 80%, #996300 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      filter: drop-shadow(0 4px 16px rgba(0, 0, 0, 0.95)) drop-shadow(0 0 30px rgba(255, 215, 0, 0.6));
    }}
    .header-datetime-badge {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 8px 36px;
      background: rgba(255, 215, 0, 0.12);
      border: 1.5px solid rgba(255, 215, 0, 0.45);
      border-radius: 30px;
      margin-top: 6px;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.25);
    }}
    .header-datetime-text {{
      color: #ffe082;
      font-family: 'Kantumruy Pro', sans-serif;
      font-size: 32px;
      font-weight: 700;
      letter-spacing: 0.5px;
      text-shadow: 0 2px 6px rgba(0, 0, 0, 0.8);
    }}
    .header-divider {{
      width: 520px;
      height: 4px;
      margin-top: 10px;
      background: linear-gradient(90deg, transparent 0%, #ffd700 50%, transparent 100%);
      border-radius: 2px;
      box-shadow: 0 0 14px rgba(255, 215, 0, 0.85);
    }}

    .pills-container {{
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 26px;
    }}
    .pill-card {{
      width: 100%;
      height: 156px;
      background: linear-gradient(180deg, #ffffff 0%, #f9fafb 100%);
      border-radius: 42px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 55px;
      box-shadow: 
        0 20px 45px rgba(0, 0, 0, 0.5),
        0 4px 10px rgba(0, 0, 0, 0.25),
        inset 0 1px 1px rgba(255, 255, 255, 1);
      border: 2px solid rgba(212, 175, 55, 0.65);
      position: relative;
      overflow: hidden;
    }}
    .pill-card::before {{
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 14px;
      background: linear-gradient(180deg, #ffd700 0%, #b45309 100%);
      box-shadow: 0 0 10px rgba(245, 158, 11, 0.6);
    }}
    .pill-label {{
      font-family: 'Kantumruy Pro', sans-serif;
      font-size: 68px;
      font-weight: 900;
      color: #0f172a;
      letter-spacing: 0.5px;
      display: flex;
      align-items: center;
      gap: 16px;
    }}
    .pill-value {{
      font-family: 'Outfit', sans-serif;
      font-size: 88px;
      font-weight: 900;
      color: #0b132b;
      letter-spacing: -1.5px;
      text-shadow: 0 2px 4px rgba(0, 0, 0, 0.12);
    }}
  </style>
</head>
<body>
  <div class="bg-image"></div>
  <div class="bg-darkener"></div>

  <div class="main-card">
    <div class="header-box">
      <div class="header-title">ហាងឆេងមាស</div>
      <div class="header-datetime-badge">
        <span class="header-datetime-text">{footer_str}</span>
      </div>
      <div class="header-divider"></div>
    </div>

    <div class="pills-container">
      <div class="pill-card">
        <span class="pill-label">1 តម្លឹង</span>
        <span class="pill-value">{damlung_str}</span>
      </div>
      <div class="pill-card">
        <span class="pill-label">1 ជី</span>
        <span class="pill-value">{chi_str}</span>
      </div>
      <div class="pill-card">
        <span class="pill-label">1 អោន</span>
        <span class="pill-value">{oz_str}</span>
      </div>
    </div>
  </div>
</body>
</html>
"""

            # 4. Render with headless browser if available, or fallback to Pillow
            browser_bin = self._find_browser()
            if not browser_bin:
                logger.info("[DailyGoldPriceCardBuilder] Browser not found — using high-performance Pillow 1080x1080 renderer.")
                return self._render_with_pillow(damlung_str, chi_str, oz_str, footer_str)

            with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tf:
                tf.write(html_content)
                temp_html = tf.name

            temp_png = temp_html.replace(".html", ".png")

            try:
                cmd = [
                    browser_bin,
                    "--headless=new",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--hide-scrollbars",
                    "--window-size=1080,1080",
                    f"--screenshot={temp_png}",
                    temp_html
                ]
                subprocess.run(cmd, timeout=15, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                if os.path.exists(temp_png) and os.path.getsize(temp_png) > 1000:
                    with open(temp_png, "rb") as pf:
                        png_bytes = pf.read()
                    logger.info(f"[DailyGoldPriceCardBuilder] Rendered card ({len(png_bytes)} bytes) successfully.")
                    return png_bytes
                else:
                    logger.warning("[DailyGoldPriceCardBuilder] Browser render output empty, falling back to Pillow.")
                    return self._render_with_pillow(damlung_str, chi_str, oz_str, footer_str)
            except Exception as render_err:
                logger.warning(f"[DailyGoldPriceCardBuilder] Browser render failed ({render_err}), using Pillow fallback.")
                return self._render_with_pillow(damlung_str, chi_str, oz_str, footer_str)
            finally:
                if os.path.exists(temp_html):
                    try: os.remove(temp_html)
                    except Exception: pass
                if os.path.exists(temp_png):
                    try: os.remove(temp_png)
                    except Exception: pass

        except Exception as e:
            logger.error(f"[DailyGoldPriceCardBuilder] Exception generating card: {e}")
            return self._render_with_pillow(damlung_str, chi_str, oz_str, footer_str)

    def _render_with_pillow(self, damlung_str: str, chi_str: str, oz_str: str, footer_str: str) -> Optional[bytes]:
        """Pillow-based Ultra-HD 1080x1080 Graphic Card Renderer for Zero-Dependency Linux Cloud environments."""
        try:
            import io
            from PIL import Image, ImageDraw, ImageFont

            bg_path = BASE_DIR / "gold_bars_raw.jpg"
            if bg_path.exists():
                img = Image.open(bg_path).convert("RGBA")
                w, h = img.size
                min_dim = min(w, h)
                left = (w - min_dim) // 2
                top = (h - min_dim) // 2
                img = img.crop((left, top, left + min_dim, top + min_dim))
                img = img.resize((1080, 1080), Image.Resampling.LANCZOS)
            else:
                img = Image.new("RGBA", (1080, 1080), (8, 12, 20, 255))

            # Dark Glassmorphic Card Overlay
            overlay = Image.new("RGBA", (1080, 1080), (0, 0, 0, 0))
            draw_ov = ImageDraw.Draw(overlay)
            draw_ov.rectangle([(0, 0), (1080, 1080)], fill=(8, 12, 20, 185))

            # Glass card in center
            draw_ov.rounded_rectangle([(90, 80), (990, 1000)], radius=36, fill=(15, 23, 42, 220), outline=(212, 175, 55, 140), width=3)
            img = Image.alpha_composite(img, overlay)
            draw = ImageDraw.Draw(img)

            # Fonts
            f_bold = BASE_DIR / "assets" / "DejaVuSans-Bold.ttf"
            if f_bold.exists():
                font_title = ImageFont.truetype(str(f_bold), 56)
                font_date = ImageFont.truetype(str(f_bold), 26)
                font_pill_label = ImageFont.truetype(str(f_bold), 34)
                font_pill_price = ImageFont.truetype(str(f_bold), 42)
            else:
                font_title = ImageFont.load_default()
                font_date = font_title
                font_pill_label = font_title
                font_pill_price = font_title

            # Title & Date
            draw.text((540, 160), "ហាងឆេងមាស", fill=(255, 215, 0), font=font_title, anchor="mm")
            draw.text((540, 235), footer_str, fill=(226, 232, 240), font=font_date, anchor="mm")

            # 3 White Rounded Pill Cards
            pills = [
                ("1 តម្លឹង", damlung_str),
                ("1 ជី", chi_str),
                ("1 អោន", oz_str)
            ]
            start_y = 330
            pill_h = 145
            gap = 45

            for i, (label, val) in enumerate(pills):
                cy = start_y + i * (pill_h + gap)
                cx1, cx2 = 160, 920
                draw.rounded_rectangle([(cx1, cy), (cx2, cy + pill_h)], radius=30, fill=(255, 255, 255, 255), outline=(212, 175, 55, 180), width=2)
                draw.text((cx1 + 60, cy + pill_h // 2), label, fill=(15, 23, 42), font=font_pill_label, anchor="lm")
                draw.text((cx2 - 60, cy + pill_h // 2), val, fill=(180, 83, 9), font=font_pill_price, anchor="rm")

            out = io.BytesIO()
            img.convert("RGB").save(out, format="PNG", quality=95)
            logger.info("[DailyGoldPriceCardBuilder] Rendered 1080x1080 card via Pillow successfully.")
            return out.getvalue()
        except Exception as pe:
            logger.error(f"[DailyGoldPriceCardBuilder] Pillow rendering error: {pe}")
            return None
