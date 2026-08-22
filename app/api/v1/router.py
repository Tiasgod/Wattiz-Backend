"""
app/api/v1/router.py
─────────────────────
Agrega todos os routers da v1 da API Wattiz.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    appliances,
    auth,
    dashboard,
    iot,
    lume,
    reports,
    tariffs,
    users,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(appliances.router)
api_router.include_router(tariffs.router)
api_router.include_router(dashboard.router)
api_router.include_router(reports.router)
api_router.include_router(lume.router)
api_router.include_router(iot.router)
