import sqlite3

class BotDB:
    def __init__(self, db_file="bot_ton.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # الرتب
        self.cursor.execute('CREATE TABLE IF NOT EXISTS ranks (gid TEXT, uid TEXT, rank TEXT)')
        # الأقفال
        self.cursor.execute('CREATE TABLE IF NOT EXISTS locks (gid TEXT, feature TEXT, status INTEGER DEFAULT 0)')
        # الترحيب والردود
        self.cursor.execute('CREATE TABLE IF NOT EXISTS settings (gid TEXT, key TEXT, value TEXT)')
        self.conn.commit()

    def set_rank(self, gid, uid, rank):
        self.cursor.execute("INSERT OR REPLACE INTO ranks VALUES (?, ?, ?)", (str(gid), str(uid), rank))
        self.conn.commit()

    def get_rank(self, gid, uid):
        self.cursor.execute("SELECT rank FROM ranks WHERE gid=? AND uid=?", (str(gid), str(uid)))
        row = self.cursor.fetchone()
        return row[0] if row else "عضو"

    def toggle_lock(self, gid, feature, status):
        self.cursor.execute("INSERT OR REPLACE INTO locks VALUES (?, ?, ?)", (str(gid), feature, status))
        self.conn.commit()

    def is_locked(self, gid, feature):
        self.cursor.execute("SELECT status FROM locks WHERE gid=? AND feature=?", (str(gid), feature))
        row = self.cursor.fetchone()
        return row[0] == 1 if row else False

db = BotDB()
