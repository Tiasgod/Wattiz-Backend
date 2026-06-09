"""
app/main.py
───────────
Ponto de entrada da aplicação FastAPI da Wattiz.
"""

import asyncio
import logging
import logging.config

import sqlalchemy as sa
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.middleware.logging import RequestLoggingMiddleware

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.APP_DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("wattiz")


# ── Metadados da API (Swagger) ────────────────────────────────────────────────
tags_metadata = [
    {"name": "Autenticação", "description": "Registro, login e refresh de tokens JWT."},
    {"name": "Usuários", "description": "Gerenciamento de perfil."},
    {"name": "Eletrodomésticos", "description": "Cadastro e cálculo de consumo dos aparelhos."},
    {"name": "Tarifas", "description": "Configuração da tarifa energética regional."},
    {"name": "Dashboard", "description": "Painel completo de consumo e custo."},
    {"name": "Relatórios", "description": "Relatórios mensais com resumo e insights."},
    {"name": "IA Lume", "description": "Assistente energética inteligente."},
    {"name": "IoT (Em breve)", "description": "Integração com dispositivos inteligentes."},
]

app = FastAPI(
    title="Wattiz API",
    description=(
        "## 💡 Wattiz — Plataforma de Inteligência Energética\n\n"
        "Backend completo para monitoramento, análise e economia de energia elétrica.\n\n"
        "**IA Lume**: assistente energética baseada em LLM (Ollama/llama3).\n\n"
        "Todos os endpoints requerem autenticação via JWT, exceto `/auth/register` e `/auth/login`."
    ),
    version=settings.APP_VERSION,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middlewares ───────────────────────────────────────────────────────────────
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(api_router)


# ── Startup / Shutdown ────────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup() -> None:
    logger.info("🚀 Wattiz API v%s iniciando...", settings.APP_VERSION)

    from app.database.session import engine
    from app.database.base import Base
    from app.models import user, appliance, tariff, consumption, report  # noqa

    # Aguarda o banco ficar pronto (até 30 segundos)
    for attempt in range(10):
        try:
            async with engine.begin() as conn:
                await conn.execute(sa.text("SELECT 1"))
            logger.info("✅ Banco de dados conectado!")
            break
        except Exception as e:
            logger.warning("⏳ Aguardando banco... tentativa %d/10: %s", attempt + 1, e)
            await asyncio.sleep(3)
    else:
        logger.critical("❌ Banco de dados não respondeu após 10 tentativas.")
        return

    # Cria tabelas
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Tabelas criadas/verificadas com sucesso.")
    except Exception as e:
        logger.error("❌ Erro ao criar tabelas: %s", e)

    logger.info("📡 Banco de dados: conectado")
    logger.info("🤖 Ollama: %s (modelo: %s)", settings.OLLAMA_BASE_URL, settings.OLLAMA_MODEL)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("🛑 Wattiz API encerrando...")
    from app.database.session import engine
    await engine.dispose()


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Sistema"], summary="Health check")
async def health() -> dict:
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


@app.get("/", tags=["Sistema"], include_in_schema=False)
async def root() -> dict:
    return {"message": "Wattiz API — acesse /docs para a documentação."}
