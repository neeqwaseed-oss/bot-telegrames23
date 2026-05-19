# TCGIS - Data Processor Dockerfile
FROM python:3.11-slim

WORKDIR /app

# تثبيت التبعيات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY src/ ./src/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.data_processor.main"]
