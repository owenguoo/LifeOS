"""
Redis queue manager for video processing pipeline
"""
import asyncio
import json
import time
from typing import Dict, Any, Optional
import redis.asyncio as redis
from config import Config


class VideoQueueManager:
    """Manages Redis queues for video processing pipeline"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or f"redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}"
        self.redis = None
        self.queue_name = Config.REDIS_QUEUE_NAME
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = redis.Redis.from_url(self.redis_url)
            await self.redis.ping()
            print(f"Connected to Redis at {self.redis_url}")
            return True
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.aclose()
    
    async def add_video_segment(self, video_path: str, metadata: Dict[str, Any] = None) -> bool:
        """Add a video segment to the processing queue"""
        try:
            if not self.redis:
                await self.connect()
            
            job_data = {
                "video_path": video_path,
                "metadata": metadata or {},
                "timestamp": time.time(),
                "status": "pending"
            }
            
            # Add to queue using LPUSH (left push)
            await self.redis.lpush(self.queue_name, json.dumps(job_data))
            print(f"Added video segment to queue: {video_path}")
            return True
            
        except Exception as e:
            print(f"Error adding video to queue: {e}")
            return False
    
    async def get_video_segment(self, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """Get next video segment from the processing queue"""
        try:
            if not self.redis:
                await self.connect()
            
            # Use BRPOP (blocking right pop) with timeout
            result = await self.redis.brpop(self.queue_name, timeout=timeout)
            
            if result:
                queue_name, job_data = result
                return json.loads(job_data)
            return None
            
        except Exception as e:
            print(f"Error getting video from queue: {e}")
            return None
    
    async def get_queue_size(self) -> int:
        """Get current queue size"""
        try:
            if not self.redis:
                await self.connect()
            return await self.redis.llen(self.queue_name)
        except Exception as e:
            print(f"Error getting queue size: {e}")
            return 0
    
    async def clear_queue(self) -> bool:
        """Clear all items from the queue"""
        try:
            if not self.redis:
                await self.connect()
            await self.redis.delete(self.queue_name)
            print("Queue cleared successfully")
            return True
        except Exception as e:
            print(f"Error clearing queue: {e}")
            return False
    
    async def add_batch_segments(self, video_paths: list, metadata: Dict[str, Any] = None) -> int:
        """Add multiple video segments to queue in batch"""
        try:
            if not self.redis:
                await self.connect()
            
            jobs = []
            for video_path in video_paths:
                job_data = {
                    "video_path": video_path,
                    "metadata": metadata or {},
                    "timestamp": time.time(),
                    "status": "pending"
                }
                jobs.append(json.dumps(job_data))
            
            # Use pipeline for batch operation
            pipe = self.redis.pipeline()
            for job in jobs:
                pipe.lpush(self.queue_name, job)
            await pipe.execute()
            
            print(f"Added {len(jobs)} video segments to queue")
            return len(jobs)
            
        except Exception as e:
            print(f"Error adding batch to queue: {e}")
            return 0