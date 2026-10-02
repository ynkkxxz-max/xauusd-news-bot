import sqlite3
import datetime
from pathlib import Path
from config import DB_PATH

def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    return conn

def init_db():
    conn = get_db_connection()
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
        is_broadcasted INTEGER DEFAULT 0,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    try:
        cursor.execute("ALTER TABLE sent_news ADD COLUMN is_broadcasted INTEGER DEFAULT 0")
    except Exception:
        pass

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
    
    # Table for tracking user votes on AI signals (Hit TP / Hit SL)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS signal_votes (
        vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
        signal_id TEXT,
        user_id INTEGER,
        user_name TEXT,
        vote_type TEXT, -- 'TP' or 'SL'
        voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(signal_id, user_id)
    )
    """)
    
    conn.commit()
    conn.close()

def is_event_stage_sent(event_id: str, stage: str, actual_val: str = None) -> bool:
    """Check if specific stage of an event was already sent.
    If stage is 'actual', checks if the actual value has already been recorded."""
    conn = get_db_connection()
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
    conn = get_db_connection()
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM sent_news WHERE news_id = ? AND is_broadcasted = 1", (news_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def record_news_sent(news_id: str, title: str, source: str, is_broadcasted: int = 0):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO sent_news (news_id, title, source, is_broadcasted, sent_at)
    VALUES (?, ?, ?, ?, datetime('now'))
    ON CONFLICT(news_id) DO UPDATE SET 
        title = excluded.title,
        source = excluded.source,
        is_broadcasted = CASE WHEN excluded.is_broadcasted = 1 THEN 1 ELSE sent_news.is_broadcasted END,
        sent_at = datetime('now')
    """, (news_id, title, source, is_broadcasted))
    conn.commit()
    conn.close()

def clear_news_from_data(news_id: str, title: str = "", source: str = ""):
    """
    Explicitly clears a news item from data pool right after broadcast.
    Marks it as broadcasted (is_broadcasted=1) and permanently records it so it can never be processed again.
    """
    record_news_sent(news_id, title, source, is_broadcasted=1)

def get_recent_news_titles(hours: int = 24) -> list:
    """Returns a list of titles actually broadcasted in the last N hours for similarity/duplicate checking."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT title FROM sent_news 
    WHERE is_broadcasted = 1 AND sent_at >= datetime('now', ?)
    """, (f"-{hours} hours",))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows if r[0]]

def is_title_already_broadcasted(title: str, hours: int = 48) -> bool:
    """Checks whether the exact title or stem-identical title was already broadcasted in the last N hours."""
    if not title:
        return False
    import re
    norm_input = re.sub(r'[^a-zA-Z0-9\u1780-\u17FF]', '', title).lower()
    if len(norm_input) < 15:
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT title FROM sent_news 
    WHERE is_broadcasted = 1 AND sent_at >= datetime('now', ?)
    """, (f"-{hours} hours",))
    rows = cursor.fetchall()
    conn.close()

    sig = norm_input[:45]
    for (past_t,) in rows:
        if not past_t:
            continue
        past_norm = re.sub(r'[^a-zA-Z0-9\u1780-\u17FF]', '', past_t).lower()
        if sig in past_norm or (len(past_norm) >= 45 and past_norm[:45] in norm_input):
            return True
    return False

def is_daily_price_sent(date_str: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM daily_price_logs WHERE date_str = ?", (date_str,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def record_daily_price_sent(date_str: str, message_id: int = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO daily_price_logs (date_str, message_id, sent_at)
    VALUES (?, ?, datetime('now'))
    """, (date_str, message_id))
    conn.commit()
    conn.close()

def get_state(key: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM bot_state WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_state(key: str, value: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO bot_state (key, value, updated_at)
    VALUES (?, ?, datetime('now'))
    """, (key, value))
    conn.commit()
    conn.close()

def get_daily_signal_count(date_str: str = None) -> int:
    """
    Returns the total number of trade signal positions issued for the given date (Cambodia Time, UTC+7).
    """
    if not date_str:
        import pytz
        cambodia_tz = pytz.timezone("Asia/Phnom_Penh")
        date_str = datetime.datetime.now(cambodia_tz).strftime("%Y-%m-%d")
    val = get_state(f"daily_signal_positions_{date_str}")
    if val is None:
        val = get_state(f"sniper_signal_count_{date_str}")
    return int(val or 0)

def increment_daily_signal_count(date_str: str = None) -> int:
    """
    Increments and returns the daily signal position count for the date.
    Strictly synchronizes across all signal modules.
    """
    if not date_str:
        import pytz
        cambodia_tz = pytz.timezone("Asia/Phnom_Penh")
        date_str = datetime.datetime.now(cambodia_tz).strftime("%Y-%m-%d")
    curr = get_daily_signal_count(date_str)
    new_count = curr + 1
    set_state(f"daily_signal_positions_{date_str}", str(new_count))
    set_state(f"sniper_signal_count_{date_str}", str(new_count))
    return new_count

def can_issue_signal_today(max_signals: int = 5, date_str: str = None) -> bool:
    """
    Checks if a new trade signal position can be issued without exceeding max_signals (default: 5).
    """
    return get_daily_signal_count(date_str) < max_signals


def record_signal_vote(signal_id: str, user_id: int, user_name: str, vote_type: str) -> dict:
    """
    Records or updates user feedback on a signal ('TP' or 'SL').
    Returns dict: {'success': bool, 'is_new': bool, 'tp_count': int, 'sl_count': int}
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user already voted
    cursor.execute("SELECT vote_type FROM signal_votes WHERE signal_id = ? AND user_id = ?", (signal_id, user_id))
    existing = cursor.fetchone()
    is_new = existing is None

    cursor.execute("""
    INSERT OR REPLACE INTO signal_votes (signal_id, user_id, user_name, vote_type, voted_at)
    VALUES (?, ?, ?, ?, datetime('now'))
    """, (signal_id, user_id, user_name, vote_type))
    conn.commit()

    # Query updated totals
    cursor.execute("SELECT vote_type, COUNT(*) FROM signal_votes WHERE signal_id = ? GROUP BY vote_type", (signal_id,))
    counts = dict(cursor.fetchall())
    conn.close()

    return {
        "success": True,
        "is_new": is_new,
        "tp_count": counts.get("TP", 0),
        "sl_count": counts.get("SL", 0)
    }

def get_overall_signal_vote_stats() -> dict:
    """Returns all-time win/loss stats voted by users."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT vote_type, COUNT(*) FROM signal_votes GROUP BY vote_type")
    counts = dict(cursor.fetchall())
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM signal_votes")
    total_traders = cursor.fetchone()[0] or 0
    conn.close()

    tp = counts.get("TP", 0)
    sl = counts.get("SL", 0)
    total = tp + sl
    win_rate = round((tp / total * 100), 1) if total > 0 else 0.0

    return {
        "total_votes": total,
        "tp_votes": tp,
        "sl_votes": sl,
        "win_rate": win_rate,
        "total_traders": total_traders
    }
def cleanup_old_records(days: int = 2) -> int:
    """
    Cleans up logs and history older than `days` (default 2 days / 48 hours) to keep data.db ultra-lightweight and fast.
    Executes SQLite VACUUM to reclaim storage and optimize performance.
    """
    conn = get_db_connection()
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
