"""
System management endpoints for video ingestion
"""
import asyncio
import os
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from app.middleware.simple_auth import get_current_user
from app.schemas.simple_auth import User
from config import Config

# Import the video lifecycle manager
import sys
from pathlib import Path
# Add the server root to Python path to import main.py
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))
from main import VideoLifecycleManager

router = APIRouter()

# Global variable to track running systems
_running_systems: Dict[str, Any] = {}


@router.post("/start")
async def start_video_system(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Start the complete video ingestion and processing system
    This endpoint starts both ingestion and workers for the authenticated user
    """
    try:
        user_id = current_user.id
        
        # Check if system is already running for this user
        if user_id in _running_systems:
            return JSONResponse(
                content={
                    "message": "Video system is already running for this user",
                    "user_id": user_id,
                    "status": "already_running"
                }
            )
        
        # Get API key
        api_key = os.getenv("TWELVELABS_API_KEY") or Config.TWELVELABS_API_KEY
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="TWELVELABS_API_KEY is not configured"
            )
        
        # Create video lifecycle manager for this user
        manager = VideoLifecycleManager(api_key, user_id)
        
        # Start the system in background
        async def run_system():
            try:
                _running_systems[user_id] = {
                    "manager": manager,
                    "status": "running",
                    "started_at": asyncio.get_event_loop().time()
                }
                await manager.start_both_systems()
            except Exception as e:
                print(f"Error in video system for user {user_id}: {e}")
                # Remove from running systems if it fails
                _running_systems.pop(user_id, None)
        
        # Add task to background
        background_tasks.add_task(run_system)
        
        return JSONResponse(
            content={
                "message": "Video ingestion and processing system started successfully",
                "user_id": user_id,
                "status": "starting",
                "config": {
                    "resolution": f"{Config.RESOLUTION[0]}x{Config.RESOLUTION[1]}",
                    "fps": Config.FPS,
                    "segment_duration": Config.SEGMENT_DURATION,
                    "num_workers": Config.NUM_WORKERS
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start video system: {str(e)}"
        )


@router.get("/status")
async def get_system_status(current_user: User = Depends(get_current_user)):
    """Get the status of the video system for the authenticated user"""
    try:
        user_id = current_user.id
        
        if user_id not in _running_systems:
            return JSONResponse(
                content={
                    "user_id": user_id,
                    "status": "not_running",
                    "message": "Video system is not currently running"
                }
            )
        
        system_info = _running_systems[user_id]
        current_time = asyncio.get_event_loop().time()
        uptime = current_time - system_info["started_at"]
        
        return JSONResponse(
            content={
                "user_id": user_id,
                "status": system_info["status"],
                "uptime_seconds": round(uptime, 2),
                "message": "Video system is running"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system status: {str(e)}"
        )


@router.post("/stop")
async def stop_video_system(current_user: User = Depends(get_current_user)):
    """Stop the video system for the authenticated user"""
    try:
        user_id = current_user.id
        
        if user_id not in _running_systems:
            return JSONResponse(
                content={
                    "user_id": user_id,
                    "status": "not_running",
                    "message": "Video system was not running"
                }
            )
        
        # Remove from running systems (this will help the background task know to stop)
        system_info = _running_systems.pop(user_id, None)
        
        return JSONResponse(
            content={
                "user_id": user_id,
                "status": "stopped",
                "message": "Video system stop requested"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop video system: {str(e)}"
        )


@router.post("/end")
async def end_video_system(current_user: User = Depends(get_current_user)):
    """
    End/shutdown the video system for the authenticated user
    Alias for /stop endpoint - called when user exits the application
    """
    try:
        user_id = current_user.id
        
        if user_id not in _running_systems:
            return JSONResponse(
                content={
                    "user_id": user_id,
                    "status": "not_running",
                    "message": "Video system was not running"
                }
            )
        
        # Remove from running systems
        system_info = _running_systems.pop(user_id, None)
        
        return JSONResponse(
            content={
                "user_id": user_id,
                "status": "ended",
                "message": "Video system ended successfully",
                "uptime_seconds": round(asyncio.get_event_loop().time() - system_info["started_at"], 2) if system_info else 0
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to end video system: {str(e)}"
        )


@router.get("/health")
async def system_health():
    """Check system health and requirements"""
    try:
        # Check Redis connection
        from video_queue.queue_manager import VideoQueueManager
        queue_manager = VideoQueueManager()
        redis_connected = await queue_manager.connect()
        if redis_connected:
            await queue_manager.disconnect()
        
        # Check API key
        api_key = os.getenv("TWELVELABS_API_KEY") or Config.TWELVELABS_API_KEY
        api_key_configured = bool(api_key)
        
        # Count running systems
        running_count = len(_running_systems)
        
        return JSONResponse(
            content={
                "status": "healthy" if redis_connected and api_key_configured else "unhealthy",
                "redis_connected": redis_connected,
                "api_key_configured": api_key_configured,
                "running_systems": running_count,
                "active_users": list(_running_systems.keys()) if _running_systems else []
            }
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "redis_connected": False,
                "api_key_configured": False,
                "running_systems": 0,
                "active_users": []
            }
        )