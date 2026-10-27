"""
Collectors package for XAU/USD news assistant.
Contains breaking news collectors, economic calendar, gold price collector, and story image builder.
"""
from .breaking_news import BreakingNewsCollector
from .economic_calendar import EconomicCalendarCollector
from .gold_price import GoldPriceCollector
from .story_image_builder import StoryImageBuilder

__all__ = [
    "BreakingNewsCollector",
    "EconomicCalendarCollector",
    "GoldPriceCollector",
    "StoryImageBuilder",
]
