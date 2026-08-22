"""
app/models/appliance.py
───────────────────────
Modelo ORM de eletrodoméstico cadastrado pelo usuário.
Cada aparelho armazena seus parâmetros de consumo; os cálculos
de kWh e custo são executados dinamicamente pelo analytics engine.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Appliance(Base):
    __tablename__ = "appliances"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Dados do aparelho ─────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    power_watts: Mapped[float] = mapped_column(Float, nullable=False)   # potência em W
    hours_per_day: Mapped[float] = mapped_column(Float, nullable=False)
    days_per_month: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    category: Mapped[str] = mapped_column(String(60), nullable=False, default="Outros")

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="appliances")  # type: ignore[name-defined]
    consumption_records: Mapped[list["ConsumptionRecord"]] = relationship(  # type: ignore[name-defined]
        "ConsumptionRecord", back_populates="appliance", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Appliance id={self.id} name={self.name} power={self.power_watts}W>"
