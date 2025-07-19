from fastapi import APIRouter
from app.api.v1.endpoints import memory

# Create the main API router
api_router = APIRouter()

# Include memory endpoints
api_router.include_router(
    memory.router,
    prefix="/memory",
    tags=["memory"]
) 