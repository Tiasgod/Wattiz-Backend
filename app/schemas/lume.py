"""
app/schemas/lume.py
───────────────────
Schemas para a API da IA Lume.
"""

from pydantic import BaseModel, Field


class LumeChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    reference_month: int | None = Field(None, ge=1, le=12)
    reference_year: int | None = None


class LumeChatResponse(BaseModel):
    response: str
    context_used: dict    # dados do backend que alimentaram a IA
    model: str


class LumeInsightRequest(BaseModel):
    reference_month: int = Field(..., ge=1, le=12)
    reference_year: int


class LumeInsightResponse(BaseModel):
    insights: list[str]
    full_analysis: str
    context_used: dict
