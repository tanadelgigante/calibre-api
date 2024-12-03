# Usa un'immagine base Python slim
FROM python:3.9-slim AS builder

# Imposta variabili ambiente per Poetry
ENV POETRY_VERSION=1.5.1 \
    POETRY_HOME=/opt/poetry \
    POETRY_VENV=/opt/poetry-venv \
    POETRY_CACHE_DIR=/opt/.cache

# Installa dipendenze di sistema e Poetry
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Installa Poetry in un ambiente virtuale
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==$POETRY_VERSION

# Aggiungi Poetry al PATH
ENV PATH="${POETRY_VENV}/bin:${PATH}"

# Imposta directory di lavoro
WORKDIR /app

# Copia solo i file necessari per installare dipendenze
COPY pyproject.toml poetry.lock* ./

# Configurazione ambiente di produzione
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# Fase finale: copia codice applicazione
COPY app/ .

# Esponi porta applicazione
EXPOSE 8000

# Comando di avvio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
