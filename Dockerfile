# ── Estágio de build ──────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Instalar dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Estágio de produção ───────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.local/bin:$PATH"

# Copiar dependências instaladas
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar código
COPY . .

# Criar usuário não-root (segurança)
RUN addgroup --system wattiz && \
    adduser --system --ingroup wattiz wattiz && \
    chown -R wattiz:wattiz /app

USER wattiz

EXPOSE 8000

# Healthcheck do container
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
