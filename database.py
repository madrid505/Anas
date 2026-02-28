# database.py

import sqlite3
from config import DATABASE_FILE

# إنشاء قاعدة البيانات والجداول إذا لم تكن موجودة
conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    points INTEGER DEFAULT 0,
    messages INTEGER DEFAULT 0,
    country TEXT DEFAULT 'غير معروف'
)
''')
conn.commit()

# إضافة مستخدم جديد
def add_user(user_id, username):
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    cursor.execute("UPDATE users SET username=? WHERE user_id=?", (username, user_id))
    conn.commit()

# زيادة النقاط
def increment_points(user_id, amount=1):
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount, user_id))
    conn.commit()

# زيادة عدد الرسائل
def increment_messages(user_id, amount=1):
    cursor.execute("UPDATE users SET messages = messages + ? WHERE user_id=?", (amount, user_id))
    conn.commit()

# الحصول على نقاط المستخدم
def get_points(user_id):
    cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

# الحصول على معلومات المستخدم
def get_user_info(user_id):
    cursor.execute("SELECT username, messages, country FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    if result:
        return {"username": result[0], "messages": result[1], "country": result[2]}
    return None
