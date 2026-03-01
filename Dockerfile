FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir telethon
CMD ["python", "main.py"]
