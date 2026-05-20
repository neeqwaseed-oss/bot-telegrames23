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

# نسخ الملفات من مجلد tcgis
COPY tcgis/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كامل محتويات src إلى /app/src
COPY tcgis/src/ /app/src/

# إضافة /app/src إلى PYTHONPATH
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# تشغيل البوت باستخدام المسار الكامل للوحدة
CMD ["python", "-m", "bot_engine.main"]
