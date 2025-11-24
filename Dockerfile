# Usar uma imagem oficial do Python como base
FROM python:3.11-slim

# Definir o diretório de trabalho no contêiner
WORKDIR /app

# Instalar dependências do sistema (ffmpeg)
# Atualiza a lista de pacotes e instala o ffmpeg sem cache
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copiar o arquivo de dependências para o contêiner
COPY requirements.txt .

# Instalar as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código da aplicação
COPY main.py .

# Expor a porta em que o app irá rodar
EXPOSE 8000

# Definir o comando para rodar a aplicação
# Usar 0.0.0.0 para torná-lo acessível de fora do contêiner
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]