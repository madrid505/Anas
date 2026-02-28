# Dockerfile
FROM python:3.11-slim

# مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ الملفات
COPY . /app

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

# تعريف المتغيرات البيئية الافتراضية (يمكن تعديلها في Northflank)
ENV TOKEN=""
ENV OWNER_ID="5010882230"

# الأمر الأساسي لتشغيل البوت
CMD ["python3", "main.py"]
