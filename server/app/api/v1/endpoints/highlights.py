from fastapi import APIRouter, HTTPException, Depends
import logging

from database.supabase_client import SupabaseManager
from app.schemas.simple_auth import User
from app.middleware.simple_auth import get_current_user
from app.services.s3_service import s3_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Supabase manager
supabase_manager = SupabaseManager()


@router.get("/list")
async def list_highlights(current_user: User = Depends(get_current_user)):
    """
    Get all highlighted videos for the current user in a non-paginated format
    Similar to Google Photos scroll interface - returns full video data for highlighted videos
    """
    try:
        user_id = current_user.id

        # First, get highlights for the user
        try:
            highlights_result = (
                supabase_manager.client.table("highlights")
                .select("highlight_id, created_at, video_id")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
        except Exception as e:
            logger.warning(f"Highlights table might not exist yet: {e}")
            return {"highlights": [], "total": 0}

        if not highlights_result.data:
            return {"highlights": [], "total": 0}

        # Get video details for each highlight
        highlights = []
        for highlight in highlights_result.data:
            try:
                video_result = (
                    supabase_manager.client.table("videos")
                    .select("*")
                    .eq("video_id", highlight["video_id"])
                    .execute()
                )

                if video_result.data:
                    video_data = video_result.data[0]

                    # Generate pre-signed URL for the video
                    if video_data.get("s3_link"):
                        original_url = video_data["s3_link"]
                        presigned_url = s3_service.generate_presigned_url(
                            video_data["s3_link"]
                        )
                        video_data["s3_link"] = presigned_url
                        logger.info(
                            f"Generated pre-signed URL for video {highlight['video_id']}: {original_url} -> {presigned_url[:100]}..."
                        )

                    highlights.append(
                        {
                            "highlight_id": highlight["highlight_id"],
                            "created_at": highlight["created_at"],
                            "videos": video_data,
                        }
                    )
                else:
                    logger.warning(
                        f"Video {highlight['video_id']} not found for highlight {highlight['highlight_id']}"
                    )
            except Exception as e:
                logger.error(f"Error fetching video {highlight['video_id']}: {e}")
                continue

        logger.info(f"Retrieved {len(highlights)} highlights for user {user_id}")
        return {"highlights": highlights, "total": len(highlights)}

    except Exception as e:
        logger.error(f"Error fetching highlights: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch highlights: {str(e)}"
        )
