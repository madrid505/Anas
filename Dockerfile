# استخدام نسخة بايثون مستقرة وخفيفة
FROM python:3.11-slim

# منع بايثون من إنشاء ملفات .pyc وتفعيل الخرج المباشر للسجلات (Logging)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# تحديد مسار العمل
WORKDIR /app

# تثبيت أدوات النظام الضرورية (مثل gcc و libsqlite3 لضمان عمل قاعدة البيانات)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# خطوة ذكية: نسخ ملف المتطلبات أولاً لتسريع البناء مستقبلاً
COPY requirements.txt .

# تثبيت المكتبات البرمجية
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# الآن نسخ باقي ملفات المشروع (الكود، الصور، الإعدادات)
COPY . .

# تعيين الأمر الافتراضي لتشغيل البوت
# استخدمنا python مباشرة لضمان التوافق مع الصور المبنية على slim
CMD ["python", "main.py"]
