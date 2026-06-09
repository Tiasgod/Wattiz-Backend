"""
app/models/report.py
────────────────────
Relatório energético mensal persistido.
Armazena o snapshot JSON dos dados analíticos para
evitar recálculo e permitir histórico de relatórios.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reference_month: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Conteúdo analítico serializado (kWh, custos, insights, IA)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Texto narrativo gerado pela IA Lume
    lume_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="reports")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<Report user={self.user_id} {self.reference_month}/{self.reference_year}>"
