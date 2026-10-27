import time
import logging
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MarketDataCache:
    """
    Ultra-Fast In-Memory Real-Time Market Data Cache (RAM Cache).
    Maintains synchronized state of:
    - Spot Gold Price & Cambodia Local Market Conversions
    - Technical Key Levels (Pivot, R1, R2, S1, S2, Buy/Sell Zones)
    - Macro Correlation Data (DXY, US10Y, GLD ETF)
    - 100-Level Institutional Order Book Depth (Bid/Ask Walls)
    - Pre-computed Decisive SMC Setup (Single Direction Plan)

    Guarantees < 0.05s response time for interactive Telegram commands (Price, SMC, Lot)
    using Stale-While-Revalidate & Continuous Background Pre-warming.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(MarketDataCache, cls).__new__(cls, *args, **kwargs)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._price_cache: Optional[Dict[str, Any]] = None
        self._price_ts: float = 0.0

        self._macro_cache: Optional[Dict[str, Any]] = None
        self._macro_ts: float = 0.0

        self._order_book_cache: Optional[Dict[str, Any]] = None
        self._order_book_ts: float = 0.0

        self._smc_setup_cache: Optional[Dict[str, Any]] = None
        self._smc_setup_ts: float = 0.0

        # Pre-formatted messages for instant sub-second delivery (< 0.01s)
        self._price_msg_cache: Optional[str] = None
        self._smc_msg_cache: Optional[str] = None

        self.TTL_PRICE = 10.0      # 10 seconds TTL for Price & Key levels
        self.TTL_MACRO = 20.0      # 20 seconds TTL for Macro DXY
        self.TTL_ORDER_BOOK = 10.0 # 10 seconds TTL for Order Book Depth
        self.TTL_SMC = 25.0        # 25 seconds TTL for Pre-computed SMC Plan

        self._initialized = True
        logger.info("[MarketDataCache] Ultra-Fast In-Memory RAM Cache initialized.")

    def get_price(self, allow_stale: bool = True) -> Optional[Dict[str, Any]]:
        """Returns cached price in < 0.001s. If allow_stale is True, returns last known valid price."""
        if self._price_cache:
            if time.time() - self._price_ts < self.TTL_PRICE or allow_stale:
                return self._price_cache
        return None

    def set_price(self, data: Dict[str, Any]):
        if data:
            self._price_cache = data
            self._price_ts = time.time()

    def get_macro(self, allow_stale: bool = True) -> Optional[Dict[str, Any]]:
        """Returns cached macro correlations in < 0.001s."""
        if self._macro_cache:
            if time.time() - self._macro_ts < self.TTL_MACRO or allow_stale:
                return self._macro_cache
        return None

    def set_macro(self, data: Dict[str, Any]):
        if data:
            self._macro_cache = data
            self._macro_ts = time.time()

    def get_order_book(self, allow_stale: bool = True) -> Optional[Dict[str, Any]]:
        """Returns cached order book depth in < 0.001s."""
        if self._order_book_cache:
            if time.time() - self._order_book_ts < self.TTL_ORDER_BOOK or allow_stale:
                return self._order_book_cache
        return None

    def set_order_book(self, data: Dict[str, Any]):
        if data:
            self._order_book_cache = data
            self._order_book_ts = time.time()

    def get_smc_setup(self, allow_stale: bool = True) -> Optional[Dict[str, Any]]:
        """Returns pre-computed SMC setup in < 0.001s."""
        if self._smc_setup_cache:
            if time.time() - self._smc_setup_ts < self.TTL_SMC or allow_stale:
                return self._smc_setup_cache
        return None

    def set_smc_setup(self, setup: Dict[str, Any]):
        if setup:
            self._smc_setup_cache = setup
            self._smc_setup_ts = time.time()

    def get_preformatted_price_msg(self) -> Optional[str]:
        """Returns pre-rendered price message for 0.0005s instant delivery."""
        if self._price_msg_cache and (time.time() - self._price_ts < self.TTL_PRICE * 2):
            return self._price_msg_cache
        return None

    def set_preformatted_price_msg(self, msg: str):
        self._price_msg_cache = msg

    def get_preformatted_smc_msg(self) -> Optional[str]:
        """Returns pre-rendered SMC setup message for 0.0005s instant delivery."""
        if self._smc_msg_cache and (time.time() - self._smc_setup_ts < self.TTL_SMC * 2):
            return self._smc_msg_cache
        return None

    def set_preformatted_smc_msg(self, msg: str):
        self._smc_msg_cache = msg

market_cache = MarketDataCache()

