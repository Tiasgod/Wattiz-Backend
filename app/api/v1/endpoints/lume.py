"""
app/api/v1/endpoints/lume.py
─────────────────────────────
Endpoints da IA Lume — chatbot e geração de insights energéticos.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.ia.lume_service import LumeService
from app.models.user import User
from app.schemas.lume import (
    LumeChatRequest,
    LumeChatResponse,
    LumeInsightRequest,
    LumeInsightResponse,
)
from app.services.lume_orchestrator import LumeOrchestrator

router = APIRouter(prefix="/lume", tags=["IA Lume"])


@router.post(
    "/chat",
    response_model=LumeChatResponse,
    summary="Conversar com a Lume",
    description=(
        "Envia uma mensagem para a IA Lume. "
        "A Lume recebe automaticamente os dados energéticos do usuário como contexto, "
        "garantindo que as respostas sejam baseadas em dados reais."
    ),
)
async def chat_with_lume(
    req: LumeChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LumeChatResponse:
    """
    Fluxo:
    1. Calcula analytics do usuário
    2. Injeta contexto no prompt
    3. Lume responde com base nos dados reais
    """
    return await LumeOrchestrator(db).chat(current_user.id, req)


@router.post(
    "/insights",
    response_model=LumeInsightResponse,
    summary="Gerar insights mensais com IA",
)
async def generate_insights(
    req: LumeInsightRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> LumeInsightResponse:
    return await LumeOrchestrator(db).generate_insights(
        current_user.id, req.reference_month, req.reference_year
    )


@router.get(
    "/health",
    summary="Status do serviço Ollama",
    description="Verifica se o Ollama está online e o modelo llama3 disponível.",
)
async def lume_health(
    _: User = Depends(get_current_active_user),
) -> dict:
    return await LumeService().health_check()
