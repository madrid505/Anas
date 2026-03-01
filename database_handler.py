import sqlite3

class Database:
    def __init__(self, db_name="bot_database.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # جدول الردود
        self.cursor.execute('CREATE TABLE IF NOT EXISTS replies (gid TEXT, word TEXT, reply TEXT)')
        # جدول الترحيب
        self.cursor.execute('CREATE TABLE IF NOT EXISTS welcome (gid TEXT, msg TEXT)')
        # جدول مراقبة الأسماء
        self.cursor.execute('CREATE TABLE IF NOT EXISTS users (uid TEXT, name TEXT, username TEXT)')
        # جدول الإنذارات
        self.cursor.execute('CREATE TABLE IF NOT EXISTS warns (uid TEXT, gid TEXT, count INTEGER DEFAULT 0)')
        # جدول إعدادات القفل (الروابط، الصور، إلخ)
        self.cursor.execute('CREATE TABLE IF NOT EXISTS settings (gid TEXT, feature TEXT, status TEXT DEFAULT "open")')
        self.conn.commit()

    def set_welcome(self, gid, msg):
        self.cursor.execute("INSERT OR REPLACE INTO welcome VALUES (?, ?)", (str(gid), msg))
        self.conn.commit()

    def get_welcome(self, gid):
        self.cursor.execute("SELECT msg FROM welcome WHERE gid=?", (str(gid),))
        row = self.fetchone()
        return row[0] if row else None

    # دوال إضافية للردود والتحذيرات يتم استدعاؤها في main.py
