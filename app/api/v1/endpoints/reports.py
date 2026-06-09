"""
app/api/v1/endpoints/reports.py
─────────────────────────────────
Endpoints de relatórios mensais.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.report import ReportGenerateRequest, ReportResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Relatórios"])


@router.post(
    "/generate",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gerar relatório mensal",
)
async def generate_report(
    req: ReportGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    report = await ReportService(db).generate(current_user.id, req)
    return ReportResponse.model_validate(report)


@router.get(
    "/",
    response_model=list[ReportResponse],
    summary="Listar relatórios do usuário",
)
async def list_reports(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ReportResponse]:
    reports = await ReportService(db).list_reports(current_user.id)
    return [ReportResponse.model_validate(r) for r in reports]


@router.get(
    "/period",
    response_model=ReportResponse,
    summary="Buscar relatório por período",
)
async def get_report_by_period(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    report = await ReportService(db).get_report(current_user.id, month, year)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relatório não encontrado.")
    return ReportResponse.model_validate(report)
