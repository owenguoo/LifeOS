from fastapi import APIRouter
from app.api.v1.endpoints import memory, simple_auth, videos, insights

# Create the main API router
api_router = APIRouter()

# Include auth endpoints
api_router.include_router(
    simple_auth.router,
    prefix="/auth",
    tags=["authentication"]
)

# Include video endpoints
api_router.include_router(
    videos.router,
    prefix="/videos",
    tags=["videos"]
)

# Include memory endpoints
api_router.include_router(
    memory.router,
    prefix="/memory",
    tags=["memory"]
)

# Include insights endpoints
api_router.include_router(
    insights.router,
    prefix="/insights",
    tags=["insights"]
) 