# Ambiente da API: instala as dependências declaradas e executa o servidor sem usuário root.
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /usr/sbin/nologin sinalyx

# Copia também os arquivos referenciados pelo requirements principal.
COPY requirements.txt requirements-dev.txt requirements-runtime.txt requirements-optional-pfsense.txt ./
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt

COPY src ./src
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations
COPY scripts ./scripts
RUN mkdir -p /app/data/raw /app/data/processed /app/data/models /app/data/runtime \
    && chown -R sinalyx:sinalyx /app

EXPOSE 8000

USER sinalyx

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
