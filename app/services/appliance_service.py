"""
app/services/appliance_service.py
──────────────────────────────────
Serviço de eletrodomésticos — CRUD + cálculo de consumo.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.energy_engine import calculate_cost, calculate_kwh
from app.core.config import settings
from app.models.appliance import Appliance
from app.schemas.appliance import ApplianceCreate, ApplianceResponse, ApplianceUpdate
from app.services.tariff_service import TariffService


class ApplianceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: uuid.UUID, data: ApplianceCreate) -> Appliance:
        appliance = Appliance(
            user_id=user_id,
            name=data.name,
            power_watts=data.power_watts,
            hours_per_day=data.hours_per_day,
            days_per_month=data.days_per_month,
            category=data.category,
        )
        self.db.add(appliance)
        await self.db.flush()
        await self.db.refresh(appliance)
        return appliance

    async def list_user_appliances(self, user_id: uuid.UUID) -> list[Appliance]:
        result = await self.db.execute(
            select(Appliance).where(Appliance.user_id == user_id).order_by(Appliance.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, appliance_id: uuid.UUID, user_id: uuid.UUID) -> Appliance | None:
        result = await self.db.execute(
            select(Appliance).where(
                Appliance.id == appliance_id,
                Appliance.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def update(
        self, appliance: Appliance, data: ApplianceUpdate
    ) -> Appliance:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(appliance, field, value)
        await self.db.flush()
        await self.db.refresh(appliance)
        return appliance

    async def delete(self, appliance: Appliance) -> None:
        await self.db.delete(appliance)
        await self.db.flush()

    async def enrich_with_calculations(
        self, appliance: Appliance, user_id: uuid.UUID
    ) -> ApplianceResponse:
        """Enriquece o schema de resposta com kWh e custo calculados."""
        tariff = await TariffService(self.db).get_active_tariff_value(user_id)
        kwh = calculate_kwh(appliance.power_watts, appliance.hours_per_day, appliance.days_per_month)
        cost = calculate_cost(kwh, tariff)

        resp = ApplianceResponse.model_validate(appliance)
        resp.kwh_per_month = kwh
        resp.estimated_cost = cost
        return resp

    async def enrich_list(
        self, appliances: list[Appliance], user_id: uuid.UUID
    ) -> list[ApplianceResponse]:
        tariff = await TariffService(self.db).get_active_tariff_value(user_id)
        result = []
        for ap in appliances:
            kwh = calculate_kwh(ap.power_watts, ap.hours_per_day, ap.days_per_month)
            cost = calculate_cost(kwh, tariff)
            resp = ApplianceResponse.model_validate(ap)
            resp.kwh_per_month = kwh
            resp.estimated_cost = cost
            result.append(resp)
        return result
