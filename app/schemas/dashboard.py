"""
app/schemas/dashboard.py
────────────────────────
Schemas de resposta para o dashboard e analytics.
"""

from pydantic import BaseModel


class CategoryBreakdown(BaseModel):
    category: str
    kwh: float
    percentage: float
    estimated_cost: float


class ApplianceRanking(BaseModel):
    appliance_id: str
    name: str
    category: str
    kwh_per_month: float
    estimated_cost: float
    percentage_of_total: float


class MonthlyComparison(BaseModel):
    current_month: int
    current_year: int
    current_kwh: float
    current_cost: float
    previous_kwh: float | None
    previous_cost: float | None
    variation_percentage: float | None  # positivo = aumento, negativo = redução


class DashboardResponse(BaseModel):
    total_kwh: float
    total_cost: float
    active_tariff: float        # R$/kWh
    highest_consumer: ApplianceRanking | None
    category_breakdown: list[CategoryBreakdown]
    monthly_comparison: MonthlyComparison
    top_appliances: list[ApplianceRanking]
    insights: list[str]         # frases geradas pelo analytics engine
