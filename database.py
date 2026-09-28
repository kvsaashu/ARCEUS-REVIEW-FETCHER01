import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import DATABASE_PATH

def get_db():
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
    except Exception:
        pass
    
    # Table for storing individual matched reviews
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_type TEXT,            -- 'APP' or 'MAP'
        target_id TEXT,               -- package_id or maps_place_id
        target_name TEXT,             -- App Title or Place Name
        review_id TEXT UNIQUE,        -- Play Store reviewId or unique hash
        user_name TEXT,
        user_image TEXT,
        rating INTEGER,
        review_text TEXT,
        review_date TEXT,
        review_time TEXT,
        matched_keywords TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Table for scan runs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scan_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_type TEXT,
        target_id TEXT,
        search_date TEXT,
        total_scanned INTEGER,
        total_matched INTEGER,
        run_type TEXT,                -- 'MANUAL' or 'AUTO'
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Table for system settings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    # Table for 8-Day Auto-Retention Campaign Tasks
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS campaign_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_type TEXT DEFAULT 'APP',
        target_id TEXT NOT NULL,
        target_name TEXT,
        start_date TEXT NOT NULL,
        check_date TEXT NOT NULL,
        retention_days INTEGER DEFAULT 8,
        keywords TEXT,
        members TEXT,
        bulker_name TEXT DEFAULT '',
        status TEXT DEFAULT 'PENDING',  -- 'PENDING', 'COMPLETED', 'FAILED'
        matched_units INTEGER DEFAULT 0,
        telegram_sent INTEGER DEFAULT 0,
        last_checked_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Safe migration in case table was created earlier without bulker_name
    try:
        cursor.execute("ALTER TABLE campaign_tasks ADD COLUMN bulker_name TEXT DEFAULT ''")
    except Exception:
        pass

    conn.commit()
    conn.close()

def save_review(review_dict: Dict[str, Any]) -> bool:
    """Saves a review. Returns True if inserted, False if already exists (duplicate)."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT OR IGNORE INTO reviews 
        (service_type, target_id, target_name, review_id, user_name, user_image, rating, review_text, review_date, review_time, matched_keywords)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            review_dict.get("service_type", "APP"),
            review_dict.get("target_id", ""),
            review_dict.get("target_name", ""),
            review_dict.get("review_id", ""),
            review_dict.get("user_name", ""),
            review_dict.get("user_image", ""),
            review_dict.get("rating", 0),
            review_dict.get("review_text", ""),
            review_dict.get("review_date", ""),
            review_dict.get("review_time", ""),
            review_dict.get("matched_keywords", "")
        ))
        inserted = cursor.rowcount > 0
        conn.commit()
        return inserted
    finally:
        conn.close()

def log_scan_run(service_type: str, target_id: str, search_date: str, total_scanned: int, total_matched: int, run_type: str = "MANUAL"):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO scan_runs (service_type, target_id, search_date, total_scanned, total_matched, run_type)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (service_type, target_id, search_date, total_scanned, total_matched, run_type))
    conn.commit()
    conn.close()

def get_recent_reviews(limit: int = 100, service_type: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    if service_type:
        cursor.execute("SELECT * FROM reviews WHERE service_type = ? ORDER BY id DESC LIMIT ?", (service_type, limit))
    else:
        cursor.execute("SELECT * FROM reviews ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results

def get_setting(key: str, default: str = "") -> str:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key: str, value: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

# --- CAMPAIGN TASKS OPERATIONS ---
def create_campaign_task(
    service_type: str,
    target_id: str,
    target_name: str,
    start_date: str,
    check_date: str,
    retention_days: int = 8,
    keywords: str = "",
    members: str = "",
    bulker_name: str = ""
) -> int:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO campaign_tasks 
    (service_type, target_id, target_name, start_date, check_date, retention_days, keywords, members, bulker_name, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
    """, (service_type, target_id, target_name, start_date, check_date, retention_days, keywords, members, bulker_name))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_campaign_tasks(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campaign_tasks ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results

def get_due_campaign_tasks(today_str: str) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    # Check any task whose check_date <= today and status is PENDING
    cursor.execute("""
    SELECT * FROM campaign_tasks 
    WHERE check_date <= ? AND status = 'PENDING'
    ORDER BY id ASC
    """, (today_str,))
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results

def get_campaign_task_by_id(task_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campaign_tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_campaign_task_status(task_id: int, status: str, matched_units: int, telegram_sent: int = 1):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE campaign_tasks 
    SET status = ?, matched_units = ?, telegram_sent = ?, last_checked_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (status, matched_units, telegram_sent, task_id))
    conn.commit()
    conn.close()

def delete_campaign_task(task_id: int) -> bool:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM campaign_tasks WHERE id = ?", (task_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# Initialize tables when imported
init_db()

