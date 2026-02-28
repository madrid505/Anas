import sqlite3

DB_FILE = "bot_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # نقاط ملك التفاعل
    c.execute("""
    CREATE TABLE IF NOT EXISTS points(
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        points INTEGER DEFAULT 0
    )
    """)
    
    # الردود
    c.execute("""
    CREATE TABLE IF NOT EXISTS replies(
        trigger TEXT PRIMARY KEY,
        response TEXT
    )
    """)
    
    # الرتب
    c.execute("""
    CREATE TABLE IF NOT EXISTS roles(
        user_id INTEGER PRIMARY KEY,
        role TEXT
    )
    """)
    
    # تتبع تغييرات الأسماء
    c.execute("""
    CREATE TABLE IF NOT EXISTS name_changes(
        user_id INTEGER PRIMARY KEY,
        old_name TEXT,
        new_name TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_FILE)
