"""
app/api/v1/endpoints/appliances.py
────────────────────────────────────
CRUD completo de eletrodomésticos com cálculo de consumo embutido.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.appliance import ApplianceCreate, ApplianceResponse, ApplianceUpdate
from app.services.appliance_service import ApplianceService

router = APIRouter(prefix="/appliances", tags=["Eletrodomésticos"])


@router.post(
    "/",
    response_model=ApplianceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar eletrodoméstico",
)
async def create_appliance(
    data: ApplianceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplianceResponse:
    service = ApplianceService(db)
    appliance = await service.create(current_user.id, data)
    return await service.enrich_with_calculations(appliance, current_user.id)


@router.get(
    "/",
    response_model=list[ApplianceResponse],
    summary="Listar todos os eletrodomésticos",
)
async def list_appliances(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ApplianceResponse]:
    service = ApplianceService(db)
    appliances = await service.list_user_appliances(current_user.id)
    return await service.enrich_list(appliances, current_user.id)


@router.get(
    "/{appliance_id}",
    response_model=ApplianceResponse,
    summary="Detalhe de um eletrodoméstico",
)
async def get_appliance(
    appliance_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplianceResponse:
    service = ApplianceService(db)
    appliance = await service.get_by_id(appliance_id, current_user.id)
    if not appliance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Eletrodoméstico não encontrado.")
    return await service.enrich_with_calculations(appliance, current_user.id)


@router.patch(
    "/{appliance_id}",
    response_model=ApplianceResponse,
    summary="Atualizar eletrodoméstico",
)
async def update_appliance(
    appliance_id: uuid.UUID,
    data: ApplianceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplianceResponse:
    service = ApplianceService(db)
    appliance = await service.get_by_id(appliance_id, current_user.id)
    if not appliance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Eletrodoméstico não encontrado.")
    updated = await service.update(appliance, data)
    return await service.enrich_with_calculations(updated, current_user.id)


@router.delete(
    "/{appliance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover eletrodoméstico",
)
async def delete_appliance(
    appliance_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = ApplianceService(db)
    appliance = await service.get_by_id(appliance_id, current_user.id)
    if not appliance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Eletrodoméstico não encontrado.")
    await service.delete(appliance)
