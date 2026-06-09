"""
app/api/v1/endpoints/dashboard.py
───────────────────────────────────
Endpoint do dashboard energético.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/",
    response_model=DashboardResponse,
    summary="Dashboard energético completo",
    description=(
        "Retorna consumo total, custo estimado, maiores consumidores, "
        "breakdown por categoria, comparação mensal e insights automáticos."
    ),
)
async def get_dashboard(
    month: int | None = Query(None, ge=1, le=12, description="Mês de referência (1-12)"),
    year: int | None = Query(None, ge=2020, description="Ano de referência"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    return await DashboardService(db).get_dashboard(current_user.id, month, year)
