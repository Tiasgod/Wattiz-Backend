"""
app/api/v1/endpoints/iot.py
────────────────────────────
Endpoints preparados para futura integração IoT.

Arquitetura IoT planejada:
  - Dispositivos enviam leituras via HTTP ou MQTT
  - Cada dispositivo se autentica com um device_token (JWT específico)
  - Leituras são armazenadas em tabela dedicada (alta frequência)
  - Analytics processa leituras em background (Celery/ARQ)
  - Dashboard mostra consumo em tempo real via WebSocket

Status atual: STUB — pronto para implementação.
"""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/iot", tags=["IoT (Em breve)"])


class IoTDeviceRegister(BaseModel):
    device_name: str = Field(..., examples=["SmartMeter-Sala"])
    device_type: str = Field(..., examples=["smart_meter", "smart_plug"])
    mac_address: str | None = None


class IoTReadingIngest(BaseModel):
    device_token: str
    power_watts: float
    timestamp: str  # ISO 8601


@router.post(
    "/devices",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="[Em breve] Registrar dispositivo IoT",
    description="Este endpoint estará disponível na próxima versão da Wattiz.",
)
async def register_device(
    data: IoTDeviceRegister,
    current_user: User = Depends(get_current_active_user),
) -> dict:
    return {
        "message": "Integração IoT em desenvolvimento. Disponível em breve!",
        "roadmap": {
            "fase_1": "Suporte a smart plugs (monitoramento por aparelho)",
            "fase_2": "Integração com medidores inteligentes (smart meters)",
            "fase_3": "Dashboard em tempo real via WebSocket",
            "fase_4": "Alertas automáticos de consumo anômalo",
        },
    }


@router.post(
    "/readings",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="[Em breve] Ingestão de leituras IoT",
)
async def ingest_reading(data: IoTReadingIngest) -> dict:
    return {"message": "Ingestão IoT em desenvolvimento."}
