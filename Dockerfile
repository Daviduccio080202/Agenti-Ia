FROM python:3.11-bookworm

WORKDIR /app

# Aggiorniamo il sistema (Evita errori di librerie mancanti)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Comando di avvio
CMD ["python", "main.py", "start"]