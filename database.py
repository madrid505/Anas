import sqlite3
from config import DATABASE_FILE

# إنشاء قاعدة البيانات إذا لم تكن موجودة
conn = sqlite3.connect(DATABASE_FILE)
cursor = conn.cursor()

# جدول المستخدمين لتتبع النقاط والمشاركة
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    points INTEGER DEFAULT 0,
    message_count INTEGER DEFAULT 0,
    country TEXT DEFAULT 'غير معروف'
)
''')

# جدول للردود المخصصة
cursor.execute('''
CREATE TABLE IF NOT EXISTS custom_replies (
    trigger TEXT PRIMARY KEY,
    response TEXT
)
''')

# جدول لتخزين آخر الأسماء لتتبع التغيير
cursor.execute('''
CREATE TABLE IF NOT EXISTS username_history (
    user_id INTEGER PRIMARY KEY,
    old_username TEXT,
    new_username TEXT
)
''')

conn.commit()

# دوال مساعدة للتعامل مع قاعدة البيانات

def add_user(user_id, username, country='غير معروف'):
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, country) VALUES (?, ?, ?)
    ''', (user_id, username, country))
    conn.commit()

def update_message_count(user_id):
    cursor.execute('''
        UPDATE users SET message_count = message_count + 1, points = points + 1 WHERE user_id = ?
    ''', (user_id,))
    conn.commit()

def get_top_user():
    cursor.execute('SELECT username, points FROM users ORDER BY points DESC LIMIT 1')
    return cursor.fetchone()

def set_custom_reply(trigger, response):
    cursor.execute('''
        INSERT OR REPLACE INTO custom_replies (trigger, response) VALUES (?, ?)
    ''', (trigger, response))
    conn.commit()

def get_custom_reply(trigger):
    cursor.execute('SELECT response FROM custom_replies WHERE trigger = ?', (trigger,))
    row = cursor.fetchone()
    return row[0] if row else None

def update_username(user_id, new_username):
    cursor.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
    old_username = cursor.fetchone()
    if old_username:
        cursor.execute('''
            INSERT OR REPLACE INTO username_history (user_id, old_username, new_username) VALUES (?, ?, ?)
        ''', (user_id, old_username[0], new_username))
        cursor.execute('UPDATE users SET username = ? WHERE user_id = ?', (new_username, user_id))
        conn.commit()
