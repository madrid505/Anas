import sqlite3

class BotDB:
    def __init__(self, db_file="bot_ton.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # جداول الرتب، الأقفال، الردود (مع دعم الميديا)، الإعدادات، والترحيب
        self.cursor.execute('CREATE TABLE IF NOT EXISTS ranks (gid TEXT, uid TEXT, rank TEXT)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS locks (gid TEXT, feature TEXT, status INTEGER DEFAULT 0)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS replies (gid TEXT, word TEXT, reply TEXT, media_id TEXT DEFAULT NULL)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS settings (gid TEXT, key TEXT, value TEXT)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS welcome (gid TEXT, msg TEXT)')
        self.conn.commit()

    def set_rank(self, gid, uid, rank):
        self.cursor.execute("INSERT OR REPLACE INTO ranks (gid, uid, rank) VALUES (?, ?, ?)", (str(gid), str(uid), rank))
        self.conn.commit()

    def get_rank(self, gid, uid):
        self.cursor.execute("SELECT rank FROM ranks WHERE gid=? AND uid=?", (str(gid), str(uid)))
        row = self.cursor.fetchone()
        return row[0] if row else "عضو"

    def toggle_lock(self, gid, feature, status):
        self.cursor.execute("INSERT OR REPLACE INTO locks (gid, feature, status) VALUES (?, ?, ?)", (str(gid), feature, status))
        self.conn.commit()

    def is_locked(self, gid, feature):
        self.cursor.execute("SELECT status FROM locks WHERE gid=? AND feature=?", (str(gid), feature))
        row = self.cursor.fetchone()
        return row[0] == 1 if row else False

    # حفظ الرد (نص أو ميديا)
    def set_reply(self, gid, word, reply_text, media_id=None):
        self.cursor.execute("INSERT OR REPLACE INTO replies (gid, word, reply, media_id) VALUES (?, ?, ?, ?)", 
                           (str(gid), word, reply_text, media_id))
        self.conn.commit()

    def delete_reply(self, gid, word):
        self.cursor.execute("DELETE FROM replies WHERE gid=? AND word=?", (str(gid), word))
        self.conn.commit()

    # جلب الرد بالكامل
    def get_reply_data(self, gid, word):
        self.cursor.execute("SELECT reply, media_id FROM replies WHERE gid=? AND word=?", (str(gid), word))
        return self.cursor.fetchone()

    def set_setting(self, gid, key, value):
        self.cursor.execute("INSERT OR REPLACE INTO settings (gid, key, value) VALUES (?, ?, ?)", (str(gid), key, value))
        self.conn.commit()

    def get_setting(self, gid, key):
        self.cursor.execute("SELECT value FROM settings WHERE gid=? AND key=?", (str(gid), key))
        row = self.cursor.fetchone()
        return row[0] if row else "off"

db = BotDB()
