FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# NÃO usar EXPOSE 8000 (opcional, mas irrelevante)
EXPOSE 8080

# Usar a porta passada pelo Cloud Run
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
