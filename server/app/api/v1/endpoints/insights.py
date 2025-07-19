from typing import List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from app.middleware.simple_auth import get_current_user
from app.schemas.simple_auth import User
from database.supabase_client import SupabaseManager


router = APIRouter()


@router.get("/recent", response_model=Dict[str, Any])
async def get_recent_events(
    current_user: User = Depends(get_current_user)
):
    """
    Get the 5 most recent events and provide a summary
    """
    try:
        supabase_manager = SupabaseManager()
        
        # Get the 5 most recent videos for the user
        videos = await supabase_manager.get_user_videos(
            user_id=str(current_user.id),
            limit=5,
            offset=0
        )
        
        if not videos:
            return {
                "message": "No recent events found",
                "recent_events": [],
                "summary": "No activities recorded recently."
            }
        
        # Create summary from the recent events
        summary_parts = []
        for i, video in enumerate(videos, 1):
            if video.get('detailed_summary'):
                timestamp = video.get('timestamp', video.get('datetime', 'Unknown time'))
                summary_parts.append(f"{i}. {timestamp}: {video['detailed_summary'][:100]}...")
        
        overall_summary = f"Recent activity summary ({len(videos)} events):\n" + "\n".join(summary_parts)
        
        return {
            "message": f"Found {len(videos)} recent events",
            "recent_events": videos,
            "summary": overall_summary
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving recent events: {str(e)}"
        )


@router.get("/summary", response_model=Dict[str, Any])
async def get_daily_recap(
    current_user: User = Depends(get_current_user)
):
    """
    Get all events from today and provide a daily recap
    """
    try:
        supabase_manager = SupabaseManager()
        
        # Get today's date range
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        # Get all videos for the user (we'll filter by date in the query)
        # Note: Since the existing method doesn't support date filtering,
        # we'll get all videos and filter them in Python
        all_videos = await supabase_manager.get_user_videos(
            user_id=str(current_user.id),
            limit=1000,  # Get more to ensure we capture today's events
            offset=0
        )
        
        # Filter videos for today
        today_videos = []
        for video in all_videos:
            video_date = None
            # Try to parse the timestamp/datetime field
            for date_field in ['timestamp', 'datetime', 'processed_at']:
                if video.get(date_field):
                    try:
                        if isinstance(video[date_field], str):
                            video_date = datetime.fromisoformat(video[date_field].replace('Z', '+00:00')).date()
                        else:
                            video_date = video[date_field].date()
                        break
                    except (ValueError, AttributeError):
                        continue
            
            if video_date == today:
                today_videos.append(video)
        
        if not today_videos:
            return {
                "date": today.isoformat(),
                "message": "No events recorded today",
                "events_count": 0,
                "events": [],
                "daily_recap": f"No activities were recorded for {today.strftime('%B %d, %Y')}. It was a quiet day!"
            }
        
        # Create comprehensive daily recap
        recap_parts = [
            f"Daily Recap for {today.strftime('%B %d, %Y')}:",
            f"Total events recorded: {len(today_videos)}",
            "",
            "Event Timeline:"
        ]
        
        # Sort events by time and create timeline
        sorted_videos = sorted(today_videos, key=lambda x: x.get('timestamp', x.get('datetime', '')))
        
        for i, video in enumerate(sorted_videos, 1):
            timestamp = video.get('timestamp', video.get('datetime', 'Unknown time'))
            if isinstance(timestamp, str):
                try:
                    # Parse and format timestamp
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%I:%M %p')
                except (ValueError, AttributeError):
                    time_str = timestamp
            else:
                time_str = str(timestamp)
            
            summary = video.get('detailed_summary', 'No summary available')
            recap_parts.append(f"{time_str}: {summary}")
        
        # Add summary insights
        recap_parts.extend([
            "",
            "Day Summary:",
            f"You had {len(today_videos)} recorded activities today. "
        ])
        
        if len(today_videos) >= 10:
            recap_parts.append("It was quite a busy day with lots of activities!")
        elif len(today_videos) >= 5:
            recap_parts.append("You had a moderately active day.")
        else:
            recap_parts.append("It was a relatively quiet day.")
        
        daily_recap = "\n".join(recap_parts)
        
        return {
            "date": today.isoformat(),
            "message": f"Found {len(today_videos)} events for today",
            "events_count": len(today_videos),
            "events": today_videos,
            "daily_recap": daily_recap
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating daily recap: {str(e)}"
        )