from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging
import boto3
import os
from botocore.exceptions import ClientError

from database.supabase_client import SupabaseManager
from app.schemas.simple_auth import User
from app.middleware.simple_auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Supabase manager
supabase_manager = SupabaseManager()

# Initialize S3 client for pre-signed URLs
def get_s3_client():
    try:
        return boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-2')  # Changed default to us-east-2
        )
    except Exception as e:
        logger.error(f"Failed to initialize S3 client: {e}")
        return None

def generate_presigned_url(s3_url: str, expiration: int = 3600) -> str:
    """
    Generate a pre-signed URL for S3 object access
    
    Args:
        s3_url: The S3 URL (e.g., https://bucket.s3.region.amazonaws.com/key)
        expiration: URL expiration time in seconds (default: 1 hour)
    
    Returns:
        Pre-signed URL or original URL if generation fails
    """
    try:
        s3_client = get_s3_client()
        if not s3_client:
            logger.warning("S3 client not available, returning original URL")
            return s3_url
        
        # Parse S3 URL to extract bucket and key
        # URL format: https://bucket.s3.region.amazonaws.com/key
        if not s3_url.startswith('https://'):
            logger.warning(f"Invalid S3 URL format: {s3_url}")
            return s3_url
        
        # Remove https:// and split by first /
        url_parts = s3_url.replace('https://', '').split('/', 1)
        if len(url_parts) != 2:
            logger.warning(f"Could not parse S3 URL: {s3_url}")
            return s3_url
        
        # Extract bucket name from the hostname
        # Handle both formats: bucket.s3.region.amazonaws.com and bucket.s3.amazonaws.com
        hostname_parts = url_parts[0].split('.')
        if len(hostname_parts) >= 3 and hostname_parts[1] == 's3':
            bucket_name = hostname_parts[0]
        else:
            logger.warning(f"Could not extract bucket name from: {s3_url}")
            return s3_url
        
        object_key = url_parts[1]
        
        logger.info(f"Generating pre-signed URL for bucket: {bucket_name}, key: {object_key}")
        
        # Generate pre-signed URL
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=expiration
        )
        
        logger.info(f"Successfully generated pre-signed URL for {object_key}")
        return presigned_url
        
    except Exception as e:
        logger.error(f"Failed to generate pre-signed URL for {s3_url}: {e}")
        return s3_url


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
            highlights_result = supabase_manager.client.table("highlights").select(
                "highlight_id, created_at, video_id"
            ).eq("user_id", user_id).order("created_at", desc=True).execute()
        except Exception as e:
            logger.warning(f"Highlights table might not exist yet: {e}")
            return {
                "highlights": [],
                "total": 0
            }
        
        if not highlights_result.data:
            return {
                "highlights": [],
                "total": 0
            }
        
        # Get video details for each highlight
        highlights = []
        for highlight in highlights_result.data:
            try:
                video_result = supabase_manager.client.table("videos").select("*").eq("video_id", highlight["video_id"]).execute()
                
                if video_result.data:
                    video_data = video_result.data[0]
                    
                    # Generate pre-signed URL for the video
                    if video_data.get("s3_link"):
                        original_url = video_data["s3_link"]
                        presigned_url = generate_presigned_url(video_data["s3_link"])
                        video_data["s3_link"] = presigned_url
                        logger.info(f"Generated pre-signed URL for video {highlight['video_id']}: {original_url} -> {presigned_url[:100]}...")
                    
                    highlights.append({
                        "highlight_id": highlight["highlight_id"],
                        "created_at": highlight["created_at"],
                        "videos": video_data
                    })
                else:
                    logger.warning(f"Video {highlight['video_id']} not found for highlight {highlight['highlight_id']}")
            except Exception as e:
                logger.error(f"Error fetching video {highlight['video_id']}: {e}")
                continue
        
        logger.info(f"Retrieved {len(highlights)} highlights for user {user_id}")
        return {
            "highlights": highlights,
            "total": len(highlights)
        }
            
    except Exception as e:
        logger.error(f"Error fetching highlights: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch highlights: {str(e)}"
        )