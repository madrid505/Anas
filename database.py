import sqlite3

DB_FILE = "bot_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # جدول نقاط التفاعل
    c.execute("""
    CREATE TABLE IF NOT EXISTS points(
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        points INTEGER DEFAULT 0
    )
    """)
    # جدول الردود
    c.execute("""
    CREATE TABLE IF NOT EXISTS replies(
        trigger TEXT PRIMARY KEY,
        response TEXT
    )
    """)
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_FILE)
