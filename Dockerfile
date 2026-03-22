FROM python:3.13-slim

# Impede a gravação de arquivos .pyc no disco
ENV PYTHONDONTWRITEBYTECODE=1
# Evita que o Python faça buffer do stdout/stderr
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala as dependências do sistema operacional (necessárias para o psycopg2)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências do Python
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o restante do código para o container
COPY . /app/
