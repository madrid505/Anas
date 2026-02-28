import sqlite3
from contextlib import closing
from config import DATABASE_FILE

# إنشاء قاعدة البيانات إذا لم تكن موجودة
def init_db():
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS user_points (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                points INTEGER DEFAULT 0
            )
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS messages_log (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                chat_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS custom_replies (
                keyword TEXT PRIMARY KEY,
                reply TEXT
            )
            """)

# إضافة نقاط لمستخدم
def add_point(user_id, username, points=1):
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        with conn:
            cur = conn.execute("SELECT points FROM user_points WHERE user_id=?", (user_id,))
            row = cur.fetchone()
            if row:
                conn.execute("UPDATE user_points SET points=points+? WHERE user_id=?", (points, user_id))
            else:
                conn.execute("INSERT INTO user_points (user_id, username, points) VALUES (?, ?, ?)", (user_id, username, points))

# الحصول على نقاط المستخدم
def get_points(user_id):
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        cur = conn.execute("SELECT points FROM user_points WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        return row[0] if row else 0

# تسجيل رسالة جديدة للعضو
def log_message(user_id, chat_id):
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        with conn:
            conn.execute("INSERT INTO messages_log (user_id, chat_id) VALUES (?, ?)", (user_id, chat_id))

# إضافة رد مخصص
def add_reply(keyword, reply):
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        with conn:
            conn.execute("INSERT OR REPLACE INTO custom_replies (keyword, reply) VALUES (?, ?)", (keyword, reply))

# الحصول على الردود
def get_reply(keyword):
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        cur = conn.execute("SELECT reply FROM custom_replies WHERE keyword=?", (keyword,))
        row = cur.fetchone()
        return row[0] if row else None
