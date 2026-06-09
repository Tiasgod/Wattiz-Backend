"""
app/database/base.py
────────────────────
Base declarativa compartilhada por todos os modelos SQLAlchemy.
Importar todos os modelos aqui garante que o Alembic os detecte.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe base de todos os modelos ORM da Wattiz."""
    pass


