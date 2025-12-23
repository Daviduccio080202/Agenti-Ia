FROM python:3.11-bookworm

WORKDIR /app

# Aggiorniamo il sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# FORZIAMO LA REINSTALLAZIONE PULITA
# Usiamo --force-reinstall per essere sicuri che non usi versioni vecchie
RUN pip install --no-cache-dir --force-reinstall -r requirements.txt

COPY main.py .

# DEBUG: Stampiamo cosa è stato installato davvero (lo vedrai nei log)
RUN pip list | grep livekit

CMD ["python", "main.py", "start"]
