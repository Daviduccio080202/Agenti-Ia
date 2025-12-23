FROM python:3.11-bookworm

WORKDIR /app

# Aggiorniamo il sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# --- IL TRUCCO ---
# Questa riga forza il sistema a ignorare la cache e reinstallare tutto
RUN echo "Forcing Update v3" 
RUN pip install --no-cache-dir --upgrade -r requirements.txt
# -----------------

COPY main.py .

CMD ["python", "main.py", "start"]
