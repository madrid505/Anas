# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# نسخ الملفات
COPY . /app

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

# تعيين الأمر الافتراضي لتشغيل البوت
CMD ["python3", "main.py"]
