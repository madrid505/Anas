import sqlite3
from contextlib import closing

DATABASE_FILE = "bot_data.db"

def init_db():
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        with conn:
            # جدول النقاط والرتب والأسماء
            conn.execute("""
            CREATE TABLE IF NOT EXISTS user_data (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                points INTEGER DEFAULT 0,
                rank TEXT DEFAULT 'عضو'
            )
            """)
            # جدول الردود التلقائية
            conn.execute("CREATE TABLE IF NOT EXISTS custom_replies (keyword TEXT PRIMARY KEY, reply TEXT)")

def update_user_info(user_id, username, full_name):
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        with conn:
            cur = conn.execute("SELECT full_name FROM user_data WHERE user_id=?", (user_id,))
            row = cur.fetchone()
            old_name = row[0] if row else full_name
            
            conn.execute("""
                INSERT INTO user_data (user_id, username, full_name) VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, full_name=excluded.full_name
            """, (user_id, username, full_name))
            return old_name # نعود بالاسم القديم للمقارنة

def set_rank(user_id, rank):
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        with conn:
            conn.execute("UPDATE user_data SET rank=? WHERE user_id=?", (rank, user_id))

def get_user_stats(user_id):
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        cur = conn.execute("SELECT rank, points, full_name FROM user_data WHERE user_id=?", (user_id,))
        return cur.fetchone()
