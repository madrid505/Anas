import sqlite3

class BotDB:
    def __init__(self, db_file="bot_ton.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('CREATE TABLE IF NOT EXISTS ranks (gid TEXT, uid TEXT, rank TEXT)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS locks (gid TEXT, feature TEXT, status INTEGER DEFAULT 0)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS replies (gid TEXT, word TEXT, reply TEXT, media_id TEXT DEFAULT NULL)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS settings (gid TEXT, key TEXT, value TEXT)')
        # جدول التفاعل الجديد
        self.cursor.execute('CREATE TABLE IF NOT EXISTS activity (gid TEXT, uid TEXT, count INTEGER DEFAULT 0, PRIMARY KEY(gid, uid))')
        self.conn.commit()

    # --- وظائف التفاعل والمشاركات ---
    def increase_messages(self, gid, uid):
        self.cursor.execute("INSERT OR IGNORE INTO activity (gid, uid, count) VALUES (?, ?, 0)", (str(gid), str(uid)))
        self.cursor.execute("UPDATE activity SET count = count + 1 WHERE gid=? AND uid=?", (str(gid), str(uid)))
        self.conn.commit()

    def get_user_messages(self, gid, uid):
        self.cursor.execute("SELECT count FROM activity WHERE gid=? AND uid=?", (str(gid), str(uid)))
        row = self.cursor.fetchone()
        return row[0] if row else 0

    def get_top_active(self, gid, limit=5):
        self.cursor.execute("SELECT uid, count FROM activity WHERE gid=? ORDER BY count DESC LIMIT ?", (str(gid), limit))
        return self.cursor.fetchall()

    # --- وظيفة كشف المحظورين (عالمياً) ---
    def is_globally_banned(self, uid):
        # يبحث إذا كان الشخص مطروداً في أي جروب مسجل في قاعدة البيانات
        self.cursor.execute("SELECT 1 FROM ranks WHERE uid=? AND rank='مطرود' LIMIT 1", (str(uid),))
        return self.cursor.fetchone() is not None

    # --- الوظائف الأساسية السابقة ---
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

    def set_reply(self, gid, word, reply_text, media_id=None):
        self.cursor.execute("INSERT OR REPLACE INTO replies (gid, word, reply, media_id) VALUES (?, ?, ?, ?)", (str(gid), word, reply_text, str(media_id) if media_id else None))
        self.conn.commit()

    def delete_reply(self, gid, word):
        self.cursor.execute("DELETE FROM replies WHERE gid=? AND word=?", (str(gid), word))
        self.conn.commit()

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
