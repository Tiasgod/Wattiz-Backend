"""
app/schemas/tariff.py
─────────────────────
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class TariffCreate(BaseModel):
    kwh_price: float = Field(..., gt=0, le=5.0, examples=[0.75])
    distributor: str | None = Field(None, max_length=120, examples=["ENEL"])
    state: str | None = Field(None, min_length=2, max_length=2, examples=["SP"])


class TariffResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    kwh_price: float
    distributor: str | None
    state: str | None
    is_active: bool
    created_at: datetime
