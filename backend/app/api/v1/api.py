from fastapi import APIRouter

from app.api.v1.endpoints import emails, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(emails.router, prefix="/tenants/{tenant_id}", tags=["emails"])

