from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from database.supabase_client import SupabaseManager
from app.api.v1.endpoints.simple_auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Supabase manager
supabase_manager = SupabaseManager()


@router.get("/list")
async def list_highlights(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get all highlighted videos for the current user in a non-paginated format
    Similar to Google Photos scroll interface - returns full video data for highlighted videos
    """
    try:
        user_id = current_user["id"]
        
        # Join highlights with videos to get full video data
        result = supabase_manager.client.table("highlights").select(
            "highlight_id, created_at, videos(*)"
        ).eq("user_id", user_id).order("created_at", desc=True).execute()
        
        if result.data:
            highlights = result.data
            logger.info(f"Retrieved {len(highlights)} highlights for user {user_id}")
            return {
                "highlights": highlights,
                "total": len(highlights)
            }
        else:
            return {
                "highlights": [],
                "total": 0
            }
            
    except Exception as e:
        logger.error(f"Error fetching highlights: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch highlights: {str(e)}"
        )