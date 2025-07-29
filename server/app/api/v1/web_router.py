from fastapi import APIRouter
from app.api.v1.endpoints import memory, simple_auth, videos, insights, highlights

# Create the web-only API router (excludes system endpoints)
web_router = APIRouter()

# Include auth endpoints
web_router.include_router(simple_auth.router, prefix="/auth", tags=["authentication"])

# Include video endpoints
web_router.include_router(videos.router, prefix="/videos", tags=["videos"])

# Include memory endpoints
web_router.include_router(memory.router, prefix="/memory", tags=["memory"])

# Include insights endpoints
web_router.include_router(insights.router, prefix="/insights", tags=["insights"])

# Include highlights endpoints
web_router.include_router(highlights.router, prefix="/highlights", tags=["highlights"])
