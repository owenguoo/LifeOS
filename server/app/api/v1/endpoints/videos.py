from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.middleware.simple_auth import get_current_user
from app.schemas.simple_auth import User
from database.supabase_client import SupabaseManager


router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_user_videos(
    limit: int = Query(50, ge=1, le=100, description="Number of videos to return"),
    offset: int = Query(0, ge=0, description="Number of videos to skip"),
    current_user: User = Depends(get_current_user),
):
    """
    Get all videos for the authenticated user
    """
    try:
        supabase_manager = SupabaseManager()
        videos = await supabase_manager.get_user_videos(
            user_id=str(current_user.id), limit=limit, offset=offset
        )
        return videos

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving videos: {str(e)}",
        )


@router.get("/{video_id}", response_model=Dict[str, Any])
async def get_video(video_id: str, current_user: User = Depends(get_current_user)):
    """
    Get a specific video by ID (only if it belongs to the authenticated user)
    """
    try:
        supabase_manager = SupabaseManager()
        video = await supabase_manager.get_video_analysis(
            video_id=video_id, user_id=str(current_user.id)
        )

        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found or you don't have permission to access it",
            )

        return video

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving video: {str(e)}",
        )


@router.delete("/{video_id}")
async def delete_video(video_id: str, current_user: User = Depends(get_current_user)):
    """
    Delete a video (only if it belongs to the authenticated user)
    """
    try:
        supabase_manager = SupabaseManager()

        # First check if the video exists and belongs to the user
        video = await supabase_manager.get_video_analysis(
            video_id=video_id, user_id=str(current_user.id)
        )

        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found or you don't have permission to delete it",
            )

        # Delete the video
        result = (
            supabase_manager.client.table("videos")
            .delete()
            .eq("video_id", video_id)
            .eq("user_id", str(current_user.id))
            .execute()
        )

        if result.data:
            return {"message": "Video deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete video",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting video: {str(e)}",
        )
