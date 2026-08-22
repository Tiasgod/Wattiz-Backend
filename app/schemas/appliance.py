"""
app/schemas/appliance.py
────────────────────────
Schemas Pydantic para eletrodomésticos.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# Categorias reconhecidas pela plataforma
ApplianceCategory = Literal[
    "Climatização",
    "Cozinha",
    "Iluminação",
    "Entretenimento",
    "Lavanderia",
    "Aquecimento",
    "Informática",
    "Outros",
]


class ApplianceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120, examples=["Chuveiro Elétrico"])
    power_watts: float = Field(..., gt=0, le=20_000, examples=[5400])
    hours_per_day: float = Field(..., gt=0, le=24, examples=[0.5])
    days_per_month: int = Field(30, ge=1, le=31)
    category: ApplianceCategory = "Outros"


class ApplianceUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=120)
    power_watts: float | None = Field(None, gt=0, le=20_000)
    hours_per_day: float | None = Field(None, gt=0, le=24)
    days_per_month: int | None = Field(None, ge=1, le=31)
    category: ApplianceCategory | None = None


class ApplianceResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    power_watts: float
    hours_per_day: float
    days_per_month: int
    category: str
    created_at: datetime
    updated_at: datetime

    # Campos calculados — preenchidos pelo service
    kwh_per_month: float | None = None
    estimated_cost: float | None = None
