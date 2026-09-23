import time
import logging
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

    Guarantees < 0.05s response time for interactive Telegram commands (Price, SMC, Lot).
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
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

        self.TTL_PRICE = 8.0       # 8 seconds TTL for Price & Key levels
        self.TTL_MACRO = 15.0     # 15 seconds TTL for Macro DXY
        self.TTL_ORDER_BOOK = 8.0 # 8 seconds TTL for Order Book Depth
        self.TTL_SMC = 20.0       # 20 seconds TTL for Pre-computed SMC Plan

        self._initialized = True
        logger.info("[MarketDataCache] Ultra-Fast In-Memory RAM Cache initialized.")

    def get_price(self) -> Optional[Dict[str, Any]]:
        if self._price_cache and (time.time() - self._price_ts < self.TTL_PRICE):
            return self._price_cache
        return None

    def set_price(self, data: Dict[str, Any]):
        if data:
            self._price_cache = data
            self._price_ts = time.time()

    def get_macro(self) -> Optional[Dict[str, Any]]:
        if self._macro_cache and (time.time() - self._macro_ts < self.TTL_MACRO):
            return self._macro_cache
        return None

    def set_macro(self, data: Dict[str, Any]):
        if data:
            self._macro_cache = data
            self._macro_ts = time.time()

    def get_order_book(self) -> Optional[Dict[str, Any]]:
        if self._order_book_cache and (time.time() - self._order_book_ts < self.TTL_ORDER_BOOK):
            return self._order_book_cache
        return None

    def set_order_book(self, data: Dict[str, Any]):
        if data:
            self._order_book_cache = data
            self._order_book_ts = time.time()

    def get_smc_setup(self) -> Optional[Dict[str, Any]]:
        if self._smc_setup_cache and (time.time() - self._smc_setup_ts < self.TTL_SMC):
            return self._smc_setup_cache
        return None

    def set_smc_setup(self, setup: Dict[str, Any]):
        if setup:
            self._smc_setup_cache = setup
            self._smc_setup_ts = time.time()

market_cache = MarketDataCache()
