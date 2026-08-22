"""
app/api/v1/endpoints/tariffs.py
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.tariff import TariffCreate, TariffResponse
from app.services.tariff_service import TariffService

router = APIRouter(prefix="/tariffs", tags=["Tarifas"])


@router.post("/", response_model=TariffResponse, status_code=status.HTTP_201_CREATED,
             summary="Cadastrar tarifa energética")
async def create_tariff(
    data: TariffCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TariffResponse:
    tariff = await TariffService(db).create(current_user.id, data)
    return TariffResponse.model_validate(tariff)


@router.get("/", response_model=list[TariffResponse], summary="Listar tarifas do usuário")
async def list_tariffs(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[TariffResponse]:
    tariffs = await TariffService(db).list_user_tariffs(current_user.id)
    return [TariffResponse.model_validate(t) for t in tariffs]


@router.get("/active", response_model=TariffResponse | None, summary="Tarifa ativa atual")
async def get_active_tariff(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TariffResponse | None:
    tariff = await TariffService(db).get_active_tariff(current_user.id)
    return TariffResponse.model_validate(tariff) if tariff else None
