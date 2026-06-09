"""
app/schemas/report.py
─────────────────────
"""
import uuid
from datetime import datetime
from pydantic import BaseModel


class ReportResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    reference_month: int
    reference_year: int
    data: dict
    lume_summary: str | None
    generated_at: datetime


class ReportGenerateRequest(BaseModel):
    reference_month: int
    reference_year: int
    include_lume_summary: bool = True
