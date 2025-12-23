FROM python:3.11-bookworm

WORKDIR /app

# Installiamo build-essential
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# --- TRUCCO ANTI-CACHE ---
# Ho aggiunto --upgrade e --force-reinstall.
# Cambiando il testo di questo comando, Docker è OBBLIGATO a eseguirlo di nuovo
# ignorando la cache vecchia di EasyPanel.
RUN pip install --no-cache-dir --upgrade --force-reinstall -r requirements.txt

COPY main.py .

# Comando di avvio (start è corretto per la produzione)
CMD ["python", "main.py", "start"]
