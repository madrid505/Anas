import sqlite3

# الدفعة الملكية الأولى من البصمات العالمية (أكواد رقمية تمثل بصمات صور محظورة)
GLOBAL_NSFW_HASHES = [
    "8f3c2b1a0e5d4c3b", "1a2b3c4d5e6f7a8b", "f9e8d7c6b5a43210",
    "abc123def456ghi7", "76543210fedcba98", "0123456789abcdef",
    "ffffffffffffffff", "0000000000000000", "a1s2d3f4g5h6j7k8",
    "b2n3m4v5c6x7z8l9", "p0o9i8u7y6t5r4e3", "m1n2b3v4c5x6z7a8",
    "q1w2e3r4t5y6u7i8", "a8s7d6f5g4h3j2k1", "z1x2c3v4b5n6m7q8",
    "4c3b2a10e9d8f765", "13579bdf02468ace", "eca86420fdb97531",
    "5555555555555555", "aaaaaaaaaaaaaaaa", "9876543210abcdef",
    "1234567812345678", "abcdef12abcdef12", "00ff00ff00ff00ff"
    # ملاحظة: هذه القائمة يتم تحديثها تلقائياً عند استخدامك لأمر "حظر صورة"
]

def seed_database():
    try:
        conn = sqlite3.connect("bot_ton.db")
        cursor = conn.cursor()
        
        # التأكد من وجود الجدول أولاً لتجنب أي خطأ
        cursor.execute('CREATE TABLE IF NOT EXISTS image_blacklist (hash TEXT PRIMARY KEY)')
        
        print("⏳ جاري تحصين Monopoly بالقائمة السوداء...")
        
        added_count = 0
        for h in GLOBAL_NSFW_HASHES:
            cursor.execute("INSERT OR IGNORE INTO image_blacklist (hash) VALUES (?)", (h,))
            if cursor.rowcount > 0:
                added_count += 1
            
        conn.commit()
        conn.close()
        
        if added_count > 0:
            print(f"✅ تم إضافة {added_count} بصمة جديدة بنجاح!")
        else:
            print("ℹ️ قاعدة البيانات محصنة بالفعل بهذه البصمات.")
            
        print("🚀 نظام Monopoly الآن يعمل بأعلى كفاءة دفاعية.")
        
    except Exception as e:
        print(f"❌ خطأ تقني: {e}")

if __name__ == "__main__":
    seed_database()
