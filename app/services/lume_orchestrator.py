"""
app/services/lume_orchestrator.py
──────────────────────────────────
Orquestrador da IA Lume — conecta analytics + serviço de IA.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.energy_engine import EnergyEngine
from app.ia.lume_service import LumeService
from app.models.appliance import Appliance
from app.schemas.lume import LumeChatRequest, LumeChatResponse, LumeInsightResponse
from app.services.tariff_service import TariffService


class LumeOrchestrator:
    """
    Garante que a Lume nunca responda sem contexto de dados reais.
    Fluxo: usuário → analytics → Lume → resposta.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.lume = LumeService()

    async def chat(
        self, user_id: uuid.UUID, req: LumeChatRequest
    ) -> LumeChatResponse:
        context = await self._build_context(user_id, req.reference_month, req.reference_year)
        response = await self.lume.chat(req.message, context)
        return LumeChatResponse(
            response=response,
            context_used=context,
            model=self.lume.model,
        )

    async def generate_insights(
        self, user_id: uuid.UUID, month: int, year: int
    ) -> LumeInsightResponse:
        context = await self._build_context(user_id, month, year)
        full_analysis = await self.lume.generate_insights(context)

        # Insights determinísticos do engine como complemento
        engine_insights = context.get("engine_insights", [])

        return LumeInsightResponse(
            insights=engine_insights,
            full_analysis=full_analysis,
            context_used=context,
        )

    async def _build_context(
        self,
        user_id: uuid.UUID,
        month: int | None,
        year: int | None,
    ) -> dict:
        """
        Constrói o contexto energético completo para alimentar a Lume.
        Este é o dado de verdade — calculado, não inventado.
        """
        now = datetime.now(timezone.utc)
        ref_month = month or now.month
        ref_year = year or now.year

        # Aparelhos
        result = await self.db.execute(
            select(Appliance).where(Appliance.user_id == user_id)
        )
        appliances = list(result.scalars().all())

        # Tarifa
        tariff = await TariffService(self.db).get_active_tariff_value(user_id)

        # Análise
        engine = EnergyEngine(tariff=tariff)
        report = engine.analyze(appliances)

        return {
            "periodo": f"{ref_month:02d}/{ref_year}",
            "total_kwh": report.total_kwh,
            "total_custo_reais": report.total_cost,
            "tarifa_kwh": tariff,
            "quantidade_aparelhos": len(appliances),
            "maior_consumidor": (
                {
                    "nome": report.highest_consumer.name,
                    "kwh": report.highest_consumer.kwh_per_month,
                    "percentual": report.highest_consumer.percentage_of_total,
                    "custo": report.highest_consumer.estimated_cost,
                }
                if report.highest_consumer
                else None
            ),
            "por_categoria": [
                {
                    "categoria": c.category,
                    "kwh": c.kwh,
                    "percentual": c.percentage,
                    "custo": c.estimated_cost,
                }
                for c in report.categories
            ],
            "top_aparelhos": [
                {
                    "nome": a.name,
                    "categoria": a.category,
                    "kwh": a.kwh_per_month,
                    "custo": a.estimated_cost,
                    "percentual": a.percentage_of_total,
                }
                for a in report.appliances[:5]
            ],
            "engine_insights": report.insights,
        }
