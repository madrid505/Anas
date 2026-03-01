import sqlite3
import logging
from contextlib import closing

# سنفترض أن DATABASE_FILE مستورد من ملف الإعدادات أو نضعه هنا كافتراضي
DATABASE_FILE = "bot_data.db"

# إعداد السجلات لمراقبة أخطاء القاعدة
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """تهيئة الجداول الأساسية للبوت"""
    try:
        with closing(sqlite3.connect(DATABASE_FILE)) as conn:
            with conn:
                # جدول النقاط والمستخدمين
                conn.execute("""
                CREATE TABLE IF NOT EXISTS user_points (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    points INTEGER DEFAULT 0
                )
                """)
                # جدول سجل الرسائل (للتحليل المستقبلي)
                conn.execute("""
                CREATE TABLE IF NOT EXISTS messages_log (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """)
                # جدول الردود التلقائية المخصصة
                conn.execute("""
                CREATE TABLE IF NOT EXISTS custom_replies (
                    keyword TEXT PRIMARY KEY,
                    reply TEXT
                )
                """)
        logger.info("✅ تم تهيئة قاعدة البيانات بنجاح.")
    except Exception as e:
        logger.error(f"❌ خطأ أثناء تهيئة القاعدة: {e}")

def add_point(user_id, username, points=1):
    """إضافة نقاط وتحديث اسم المستخدم"""
    try:
        with closing(sqlite3.connect(DATABASE_FILE)) as conn:
            with conn:
                conn.execute("""
                INSERT INTO user_points (user_id, username, points) 
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET 
                points = points + excluded.points,
                username = excluded.username
                """, (user_id, username, points))
    except Exception as e:
        logger.error(f"❌ خطأ في add_point: {e}")

def get_points(user_id):
    """الحصول على نقاط مستخدم محدد"""
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        cur = conn.execute("SELECT points FROM user_points WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        return row[0] if row else 0

def get_top_users(limit=10):
    """جلب قائمة بأكثر المستخدمين تفاعلاً"""
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        cur = conn.execute("SELECT username, points FROM user_points ORDER BY points DESC LIMIT ?", (limit,))
        return cur.fetchall()

def log_message(user_id, chat_id):
    """تسجيل نشاط الرسائل"""
    try:
        with closing(sqlite3.connect(DATABASE_FILE)) as conn:
            with conn:
                conn.execute("INSERT INTO messages_log (user_id, chat_id) VALUES (?, ?)", (user_id, chat_id))
    except Exception as e:
        logger.error(f"❌ خطأ في log_message: {e}")

def add_reply(keyword, reply):
    """إضافة أو تحديث رد مخصص"""
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        with conn:
            conn.execute("INSERT OR REPLACE INTO custom_replies (keyword, reply) VALUES (?, ?)", (keyword.lower(), reply))

def get_reply(keyword):
    """البحث عن رد مخصص للكلمة المفتاحية"""
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        cur = conn.execute("SELECT reply FROM custom_replies WHERE keyword=?", (keyword.lower(),))
        row = cur.fetchone()
        return row[0] if row else None

def delete_reply(keyword):
    """حذف رد مخصص"""
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        with conn:
            conn.execute("DELETE FROM custom_replies WHERE keyword=?", (keyword.lower(),))
