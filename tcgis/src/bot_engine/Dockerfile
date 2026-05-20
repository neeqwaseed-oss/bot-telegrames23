# TCGIS - Bot Engine Dockerfile
FROM python:3.11-slim

WORKDIR /app

# تثبيت أدوات النظام اللازمة
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# تحديث pip وتثبيت wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# نسخ ملف المتطلبات من مجلد tcgis
COPY tcgis/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ محتويات src مباشرة إلى /app ليكون bot_engine في الجذر
COPY tcgis/src/ .

# إضافة /app إلى PYTHONPATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# تشغيل البوت
CMD ["python", "-m", "bot_engine.main"]
