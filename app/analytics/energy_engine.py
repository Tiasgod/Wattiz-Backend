"""
app/analytics/energy_engine.py
───────────────────────────────
Motor de analytics energético da Wattiz.

Responsabilidades:
  1. Calcular kWh e custo por aparelho
  2. Agregar por categoria
  3. Comparar períodos mensais
  4. Detectar anomalias e tendências
  5. Gerar insights em linguagem natural (sem IA — regras determinísticas)

Os dados produzidos aqui alimentam o dashboard e a IA Lume,
garantindo que a Lume nunca invente números.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.appliance import Appliance
    from app.models.consumption import ConsumptionRecord


# ─── Fórmula base ─────────────────────────────────────────────────────────────
def calculate_kwh(power_watts: float, hours_per_day: float, days_per_month: int) -> float:
    """
    Fórmula oficial: consumo_kwh = (potência * horas_dia * dias_mês) / 1000

    Args:
        power_watts: Potência do aparelho em Watts.
        hours_per_day: Horas de uso por dia.
        days_per_month: Dias de uso por mês.

    Returns:
        Consumo estimado em kWh no período.
    """
    return round((power_watts * hours_per_day * days_per_month) / 1000, 4)


def calculate_cost(kwh: float, tariff: float) -> float:
    """Custo estimado em R$ dado consumo e tarifa R$/kWh."""
    return round(kwh * tariff, 2)


# ─── Estruturas de dados analíticos ───────────────────────────────────────────

@dataclass
class ApplianceAnalytics:
    appliance_id: str
    name: str
    category: str
    kwh_per_month: float
    estimated_cost: float
    percentage_of_total: float = 0.0


@dataclass
class CategoryAnalytics:
    category: str
    kwh: float
    estimated_cost: float
    percentage: float = 0.0


@dataclass
class EnergyReport:
    """Resultado completo da análise energética de um período."""
    total_kwh: float
    total_cost: float
    tariff_used: float
    appliances: list[ApplianceAnalytics] = field(default_factory=list)
    categories: list[CategoryAnalytics] = field(default_factory=list)
    highest_consumer: ApplianceAnalytics | None = None
    insights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serializa para JSON — usado na persistência do relatório."""
        return {
            "total_kwh": self.total_kwh,
            "total_cost": self.total_cost,
            "tariff_used": self.tariff_used,
            "appliances": [
                {
                    "appliance_id": a.appliance_id,
                    "name": a.name,
                    "category": a.category,
                    "kwh_per_month": a.kwh_per_month,
                    "estimated_cost": a.estimated_cost,
                    "percentage_of_total": a.percentage_of_total,
                }
                for a in self.appliances
            ],
            "categories": [
                {
                    "category": c.category,
                    "kwh": c.kwh,
                    "estimated_cost": c.estimated_cost,
                    "percentage": c.percentage,
                }
                for c in self.categories
            ],
            "highest_consumer": (
                {
                    "name": self.highest_consumer.name,
                    "kwh_per_month": self.highest_consumer.kwh_per_month,
                    "percentage_of_total": self.highest_consumer.percentage_of_total,
                }
                if self.highest_consumer
                else None
            ),
            "insights": self.insights,
        }


# ─── Motor principal ───────────────────────────────────────────────────────────

