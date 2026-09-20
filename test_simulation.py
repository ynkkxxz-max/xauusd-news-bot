import sys
import os
from pathlib import Path

# Ensure paths
sys.path.insert(0, str(Path(__file__).resolve().parent))

from collectors.gold_price import GoldPriceCollector
from collectors.economic_calendar import EconomicCalendarCollector
from collectors.breaking_news import BreakingNewsCollector
from analyzers.gold_filter import GoldNewsFilter
from analyzers.macro_analyzer import MacroAnalyzer
from formatters.khmer_formatter import KhmerFormatter
from telegram_notifier import TelegramNotifier
import database

def run_all_tests():
    print("================================================================")
    print("🚀 RUNNING XAUUSD NEWS ASSISTANT COMPLETE SYSTEM VERIFICATION")
    print("================================================================")

    # 1. Test Gold Price Collection & Cambodian Unit Conversion
    print("\n--- [TEST 1] Gold Price & Cambodian Weight Conversion ---")
    gold_collector = GoldPriceCollector()
    price_data = gold_collector.fetch_price()
    print(f"XAUUSD Price (1 Troy Oz): ${price_data['price_oz']:,.2f}")
    print(f"1 តម្លឹង (37.5g)          : ${price_data['price_damlung']:,.2f}")
    print(f"1 ជី (3.75g)             : ${price_data['price_chi']:,.2f}")
    print(f"1 ហ៊ុន (0.375g)          : ${price_data['price_hun']:,.2f}")
    print(f"Daily Change             : ${price_data['change']:,.2f} ({price_data['change_pct']:.2f}%)")
    
    # Assert unit conversion integrity
    # 1 Damlung = 10 Chi = 100 Hun
    assert abs(price_data['price_damlung'] - price_data['price_chi'] * 10) < 0.01
    assert abs(price_data['price_chi'] - price_data['price_hun'] * 10) < 0.01
    print("✅ Unit conversion mathematical validation PASSED!")

    # Format daily gold price message
    daily_msg = KhmerFormatter.format_daily_gold_price(price_data)
    print("\n[Preview: Daily Gold Price Message in Khmer]:")
    print(daily_msg)

    # 2. Test Upcoming High-Impact Alert (Mode 2)
    print("\n--- [TEST 2] Upcoming High-Impact News Alerts (15m & 5m) ---")
    mock_event = {
        "id": "USD_CPI_20260920_1930",
        "title": "CPI m/m (Consumer Price Index)",
        "currency": "USD",
        "impact": "HIGH",
        "release_time_str": "19:30",
        "forecast": "0.3%",
        "previous": "0.2%",
        "source": "US Bureau of Labor Statistics / Global Calendar"
    }

    upcoming_15m_msg = KhmerFormatter.format_upcoming_alert(mock_event, minutes_left=15)
    print("\n[Preview: 15-Minute Upcoming Alert]:")
    print(upcoming_15m_msg)

    upcoming_5m_msg = KhmerFormatter.format_upcoming_alert(mock_event, minutes_left=5)
    print("\n[Preview: 5-Minute Countdown Alert]:")
    print(upcoming_5m_msg)

    # 3. Test Actual Release Analysis Engine (Mode 3)
    print("\n--- [TEST 3] Macro Analyzer: CPI Actual vs Forecast ---")
    # Scenario A: CPI Higher than forecast (0.5% vs 0.3%) -> Bullish USD -> Bearish Gold
    analysis_higher = MacroAnalyzer.analyze_actual_vs_forecast(
        mock_event["title"], actual="0.5%", forecast="0.3%", previous="0.2%"
    )
    mock_event["actual"] = "0.5%"
    actual_alert_higher = KhmerFormatter.format_actual_release_alert(mock_event, analysis_higher)
    print("\n[Preview: Flash Release Alert (Actual > Forecast)]:")
    print(actual_alert_higher)
    assert "Possible Bearish Pressure" in analysis_higher["xau_pressure"]
    print("✅ CPI Higher -> Bearish Gold logic verified!")

    # Scenario B: Unemployment higher than forecast -> Bearish USD -> Bullish Gold
    unemployment_analysis = MacroAnalyzer.analyze_actual_vs_forecast(
        "Unemployment Rate", actual="4.3%", forecast="4.0%", previous="4.0%"
    )
    assert "Possible Bullish Pressure" in unemployment_analysis["xau_pressure"]
    print("✅ Inverse metric (Unemployment) -> Bullish Gold logic verified!")

    # 4. Test Breaking Event (Mode 4)
    print("\n--- [TEST 4] Mode 4 Breaking Event Alert ---")
    mock_breaking = {
        "title": "Breaking: Middle East conflict escalates, market seeks safe haven assets",
        "source": "ForexLive Gold",
        "link": "https://example.com/news/123"
    }
    breaking_analysis = MacroAnalyzer.analyze_breaking_news(mock_breaking["title"])
    breaking_msg = KhmerFormatter.format_breaking_event_alert(mock_breaking, breaking_analysis)
    print("\n[Preview: Breaking News Alert in Khmer]:")
    print(breaking_msg)
    assert "Possible Bullish Pressure" in breaking_analysis["xau_pressure"]
    print("✅ Safe-haven geopolitical escalation -> Bullish Gold verified!")

    # 5. Test Deduplication & SQLite Database
    print("\n--- [TEST 5] Anti-Spam & SQLite Deduplication ---")
    test_event_id = "USD_TEST_EVENT_001"
    # Stage 1: check not sent
    assert not database.is_event_stage_sent(test_event_id, "upcoming_15m")
    # Record sent
    database.record_event_stage(test_event_id, "Test Event", "USD", "19:30", "upcoming_15m")
    # Stage 2: check is sent (should prevent duplicate)
    assert database.is_event_stage_sent(test_event_id, "upcoming_15m")
    print("✅ Event stage deduplication test PASSED!")

    # Test news deduplication
    test_news_id = "test_news_hash_999"
    assert not database.is_news_sent(test_news_id)
    database.record_news_sent(test_news_id, "Test Title", "Test Source")
    assert database.is_news_sent(test_news_id)
    print("✅ News deduplication test PASSED!")

    # Test Telegram notifier simulation dispatch
    notifier = TelegramNotifier()
    res = notifier.send_message(daily_msg, auto_pin=True)
    assert res.get("ok") is True
    print("✅ Telegram Dispatch Simulator PASSED!")

    print("\n================================================================")
    print("🎉 ALL TEST SUITES PASSED FLAWLESSLY!")
    print("================================================================")

if __name__ == "__main__":
    run_all_tests()
