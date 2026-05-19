# TCGIS - API Gateway Dockerfile
FROM python:3.11-slim

WORKDIR /app

# تثبيت التبعيات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY src/ ./src/

# المتغيرات البيئية
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# المنفذ
EXPOSE 8000

# الأمر
CMD ["uvicorn", "src.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
