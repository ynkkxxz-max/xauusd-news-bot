import io
import logging
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as patches
import numpy as np

from config import CAMBODIA_TZ

logger = logging.getLogger(__name__)

class CandlestickChartRenderer:
    """
    Renders institutional TradingView-style dark theme Japanese Candlestick charts (HD)
    annotated with SMC structures: Order Blocks, Liquidity Sweeps, Pivots, and Buy/Sell Targets.
    """

    # Institutional Palette
    BG_DARK = "#0d1117"        # Dark Navy Slate
    PANEL_DARK = "#161b22"     # Surface
    GRID_DARK = "#21262d"      # Subtle grid
    BULL_GREEN = "#26a69a"     # TradingView Bull Green
    BEAR_RED = "#ef5350"       # TradingView Bear Red
    TEXT_WHITE = "#f0f6fc"
    TEXT_MUTED = "#8b949e"
    ACCENT_CYAN = "#38bdf8"
    GOLD_COLOR = "#f59e0b"

    def render_candlestick_chart(
        self,
        candles: list,
        current_price: float,
        key_levels: dict = None,
        setup: dict = None,
        timeframe: str = "M15",
        title_extra: str = ""
    ) -> bytes:
        """
        Renders a high-resolution dark-themed Japanese Candlestick chart and returns PNG bytes.
        candles: list of dicts with 'open', 'high', 'low', 'close', and optional 'ts'.
        """
        if not candles or len(candles) < 5:
            logger.warning("[CandlestickChartRenderer] Insufficient candle data.")
            return None

        # Take the most recent 35-45 candles for clean spacing
        plot_candles = candles[-42:]
        n = len(plot_candles)

        # Setup figure
        fig, (ax, ax_vol) = plt.subplots(
            2, 1, figsize=(12, 7.2), dpi=130,
            gridspec_kw={"height_ratios": [5.2, 1.2]},
            facecolor=self.BG_DARK
        )

        ax.set_facecolor(self.PANEL_DARK)
        ax_vol.set_facecolor(self.PANEL_DARK)

        # Remove outer spines
        for spine in ["top", "left", "right", "bottom"]:
            ax.spines[spine].set_color(self.GRID_DARK)
            ax_vol.spines[spine].set_color(self.GRID_DARK)

        # Plot candles
        width = 0.65
        width_wick = 0.12

        highs = [c["high"] for c in plot_candles]
        lows = [c["low"] for c in plot_candles]
        min_p = min(lows)
        max_p = max(highs)
        p_margin = (max_p - min_p) * 0.15 or 5.0
        ax.set_ylim(min_p - p_margin, max_p + p_margin)
        ax.set_xlim(-1, n + 4)
        ax_vol.set_xlim(-1, n + 4)

        for i, c in enumerate(plot_candles):
            o, h, l, cl = c["open"], c["high"], c["low"], c["close"]
            is_bull = cl >= o
            c_color = self.BULL_GREEN if is_bull else self.BEAR_RED

            # Wick
            ax.plot([i, i], [l, h], color=c_color, linewidth=1.4, zorder=2)

            # Body
            b_low = min(o, cl)
            b_high = max(o, cl)
            body_h = max(b_high - b_low, 0.10)
            rect = patches.Rectangle(
                (i - width / 2.0, b_low), width, body_h,
                facecolor=c_color, edgecolor=c_color, zorder=3
            )
            ax.add_patch(rect)

            # Synthetic volume bar below
            vol_val = abs(cl - o) * 1.5 + (h - l) * 0.8
            vol_rect = patches.Rectangle(
                (i - width / 2.0, 0), width, vol_val,
                facecolor=c_color, alpha=0.65, zorder=3
            )
            ax_vol.add_patch(vol_rect)

        # Overlay Key SMC Levels if provided
        levels = key_levels or {}
        pivot = levels.get("pivot")
        r1 = levels.get("r1")
        s1 = levels.get("s1")

        if r1:
            ax.axhline(r1, color=self.BEAR_RED, linestyle="--", linewidth=1.1, alpha=0.8, zorder=4)
            ax.text(n - 1, r1 + 0.6, f" [BSL/RES] ${r1:,.2f}", color=self.BEAR_RED, fontsize=9, fontweight="bold", zorder=5)

        if pivot:
            ax.axhline(pivot, color=self.GOLD_COLOR, linestyle=":", linewidth=1.1, alpha=0.8, zorder=4)
            ax.text(n - 1, pivot + 0.6, f" [PIVOT] ${pivot:,.2f}", color=self.GOLD_COLOR, fontsize=9, fontweight="bold", zorder=5)

        if s1:
            ax.axhline(s1, color=self.BULL_GREEN, linestyle="--", linewidth=1.1, alpha=0.8, zorder=4)
            ax.text(n - 1, s1 + 0.6, f" [SSL/DEMAND] ${s1:,.2f}", color=self.BULL_GREEN, fontsize=9, fontweight="bold", zorder=5)

        # Overlay AI SMC Setup Target Box (Entry, SL, TP)
        if setup and isinstance(setup, dict):
            entry = setup.get("entry", current_price)
            sl = setup.get("sl")
            tp1 = setup.get("tp1")
            direction = setup.get("direction", "BUY").upper()

            # Entry Line
            ax.axhline(entry, color=self.ACCENT_CYAN, linestyle="-", linewidth=1.4, alpha=0.9, zorder=5)
            ax.text(0.5, entry + 0.6, f"[ENTRY] ${entry:,.2f}", color=self.ACCENT_CYAN, fontsize=9.5, fontweight="bold", zorder=6)

            # SL Line
            if sl:
                ax.axhline(sl, color="#f43f5e", linestyle="-.", linewidth=1.2, alpha=0.85, zorder=5)
                ax.text(0.5, sl - 1.4, f"[STOP LOSS] ${sl:,.2f}", color="#f43f5e", fontsize=9, fontweight="bold", zorder=6)

            # TP1 Line
            if tp1:
                ax.axhline(tp1, color="#10b981", linestyle="-.", linewidth=1.2, alpha=0.85, zorder=5)
                ax.text(0.5, tp1 + 0.6, f"[TAKE PROFIT] ${tp1:,.2f}", color="#10b981", fontsize=9, fontweight="bold", zorder=6)

            # Shaded Zone between Entry and SL (Risk Box) & Entry and TP1 (Profit Box)
            if sl and tp1:
                box_x_start = n - 12
                box_x_end = n + 3
                # Risk box (Light Red)
                risk_rect = patches.Rectangle(
                    (box_x_start, min(entry, sl)),
                    box_x_end - box_x_start,
                    abs(entry - sl),
                    facecolor="#ef4444", alpha=0.15, zorder=1
                )
                ax.add_patch(risk_rect)
                # Reward box (Light Green)
                reward_rect = patches.Rectangle(
                    (box_x_start, min(entry, tp1)),
                    box_x_end - box_x_start,
                    abs(entry - tp1),
                    facecolor="#10b981", alpha=0.15, zorder=1
                )
                ax.add_patch(reward_rect)

        # Highlight Current Spot Price
        ax.axhline(current_price, color=self.TEXT_WHITE, linestyle=":", linewidth=1.0, alpha=0.6, zorder=4)
        ax.text(n + 0.2, current_price, f" ${current_price:,.2f}", color=self.TEXT_WHITE,
                bbox=dict(boxstyle="round,pad=0.3", fc="#1e293b", ec=self.ACCENT_CYAN, lw=1.2),
                fontsize=9.5, fontweight="bold", verticalalignment="center", zorder=7)

        # Grids and axes labels
        ax.grid(True, color=self.GRID_DARK, linestyle=":", linewidth=0.7, alpha=0.7)
        ax_vol.grid(True, color=self.GRID_DARK, linestyle=":", linewidth=0.7, alpha=0.7)

        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")
        ax.tick_params(colors=self.TEXT_MUTED, labelsize=9)
        ax.set_xticklabels([])

        ax_vol.yaxis.tick_right()
        ax_vol.tick_params(colors=self.TEXT_MUTED, labelsize=8)
        ax_vol.set_xticklabels([])
        ax_vol.set_yticks([])

        # Title and Branding Header
        now_kh = datetime.now(CAMBODIA_TZ)
        time_str = now_kh.strftime("%d/%m/%Y %H:%M")
        chart_title = f"XAU/USD (Gold) • {timeframe} Institutional Chart • {time_str} UTC+7"
        if title_extra:
            chart_title += f" | {title_extra}"

        fig.text(0.08, 0.94, "AI LIVE CANDLESTICK & SMC PATTERN SCANNER", color=self.TEXT_WHITE, fontsize=13, fontweight="bold")
        fig.text(0.08, 0.905, chart_title, color=self.TEXT_MUTED, fontsize=9.5)

        # Watermark
        fig.text(0.50, 0.52, "XAUUSD INSTITUTIONAL INTELLIGENCE", color=self.GRID_DARK, fontsize=20,
                 fontweight="bold", alpha=0.4, horizontalalignment="center", verticalalignment="center", rotation=15)

        plt.subplots_adjust(left=0.04, right=0.90, top=0.88, bottom=0.06, hspace=0.08)

        # Export to PNG buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png", facecolor=self.BG_DARK, edgecolor="none", dpi=130)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
