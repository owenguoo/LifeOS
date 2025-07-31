"""
Redis queue manager for video processing pipeline
"""

import json
import time
from typing import Dict, Any, Optional
import redis.asyncio as redis
from config import Config


class VideoQueueManager:
    """Manages Redis queues for video processing pipeline"""

    def __init__(self, redis_url: str = ""):
        self.redis_url = (
            redis_url
            or f"redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}"
        )
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

    async def add_video_segment(
        self, video_path: str, metadata: Dict[str, Any] = {}
    ) -> bool:
        """Add a video segment to the processing queue"""
        try:
            if not self.redis:
                await self.connect()

            job_data = {
                "video_path": video_path,
                "metadata": metadata or {},
                "timestamp": time.time(),
                "status": "pending",
            }

            # Add to queue using LPUSH (left push)
            await self.redis.lpush(self.queue_name, json.dumps(job_data))
            print(f"Added video segment to queue: {video_path}")
            return True

        except Exception as e:
            print(f"Error adding video to queue: {e}")
            return False

    async def add_video_segment_data(self, segment_data: Dict[str, Any]) -> bool:
        """Add video segment data directly to the processing queue"""
        try:
            if not self.redis:
                await self.connect()

            job_data = {
                "segment_data": segment_data,
                "timestamp": time.time(),
                "status": "pending",
            }

            # Add to queue using LPUSH (left push)
            await self.redis.lpush(self.queue_name, json.dumps(job_data))
            print(
                f"Added video segment data to queue: segment_id={segment_data.get('segment_id')}"
            )
            return True

        except Exception as e:
            print(f"Error adding video segment data to queue: {e}")
            return False

    async def get_video_segment(self, timeout: int = None) -> Optional[Dict[str, Any]]:
        """Get next video segment from the processing queue with configurable timeout"""
        try:
            if not self.redis:
                await self.connect()

            # Use shorter timeout for better responsiveness - workers check more frequently
            actual_timeout = timeout or 0.5  # Reduced from 2s to 0.5s
            result = await self.redis.brpop([self.queue_name], timeout=actual_timeout)

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

    async def add_batch_segments(
        self, video_paths: list, metadata: Dict[str, Any] = {}
    ) -> int:
        """Add multiple video segments to queue in optimized batch"""
        try:
            if not self.redis:
                await self.connect()

            current_time = time.time()
            jobs = []

            for video_path in video_paths:
                job_data = {
                    "video_path": video_path,
                    "metadata": metadata or {},
                    "timestamp": current_time,  # Use same timestamp for batch
                    "status": "pending",
                }
                jobs.append(json.dumps(job_data))

            # Use pipeline for atomic batch operation
            pipe = self.redis.pipeline()
            # Add all jobs in single pipeline execution
            pipe.lpush(self.queue_name, *jobs)
            await pipe.execute()

            print(f"Added {len(jobs)} video segments to queue in batch")
            return len(jobs)

        except Exception as e:
            print(f"Error adding batch to queue: {e}")
            return 0
