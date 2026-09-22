import io
import logging
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from config import BASE_DIR, CAMBODIA_TZ

logger = logging.getLogger(__name__)

FONT_PATH = BASE_DIR / "assets" / "DejaVuSans.ttf"
FONT_BOLD_PATH = BASE_DIR / "assets" / "DejaVuSans-Bold.ttf"

HEADER_BG = (30, 58, 92)
COL_HEADER_BG = (232, 238, 245)
DAY_BG = (214, 226, 239)
ROW_BG = (255, 255, 255)
ROW_ALT_BG = (244, 247, 250)
SOON_BG = (252, 235, 235)
GRID = (214, 220, 228)
TEXT = (32, 36, 42)
MUTED = (125, 133, 143)
WHITE = (255, 255, 255)

IMPACT_COLORS = {
    "HIGH": (214, 48, 48),
    "MEDIUM": (230, 126, 34),
    "LOW": (241, 196, 15),
}
DEFAULT_IMPACT = (149, 149, 149)

# (label, width, align)
COLS = [
    ("TIME", 92, "left"),
    ("CUR", 64, "left"),
    ("", 44, "left"),
    ("EVENT", 520, "left"),
    ("ACTUAL", 104, "right"),
    ("FORECAST", 104, "right"),
    ("PREVIOUS", 104, "right"),
]
WIDTH = sum(c[1] for c in COLS)
TITLE_H = 52
COL_HEADER_H = 34
DAY_ROW_H = 30
ROW_H = 34
FOOTER_H = 36
PAD_X = 10


class CalendarImageBuilder:
    """Renders a ForexFactory-style daily calendar table as a PNG image.

    Draws only from data the bot already collects, so no scraping or
    third-party screenshot service is involved.
    """

    def __init__(self):
        try:
            self.font = ImageFont.truetype(str(FONT_PATH), 15)
            self.font_bold = ImageFont.truetype(str(FONT_BOLD_PATH), 15)
            self.font_small = ImageFont.truetype(str(FONT_PATH), 12)
            self.font_title = ImageFont.truetype(str(FONT_BOLD_PATH), 19)
        except OSError as e:
            logger.error(f"[CalendarImageBuilder] fonts unavailable: {e}")
            self.font = None

    def build_day_png(self, events: list, day: datetime = None) -> bytes:
        """Returns PNG bytes for one Cambodia-time day, or None if nothing to draw."""
        if self.font is None or not events:
            return None

        day = day or datetime.now(CAMBODIA_TZ)
        now = datetime.now(CAMBODIA_TZ)
        ordered = sorted(events, key=lambda ev: ev["release_dt"])

        groups = []
        for ev in ordered:
            label = ev["release_dt"].strftime("%a %d %b %Y")
            if not groups or groups[-1][0] != label:
                groups.append((label, []))
            groups[-1][1].append(ev)

        body_rows = sum(len(evs) for _, evs in groups)
        height = (
            TITLE_H + COL_HEADER_H + len(groups) * DAY_ROW_H
            + body_rows * ROW_H + FOOTER_H
        )

        img = Image.new("RGB", (WIDTH, height), WHITE)
        draw = ImageDraw.Draw(img)

        # Title bar
        draw.rectangle([0, 0, WIDTH, TITLE_H], fill=HEADER_BG)
        draw.text(
            (14, (TITLE_H - 24) // 2),
            f"ECONOMIC CALENDAR — {day.strftime('%a %d %b %Y')}",
            font=self.font_title, fill=WHITE,
        )
        right = f"{len(ordered)} events"
        rw = draw.textlength(right, font=self.font_small)
        draw.text((WIDTH - rw - 14, (TITLE_H - 16) // 2), right, font=self.font_small, fill=WHITE)

        # Column header
        y = TITLE_H
        draw.rectangle([0, y, WIDTH, y + COL_HEADER_H], fill=COL_HEADER_BG)
        x = 0
        for label, w, _ in COLS:
            if label:
                draw.text((x + PAD_X, y + 9), label, font=self.font_bold, fill=TEXT)
            x += w
        y += COL_HEADER_H

        # Body
        alt = False
        for label, evs in groups:
            draw.rectangle([0, y, WIDTH, y + DAY_ROW_H], fill=DAY_BG)
            draw.text((PAD_X, y + 6), label, font=self.font_bold, fill=TEXT)
            y += DAY_ROW_H
            for ev in evs:
                soon = abs((ev["release_dt"] - now).total_seconds()) <= 1800
                bg = SOON_BG if soon else (ROW_ALT_BG if alt else ROW_BG)
                draw.rectangle([0, y, WIDTH, y + ROW_H], fill=bg)
                self._draw_event_row(draw, ev, y)
                alt = not alt
                y += ROW_H
            draw.line([0, y - 1, WIDTH, y - 1], fill=GRID)

        # Vertical grid lines over the body
        body_top = TITLE_H + COL_HEADER_H
        x = 0
        for _, w, _ in COLS[:-1]:
            x += w
            draw.line([x, body_top, x, y], fill=GRID)
        draw.rectangle([0, body_top, WIDTH - 1, y - 1], outline=GRID)

        # Footer legend
        fy = height - FOOTER_H
        draw.rectangle([0, fy, WIDTH, height], fill=COL_HEADER_BG)
        lx = PAD_X
        for name in ("HIGH", "MEDIUM", "LOW"):
            draw.rectangle([lx, fy + 12, lx + 14, fy + 26], fill=IMPACT_COLORS[name])
            draw.text((lx + 20, fy + 11), name, font=self.font_small, fill=TEXT)
            lx += 20 + draw.textlength(name, font=self.font_small) + 26
        note = "All times Cambodia (UTC+7) — rows in pink start within 30 min"
        nw = draw.textlength(note, font=self.font_small)
        draw.text((WIDTH - nw - 14, fy + 11), note, font=self.font_small, fill=MUTED)

        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    def _draw_event_row(self, draw: ImageDraw.ImageDraw, ev: dict, y: int):
        cy = y + ROW_H // 2
        x = 0
        values = [
            ev.get("release_time_str", ""),
            ev.get("currency", ""),
            None,
            ev.get("title", ""),
            ev.get("actual", ""),
            ev.get("forecast", ""),
            ev.get("previous", ""),
        ]
        for (label, w, align), val in zip(COLS, values):
            if val is None:
                color = IMPACT_COLORS.get(ev.get("impact", ""), DEFAULT_IMPACT)
                draw.rectangle([x + 14, cy - 7, x + 28, cy + 7], fill=color)
            elif val != "":
                font = self.font_bold if align == "left" and label == "TIME" else self.font
                max_w = w - 2 * PAD_X
                text = self._truncate(draw, val, font, max_w)
                tw = draw.textlength(text, font=font)
                tx = x + PAD_X if align == "left" else x + w - PAD_X - tw
                draw.text((tx, cy - 9), text, font=font, fill=TEXT)
            x += w
        draw.line([0, y + ROW_H - 1, WIDTH, y + ROW_H - 1], fill=GRID)

    @staticmethod
    def _truncate(draw: ImageDraw.ImageDraw, text: str, font, max_w: float) -> str:
        if draw.textlength(text, font=font) <= max_w:
            return text
        while len(text) > 1 and draw.textlength(text + "...", font=font) > max_w:
            text = text[:-1]
        return text + "..."
