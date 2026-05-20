# TCGIS - Bot Engine Dockerfile
FROM python:3.11-slim

WORKDIR /app

# تثبيت أدوات البناء اللازمة لبعض المكتبات مثل fasttext
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# نسخ الملفات من مجلد tcgis
COPY tcgis/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY tcgis/src/ ./src/

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "-m", "bot_engine.main"]
