"""
app/services/tariff_service.py
───────────────────────────────
Serviço de tarifas energéticas.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.tariff import Tariff
from app.schemas.tariff import TariffCreate


class TariffService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: uuid.UUID, data: TariffCreate) -> Tariff:
        """Cria nova tarifa e desativa as anteriores."""
        # Desativa tarifas anteriores
        existing = await self.list_user_tariffs(user_id)
        for t in existing:
            t.is_active = False

        tariff = Tariff(
            user_id=user_id,
            kwh_price=data.kwh_price,
            distributor=data.distributor,
            state=data.state,
            is_active=True,
        )
        self.db.add(tariff)
        await self.db.flush()
        await self.db.refresh(tariff)
        return tariff

    async def list_user_tariffs(self, user_id: uuid.UUID) -> list[Tariff]:
        result = await self.db.execute(
            select(Tariff)
            .where(Tariff.user_id == user_id)
            .order_by(Tariff.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_tariff(self, user_id: uuid.UUID) -> Tariff | None:
        result = await self.db.execute(
            select(Tariff).where(
                Tariff.user_id == user_id,
                Tariff.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def get_active_tariff_value(self, user_id: uuid.UUID) -> float:
        """Retorna o valor da tarifa ativa ou o padrão configurado."""
        tariff = await self.get_active_tariff(user_id)
        return tariff.kwh_price if tariff else settings.DEFAULT_TARIFF
