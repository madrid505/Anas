import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# جدول الرسائل (لنظام ملك التفاعل)
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    group_id INTEGER,
    user_id INTEGER,
    count INTEGER DEFAULT 0,
    PRIMARY KEY (group_id, user_id)
)
""")

# جدول الرتب
cursor.execute("""
CREATE TABLE IF NOT EXISTS ranks (
    group_id INTEGER,
    user_id INTEGER,
    rank TEXT,
    PRIMARY KEY (group_id, user_id)
)
""")

# جدول الردود
cursor.execute("""
CREATE TABLE IF NOT EXISTS replies (
    group_id INTEGER,
    trigger TEXT,
    response TEXT,
    PRIMARY KEY (group_id, trigger)
)
""")

conn.commit()
