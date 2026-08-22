"""
app/services/dashboard_service.py
───────────────────────────────────
Serviço de dashboard — orquestra analytics e prepara dados para o frontend.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.energy_engine import EnergyEngine
from app.models.appliance import Appliance
from app.models.consumption import ConsumptionRecord
from app.schemas.dashboard import (
    ApplianceRanking,
    CategoryBreakdown,
    DashboardResponse,
    MonthlyComparison,
)
from app.services.tariff_service import TariffService


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_dashboard(
        self,
        user_id: uuid.UUID,
        month: int | None = None,
        year: int | None = None,
    ) -> DashboardResponse:
        """
        Constrói o dashboard completo para o usuário.

        Se mês/ano não informados, usa o período atual.
        """
        now = datetime.now(timezone.utc)
        ref_month = month or now.month
        ref_year = year or now.year

        # ── 1. Tarifa ativa ───────────────────────────────────────────────────
        tariff_service = TariffService(self.db)
        tariff_value = await tariff_service.get_active_tariff_value(user_id)

        # ── 2. Aparelhos do usuário ───────────────────────────────────────────
        result = await self.db.execute(
            select(Appliance).where(Appliance.user_id == user_id)
        )
        appliances = list(result.scalars().all())

        # ── 3. Análise energética ─────────────────────────────────────────────
        engine = EnergyEngine(tariff=tariff_value)
        report = engine.analyze(appliances)

        # ── 4. Dados do mês anterior para comparação ──────────────────────────
        prev_month = ref_month - 1 if ref_month > 1 else 12
        prev_year = ref_year if ref_month > 1 else ref_year - 1
        prev_kwh, prev_cost = await self._get_historical_totals(user_id, prev_month, prev_year)

        variation = engine.compare_months(report.total_kwh, prev_kwh)

        # ── 5. Montar schemas de resposta ─────────────────────────────────────
        top_appliances = [
            ApplianceRanking(
                appliance_id=a.appliance_id,
                name=a.name,
                category=a.category,
                kwh_per_month=a.kwh_per_month,
                estimated_cost=a.estimated_cost,
                percentage_of_total=a.percentage_of_total,
            )
            for a in report.appliances[:5]  # top 5
        ]

        categories = [
            CategoryBreakdown(
                category=c.category,
                kwh=c.kwh,
                percentage=c.percentage,
                estimated_cost=c.estimated_cost,
            )
            for c in report.categories
        ]

        monthly = MonthlyComparison(
            current_month=ref_month,
            current_year=ref_year,
            current_kwh=report.total_kwh,
            current_cost=report.total_cost,
            previous_kwh=prev_kwh,
            previous_cost=prev_cost,
            variation_percentage=variation,
        )

        return DashboardResponse(
            total_kwh=report.total_kwh,
            total_cost=report.total_cost,
            active_tariff=tariff_value,
            highest_consumer=top_appliances[0] if top_appliances else None,
            category_breakdown=categories,
            monthly_comparison=monthly,
            top_appliances=top_appliances,
            insights=report.insights,
        )

    async def _get_historical_totals(
        self, user_id: uuid.UUID, month: int, year: int
    ) -> tuple[float | None, float | None]:
        """Busca totais históricos de um período específico nos registros de consumo."""
        result = await self.db.execute(
            select(ConsumptionRecord).where(
                and_(
                    ConsumptionRecord.user_id == user_id,
                    ConsumptionRecord.reference_month == month,
                    ConsumptionRecord.reference_year == year,
                )
            )
        )
        records = list(result.scalars().all())

        if not records:
            return None, None

        total_kwh = sum(r.kwh_consumed for r in records)
        total_cost = sum(r.estimated_cost for r in records)
        return total_kwh, total_cost
