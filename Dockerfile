FROM python:3.11-bookworm

WORKDIR /app

# Installiamo build-essential (serve per compilare alcune dipendenze)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Installazione pulita senza usare la cache vecchia
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Avvio
CMD ["python", "main.py", "start"]
