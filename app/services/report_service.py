"""
app/services/report_service.py
────────────────────────────────
Serviço de geração e consulta de relatórios mensais.
"""

from __future__ import annotations

import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.energy_engine import EnergyEngine
from app.ia.lume_service import LumeService
from app.models.appliance import Appliance
from app.models.report import Report
from app.schemas.report import ReportGenerateRequest
from app.services.tariff_service import TariffService


class ReportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def generate(
        self, user_id: uuid.UUID, req: ReportGenerateRequest
    ) -> Report:
        """
        Gera ou atualiza o relatório mensal do usuário.
        1. Calcula analytics com EnergyEngine
        2. (Opcional) Enriquece com resumo da Lume
        3. Persiste no banco
        """
        # ── Aparelhos e tarifa ────────────────────────────────────────────────
        result = await self.db.execute(
            select(Appliance).where(Appliance.user_id == user_id)
        )
        appliances = list(result.scalars().all())

        tariff = await TariffService(self.db).get_active_tariff_value(user_id)
        engine = EnergyEngine(tariff=tariff)
        energy_report = engine.analyze(appliances)
        report_data = energy_report.to_dict()

        # ── Resumo da Lume ────────────────────────────────────────────────────
        lume_summary: str | None = None
        if req.include_lume_summary:
            lume = LumeService()
            lume_summary = await lume.generate_insights(report_data)

        # ── Verificar se já existe relatório para o período ───────────────────
        existing = await self.get_report(user_id, req.reference_month, req.reference_year)

        if existing:
            existing.data = report_data
            existing.lume_summary = lume_summary
            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        report = Report(
            user_id=user_id,
            reference_month=req.reference_month,
            reference_year=req.reference_year,
            data=report_data,
            lume_summary=lume_summary,
        )
        self.db.add(report)
        await self.db.flush()
        await self.db.refresh(report)
        return report

    async def get_report(
        self, user_id: uuid.UUID, month: int, year: int
    ) -> Report | None:
        result = await self.db.execute(
            select(Report).where(
                and_(
                    Report.user_id == user_id,
                    Report.reference_month == month,
                    Report.reference_year == year,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_reports(self, user_id: uuid.UUID) -> list[Report]:
        result = await self.db.execute(
            select(Report)
            .where(Report.user_id == user_id)
            .order_by(Report.reference_year.desc(), Report.reference_month.desc())
        )
        return list(result.scalars().all())
