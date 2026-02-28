# database.py
import sqlite3
from config import DATABASE_FILE

def get_connection():
    return sqlite3.connect(DATABASE_FILE)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # جدول نقاط التفاعل
    c.execute('''CREATE TABLE IF NOT EXISTS points (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT,
                    points INTEGER DEFAULT 0
                 )''')
    # جدول الاسماء القديمة والجديدة
    c.execute('''CREATE TABLE IF NOT EXISTS names (
                    user_id INTEGER PRIMARY KEY,
                    old_name TEXT,
                    new_name TEXT
                 )''')
    conn.commit()
    conn.close()
