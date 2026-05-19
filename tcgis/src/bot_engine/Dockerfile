# TCGIS - Bot Engine Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "-m", "src.bot_engine.main"]
