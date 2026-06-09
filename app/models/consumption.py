"""
app/models/consumption.py
─────────────────────────
Registro histórico de consumo mensal por eletrodoméstico.
Permite comparações entre períodos e detecção de tendências.

Por que guardar consumo calculado?
  Embora o consumo possa ser recalculado a partir dos parâmetros do aparelho,
  o registro histórico captura snapshots reais — útil quando o usuário
  altera horas de uso ao longo dos meses.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ConsumptionRecord(Base):
    __tablename__ = "consumption_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    appliance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appliances.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Período de referência ─────────────────────────────────────────────────
    reference_month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-12
    reference_year: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── Valores calculados no momento do registro ─────────────────────────────
    kwh_consumed: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False)  # R$
    tariff_used: Mapped[float] = mapped_column(Float, nullable=False)      # R$/kWh

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    appliance: Mapped["Appliance"] = relationship(  # type: ignore[name-defined]
        "Appliance", back_populates="consumption_records"
    )

    def __repr__(self) -> str:
        return (
            f"<ConsumptionRecord appliance={self.appliance_id} "
            f"{self.reference_month}/{self.reference_year} "
            f"{self.kwh_consumed}kWh>"
        )
