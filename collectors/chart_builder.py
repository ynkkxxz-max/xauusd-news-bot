import io
import logging
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # headless backend — required on Render/servers with no display
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import requests

from config import CAMBODIA_TZ

logger = logging.getLogger(__name__)


class GoldChartBuilder:
    """Builds a clean XAUUSD price-line chart PNG from real market data.

    Data source: Yahoo Finance GC=F (COMEX gold futures), the same benchmark
    the price collector already trusts. Renders headlessly and returns PNG
    bytes ready to upload to Telegram via sendPhoto.
    """

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    def _fetch_history(self, range_str: str = "3mo") -> tuple:
        """Returns (dates, closes) lists from Yahoo Finance chart API."""
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1d&range={range_str}"
        resp = requests.get(url, headers=self.headers, timeout=12)
        resp.raise_for_status()
        result = resp.json()["chart"]["result"][0]
        ts = result.get("timestamp", [])
        closes = result["indicators"]["quote"][0].get("close", [])
        dates, prices = [], []
        for t, c in zip(ts, closes):
            if c is None:
                continue
            dates.append(datetime.fromtimestamp(t, CAMBODIA_TZ))
            prices.append(float(c))
        return dates, prices

    def build_chart_png(self, price_data: dict, range_str: str = "3mo") -> bytes:
        """Renders the chart and returns PNG bytes. Returns None on failure.

        price_data: the dict from GoldPriceCollector.fetch_price() so the chart
        header matches the text message (latest price + daily change).
        """
        try:
            dates, closes = self._fetch_history(range_str)
        except Exception as e:
            logger.warning(f"[GoldChartBuilder] history fetch failed: {e}")
            return None

        if len(closes) < 2:
            logger.warning("[GoldChartBuilder] not enough history to plot")
            return None

        # Prefer the live collector price for the headline number; fall back to last close.
        latest = price_data.get("price_oz") or closes[-1]
        change = price_data.get("change", 0.0)
        change_pct = price_data.get("change_pct", 0.0)
        up = change >= 0
        line_color = "#16a34a" if up else "#dc2626"
        arrow = "▲" if up else "▼"

        fig, ax = plt.subplots(figsize=(10, 5.6), dpi=130)
        fig.patch.set_facecolor("#0e1117")
        ax.set_facecolor("#0e1117")

        ax.plot(dates, closes, color=line_color, linewidth=2.0, zorder=3)
        ax.fill_between(dates, closes, min(closes), color=line_color, alpha=0.12, zorder=2)

        # Mark the latest point
        ax.scatter([dates[-1]], [closes[-1]], color=line_color, s=45, zorder=4,
                   edgecolors="white", linewidths=1.2)

        ax.set_title(
            f"XAUUSD / Gold  —  ${latest:,.2f}  {arrow} {change:+,.2f} ({change_pct:+.2f}%)",
            color="white", fontsize=15, fontweight="bold", pad=16, loc="left",
        )
        ax.set_ylabel("USD / Troy Ounce", color="#9ca3af", fontsize=10)

        # Styling: dark grid, muted ticks
        ax.grid(True, color="#2a2f3a", linewidth=0.6, alpha=0.7, zorder=1)
        for spine in ax.spines.values():
            spine.set_color("#2a2f3a")
        ax.tick_params(colors="#9ca3af", labelsize=9)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate(rotation=0, ha="center")

        now_kh = datetime.now(CAMBODIA_TZ)
        ax.text(
            0.995, 0.02,
            f"3-Month Trend  •  Updated {now_kh.strftime('%d/%m/%Y %H:%M')} (Cambodia, UTC+7)",
            transform=ax.transAxes, ha="right", va="bottom",
            color="#6b7280", fontsize=8,
        )

        fig.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        logger.info(f"[GoldChartBuilder] chart rendered ({len(buf.getvalue())} bytes)")
        return buf.getvalue()
