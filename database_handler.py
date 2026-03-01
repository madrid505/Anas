import sqlite3

class Database:
    def __init__(self, db_name="bot_database.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.setup()

    def setup(self):
        # جدول الرتب (منشئ، مدير، مميز)
        self.cursor.execute('CREATE TABLE IF NOT EXISTS ranks (gid TEXT, uid TEXT, rank TEXT)')
        # جدول الإعدادات (قفل الروابط، الصور، الخ)
        self.cursor.execute('CREATE TABLE IF NOT EXISTS settings (gid TEXT, feature TEXT, status TEXT DEFAULT "open")')
        # جدول الردود والترحيب
        self.cursor.execute('CREATE TABLE IF NOT EXISTS replies (gid TEXT, word TEXT, reply TEXT)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS welcome (gid TEXT, msg TEXT)')
        self.conn.commit()

    def set_rank(self, gid, uid, rank):
        self.cursor.execute("INSERT OR REPLACE INTO ranks VALUES (?, ?, ?)", (str(gid), str(uid), rank))
        self.conn.commit()

    def get_rank(self, gid, uid):
        self.cursor.execute("SELECT rank FROM ranks WHERE gid=? AND uid=?", (str(gid), str(uid)))
        row = self.cursor.fetchone()
        return row[0] if row else "عضو"

    def set_setting(self, gid, feature, status):
        self.cursor.execute("INSERT OR REPLACE INTO settings VALUES (?, ?, ?)", (str(gid), feature, status))
        self.conn.commit()

    def get_setting(self, gid, feature):
        self.cursor.execute("SELECT status FROM settings WHERE gid=? AND feature=?", (str(gid), feature))
        row = self.cursor.fetchone()
        return row[0] if row else "open"
