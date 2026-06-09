"""
app/main.py
───────────
Ponto de entrada da aplicação FastAPI da Wattiz.

Responsabilidades:
  1. Instanciar o app FastAPI com metadados (Swagger)
  2. Registrar middlewares (CORS, logging)
  3. Registrar todos os routers
  4. Criar tabelas no banco ao iniciar (dev) ou usar Alembic (prod)
  5. Expor health check
"""

import logging
import logging.config

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
    """
    Inicialização do servidor.
    Roda as migrations do Alembic automaticamente (dev e produção).
    """
    logger.info("🚀 Wattiz API v%s iniciando...", settings.APP_VERSION)

    # Roda migrations Alembic (cria/atualiza tabelas automaticamente)
    try:
        import subprocess
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            logger.info("✅ Migrations aplicadas com sucesso.")
        else:
            logger.warning("⚠️ Alembic stderr: %s", result.stderr[:300])
            # Fallback: cria tabelas diretamente se Alembic falhar
            from app.database.base import Base
            from app.database.session import engine
            from app.models import user, appliance, tariff, consumption, report  # noqa
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Tabelas criadas via SQLAlchemy (fallback).")
    except Exception as e:
        logger.error("❌ Erro ao rodar migrations: %s", e)
        # Fallback final: cria tabelas diretamente
        try:
            from app.database.base import Base
            from app.database.session import engine
            from app.models import user, appliance, tariff, consumption, report  # noqa
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Tabelas criadas via fallback SQLAlchemy.")
        except Exception as e2:
            logger.critical("❌ Falha crítica ao criar tabelas: %s", e2)

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
