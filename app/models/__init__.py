# Importa todos os models para o Alembic detectar automaticamente
from app.models.user import User
from app.models.appliance import Appliance
from app.models.tariff import Tariff
from app.models.consumption import ConsumptionRecord
from app.models.report import Report

__all__ = ["User", "Appliance", "Tariff", "ConsumptionRecord", "Report"]
