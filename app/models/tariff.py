"""
app/models/tariff.py
────────────────────
Tarifa energética do usuário por região/distribuidora.
O usuário pode cadastrar múltiplas tarifas e marcar uma como ativa.
Preparado para futura integração com APIs de distribuidoras (ANEEL).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Tariff(Base):
    __tablename__ = "tariffs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    distributor: Mapped[str] = mapped_column(String(120), nullable=True)   # ex: "CPFL", "ENEL"
    state: Mapped[str] = mapped_column(String(2), nullable=True)           # UF
    kwh_price: Mapped[float] = mapped_column(Float, nullable=False)        # R$/kWh
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="tariffs")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<Tariff id={self.id} kwh_price={self.kwh_price} active={self.is_active}>"
