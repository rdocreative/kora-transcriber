# Usar uma imagem oficial do Python como base
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema (ffmpeg)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copiar dependências
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
COPY main.py .

# Expor porta (não importa, só documentação)
EXPOSE 8080

# Iniciar app usando porta dinâmica do Cloud Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]
