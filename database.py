# database.py

import sqlite3
from config import DATABASE_FILE

# إنشاء قاعدة البيانات إذا لم تكن موجودة
conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
cursor = conn.cursor()

# جدول لتخزين نقاط ملك التفاعل
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_points (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    points INTEGER DEFAULT 0
)
""")

# جدول لتخزين عدد الرسائل لكل عضو (للكشف)
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_messages (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    messages_count INTEGER DEFAULT 0,
    country TEXT DEFAULT 'غير معروف'
)
""")

conn.commit()

# دوال مساعدة

def add_user(user_id: int, username: str):
    cursor.execute("INSERT OR IGNORE INTO user_points (user_id, username) VALUES (?, ?)", (user_id, username))
    cursor.execute("INSERT OR IGNORE INTO user_messages (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

def increment_points(user_id: int, points: int = 1):
    cursor.execute("UPDATE user_points SET points = points + ? WHERE user_id = ?", (points, user_id))
    conn.commit()

def get_points(user_id: int):
    cursor.execute("SELECT points FROM user_points WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def increment_messages(user_id: int):
    cursor.execute("UPDATE user_messages SET messages_count = messages_count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()

def get_messages(user_id: int):
    cursor.execute("SELECT messages_count FROM user_messages WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def update_country(user_id: int, country: str):
    cursor.execute("UPDATE user_messages SET country = ? WHERE user_id = ?", (country, user_id))
    conn.commit()

def get_user_info(user_id: int):
    cursor.execute("SELECT username, messages_count, country FROM user_messages WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        return {"username": result[0], "messages": result[1], "country": result[2]}
    return None
