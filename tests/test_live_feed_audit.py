import os
import sys

os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from collectors.breaking_news import BreakingNewsCollector
from analyzers.macro_analyzer import MacroAnalyzer
from formatters.khmer_formatter import KhmerFormatter

def audit_live_feeds():
    print("=" * 60)
    print("📡 LIVE RSS FEEDS AUDIT & SIMULATION")
    print("=" * 60)
    collector = BreakingNewsCollector()
    analyzer = MacroAnalyzer()
    formatter = KhmerFormatter()

    print("Fetching live feeds across all 21 sources...")
    items = collector.fetch_latest_news()
    print(f"Total raw items fetched: {len(items)}")

    approved_items = []
    dropped_neutral = 0
    dropped_questions = 0

    for item in items[:15]:
        title = item.get("title", "")
        if "?" in title:
            dropped_questions += 1
            continue

        analysis = analyzer.analyze_breaking_news(item)
        impact = analysis.get("impact", "")
        if "អព្យាក្រឹត" in impact:
            dropped_neutral += 1
            continue

        formatted = formatter.format_breaking_event_alert(item, analysis)
        approved_items.append((item, analysis, formatted))

    print(f"Audited top 15 items: {len(approved_items)} passed all institutional quality gates.")
    print(f"Dropped as neutral: {dropped_neutral}")
    print(f"Dropped as speculative/question: {dropped_questions}")

    if approved_items:
        print("\n--- SAMPLE APPROVED CANDIDATE ---")
        item, analysis, formatted = approved_items[0]
        print(f"Original English Title: {item.get('title')}")
        print(f"Source: {item.get('source')}")
        print(f"Link: {item.get('link')}")
        print("\nFormatted Telegram Channel Message:")
        print("-" * 40)
        print(formatted)
        print("-" * 40)

if __name__ == "__main__":
    audit_live_feeds()
