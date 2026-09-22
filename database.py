import sqlite3
import datetime
from pathlib import Path
from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table for tracking sent events (Economic calendar)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sent_events (
        event_id TEXT PRIMARY KEY,
        event_name TEXT,
        currency TEXT,
        release_time TEXT,
        stage TEXT, -- 'upcoming_15m', 'upcoming_5m', 'actual'
        actual_val TEXT,
        forecast_val TEXT,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Table for tracking sent breaking news / general news (Deduplication)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sent_news (
        news_id TEXT PRIMARY KEY,
        title TEXT,
        source TEXT,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Table for tracking daily price broadcasts to ensure once-per-day execution
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_price_logs (
        date_str TEXT PRIMARY KEY,
        message_id INTEGER,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Generic key-value state (e.g. last breaking-alert timestamp)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bot_state (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

def is_event_stage_sent(event_id: str, stage: str, actual_val: str = None) -> bool:
    """Check if specific stage of an event was already sent.
    If stage is 'actual', checks if the actual value has already been recorded."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    composite_id = f"{event_id}_{stage}"
    
    if stage == 'actual':
        cursor.execute(
            "SELECT actual_val FROM sent_events WHERE event_id = ?", 
            (composite_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return False
        # If we already recorded this exact actual value, don't resend
        return row[0] == str(actual_val) if actual_val is not None else True
    else:
        cursor.execute(
            "SELECT 1 FROM sent_events WHERE event_id = ?", 
            (composite_id,)
        )
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

def record_event_stage(event_id: str, event_name: str, currency: str, release_time: str, stage: str, actual_val: str = None, forecast_val: str = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Use insert or replace keyed by composite identifier
    composite_id = f"{event_id}_{stage}"
    cursor.execute("""
    INSERT OR REPLACE INTO sent_events (event_id, event_name, currency, release_time, stage, actual_val, forecast_val, sent_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (composite_id, event_name, currency, release_time, stage, actual_val, forecast_val))
    conn.commit()
    conn.close()

def is_news_sent(news_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM sent_news WHERE news_id = ?", (news_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def record_news_sent(news_id: str, title: str, source: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR IGNORE INTO sent_news (news_id, title, source, sent_at)
    VALUES (?, ?, ?, datetime('now'))
    """, (news_id, title, source))
    conn.commit()
    conn.close()

def get_recent_news_titles(hours: int = 4) -> list:
    """Returns a list of titles sent in the last N hours for similarity/duplicate checking."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT title FROM sent_news 
    WHERE sent_at >= datetime('now', ?)
    """, (f"-{hours} hours",))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows if r[0]]

def is_daily_price_sent(date_str: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM daily_price_logs WHERE date_str = ?", (date_str,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def record_daily_price_sent(date_str: str, message_id: int = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO daily_price_logs (date_str, message_id, sent_at)
    VALUES (?, ?, datetime('now'))
    """, (date_str, message_id))
    conn.commit()
    conn.close()

def get_state(key: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM bot_state WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_state(key: str, value: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO bot_state (key, value, updated_at)
    VALUES (?, ?, datetime('now'))
    """, (key, value))
    conn.commit()
def cleanup_old_records(days: int = 30) -> int:
    """
    Cleans up logs and history older than `days` to keep data.db lightweight and fast.
    Executes SQLite VACUUM to reclaim storage.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    DELETE FROM sent_news 
    WHERE sent_at < datetime('now', ?)
    """, (f"-{days} days",))
    deleted_news = cursor.rowcount

    cursor.execute("""
    DELETE FROM sent_events 
    WHERE sent_at < datetime('now', ?)
    """, (f"-{days} days",))
    deleted_events = cursor.rowcount

    cursor.execute("""
    DELETE FROM daily_price_logs 
    WHERE sent_at < datetime('now', ?)
    """, (f"-{days} days",))
    deleted_prices = cursor.rowcount

    conn.commit()
    cursor.execute("VACUUM")
    conn.close()
    return deleted_news + deleted_events + deleted_prices

# Initialize upon import
init_db()
