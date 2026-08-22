"""
app/database/session.py
───────────────────────
Configura o engine assíncrono do SQLAlchemy e a fábrica de sessões.

Por que async?
  FastAPI é totalmente assíncrono. Usar asyncpg + AsyncSession evita
  bloqueio de threads e permite lidar com centenas de requisições simultâneas
  sem escalar horizontalmente de imediato.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# ── Engine principal ──────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,       # loga SQL em desenvolvimento
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,            # verifica conexão antes de reusar
)

# ── Fábrica de sessões ────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,        # evita lazy-load após commit
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependência FastAPI que fornece uma sessão de banco de dados.
    Garante rollback automático em caso de exceção e fechamento da sessão.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