class EnergyEngine:
    """
    Orquestra todos os cálculos energéticos.

    Uso:
        engine = EnergyEngine(tariff=0.75)
        report = engine.analyze(appliances)
    """

    def __init__(self, tariff: float) -> None:
        self.tariff = tariff

    def analyze(self, appliances: list["Appliance"]) -> EnergyReport:
        """
        Analisa uma lista de aparelhos e retorna o relatório energético completo.
        """
        if not appliances:
            return EnergyReport(
                total_kwh=0.0,
                total_cost=0.0,
                tariff_used=self.tariff,
                insights=["Nenhum eletrodoméstico cadastrado ainda."],
            )

        # ── 1. Calcular por aparelho ───────────────────────────────────────────
        appliance_data: list[ApplianceAnalytics] = []
        for ap in appliances:
            kwh = calculate_kwh(ap.power_watts, ap.hours_per_day, ap.days_per_month)
            cost = calculate_cost(kwh, self.tariff)
            appliance_data.append(
                ApplianceAnalytics(
                    appliance_id=str(ap.id),
                    name=ap.name,
                    category=ap.category,
                    kwh_per_month=kwh,
                    estimated_cost=cost,
                )
            )

        # ── 2. Totais ─────────────────────────────────────────────────────────
        total_kwh = round(sum(a.kwh_per_month for a in appliance_data), 4)
        total_cost = round(sum(a.estimated_cost for a in appliance_data), 2)

        # ── 3. Percentuais individuais ────────────────────────────────────────
        for a in appliance_data:
            a.percentage_of_total = (
                round((a.kwh_per_month / total_kwh) * 100, 1) if total_kwh > 0 else 0.0
            )

        # ── 4. Agrupamento por categoria ──────────────────────────────────────
        cat_map: dict[str, float] = {}
        for a in appliance_data:
            cat_map[a.category] = cat_map.get(a.category, 0.0) + a.kwh_per_month

        categories = [
            CategoryAnalytics(
                category=cat,
                kwh=round(kwh, 4),
                estimated_cost=calculate_cost(kwh, self.tariff),
                percentage=round((kwh / total_kwh) * 100, 1) if total_kwh > 0 else 0.0,
            )
            for cat, kwh in sorted(cat_map.items(), key=lambda x: x[1], reverse=True)
        ]

        # ── 5. Maior consumidor ───────────────────────────────────────────────
        highest = max(appliance_data, key=lambda a: a.kwh_per_month, default=None)

        # ── 6. Insights determinísticos ───────────────────────────────────────
        insights = self._generate_insights(appliance_data, categories, total_kwh, total_cost)

        return EnergyReport(
            total_kwh=total_kwh,
            total_cost=total_cost,
            tariff_used=self.tariff,
            appliances=sorted(appliance_data, key=lambda a: a.kwh_per_month, reverse=True),
            categories=categories,
            highest_consumer=highest,
            insights=insights,
        )

    # ─── Insights ─────────────────────────────────────────────────────────────

    def _generate_insights(
        self,
        appliances: list[ApplianceAnalytics],
        categories: list[CategoryAnalytics],
        total_kwh: float,
        total_cost: float,
    ) -> list[str]:
        insights: list[str] = []

        if not appliances:
            return insights

        # Maior consumidor individual
        top = appliances[0]
        if top.percentage_of_total >= 30:
            insights.append(
                f"⚠️ Seu {top.name} representa {top.percentage_of_total}% do consumo total "
                f"({top.kwh_per_month} kWh). Reduzir o uso pode gerar economia significativa."
            )

        # Categoria dominante
        if categories and categories[0].percentage >= 40:
            cat = categories[0]
            insights.append(
                f"📊 A categoria '{cat.category}' concentra {cat.percentage}% do consumo "
                f"({cat.kwh:.1f} kWh / R$ {cat.estimated_cost:.2f})."
            )

        # Custo mensal alto
        if total_cost > 300:
            insights.append(
                f"💡 Seu gasto estimado de R$ {total_cost:.2f}/mês está acima da média "
                f"de residências com perfil similar. Revise aparelhos de alta potência."
            )
        elif total_cost < 100:
            insights.append(
                f"✅ Parabéns! Seu consumo de R$ {total_cost:.2f}/mês está dentro de uma "
                f"faixa eficiente."
            )

        # Aparelhos ociosos (alta potência + pouco uso = oportunidade)
        for ap in appliances:
            if ap.kwh_per_month > 50 and ap.percentage_of_total > 20:
                insights.append(
                    f"🔌 {ap.name} consome {ap.kwh_per_month} kWh/mês. "
                    f"Considere um modelo mais eficiente ou reduzir o tempo de uso."
                )
                break  # um insight desse tipo por análise

        return insights

    # ─── Comparação mensal ────────────────────────────────────────────────────

    @staticmethod
    def compare_months(
        current_kwh: float,
        previous_kwh: float | None,
    ) -> float | None:
        """
        Retorna a variação percentual entre dois meses.
        Positivo = aumento, negativo = redução.
        """
        if previous_kwh is None or previous_kwh == 0:
            return None
        return round(((current_kwh - previous_kwh) / previous_kwh) * 100, 1)

    @staticmethod
    def forecast_next_month(history_kwh: list[float]) -> float | None:
        """
        Previsão simples para o próximo mês usando média móvel dos últimos 3 meses.
        Pode ser evoluída para modelos de ML no futuro.
        """
        if len(history_kwh) < 2:
            return None
        window = history_kwh[-3:]  # últimos 3 meses
        return round(sum(window) / len(window), 2)
