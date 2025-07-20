#!/usr/bin/env python3
"""
Main orchestration script for the video ingestion and processing system with Redis queues
"""

import asyncio
import sys
import os
from pathlib import Path
from video_injestion.ingestion import VideoIngestionSystem
from video_queue.worker_manager import WorkerManager
from video_queue.queue_manager import VideoQueueManager
from config import Config


class VideoLifecycleManager:
    """Manages the complete video ingestion and processing lifecycle with Redis queues"""
    
    def __init__(self, api_key: str, user_id: str = None):
        self.api_key = api_key
        self.user_id = user_id
        self.ingestion_system = VideoIngestionSystem(
            fps=Config.FPS,
            resolution=Config.RESOLUTION,
            segment_duration=Config.SEGMENT_DURATION,
            user_id=user_id  # Pass user_id to ingestion system
        )
        self.worker_manager = WorkerManager(
            api_key=api_key,
            num_workers=Config.NUM_WORKERS,
        )
        self.queue_manager = VideoQueueManager()
        
    async def start_ingestion_only(self):
        """Start only the video ingestion system"""
        print("🎥 Starting Video Ingestion System with Redis Queue")
        print("================================================")
        await self.ingestion_system.start_ingestion()
    
    async def start_workers_only(self):
        """Start only the video processing workers"""
        print("👷 Starting Video Processing Workers")
        print("===================================")
        await self.worker_manager.start_workers()
    
    async def start_both_systems(self):
        """Start both ingestion and processing systems concurrently"""
        print("🚀 Starting Complete Video Lifecycle System with Redis")
        print("====================================================")
        
        # Start both systems concurrently
        tasks = [
            asyncio.create_task(self.ingestion_system.start_ingestion()),
            asyncio.create_task(self.worker_manager.start_workers())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\n🛑 Stopping all systems...")
            # Cancel all tasks
            for task in tasks:
                task.cancel()
            # Wait for tasks to complete cancellation
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except:
                pass  # Ignore cancellation errors
    
    async def batch_process_existing(self):
        """Process all existing video files in the output directory"""
        print("📁 Processing Existing Video Files")
        print("=================================")
        
        # Connect to queue manager
        await self.queue_manager.connect()
        
        
        
        # Add all videos to queue
        
        print("💡 Start workers to process these files: python worker_manager.py")
        
        await self.queue_manager.disconnect()
    
    async def monitor_queue(self):
        """Monitor the Redis queue status"""
        print("📊 Queue Monitoring")
        print("==================")
        
        await self.queue_manager.connect()
        
        try:
            while True:
                queue_size = await self.queue_manager.get_queue_size()
                print(f"Queue size: {queue_size} items")
                await asyncio.sleep(5)
        except KeyboardInterrupt:
            print("\nStopping queue monitoring...")
        finally:
            await self.queue_manager.disconnect()


def print_usage():
    """Print usage information"""
    print("Video Ingestion and Processing System with Redis Queues")
    print("======================================================")
    print()
    print("Usage: python main.py [mode]")
    print()
    print("Modes:")
    print("  ingestion    - Start video ingestion only (puts segments in Redis queue)")
    print("  workers      - Start video processing workers only (processes from Redis queue)")
    print("  both         - Start both systems (default)")
    print("  monitor      - Monitor Redis queue status")
    print("  help         - Show this help message")
    print()
    print("Requirements:")
    print("  - Redis server running on localhost:6379")
    print("  - Set TWELVELABS_API_KEY environment variable")
    print("  - Ensure camera is connected and accessible")
    print()
    print("Configuration:")
    print(f"  - Resolution: {Config.RESOLUTION[0]}x{Config.RESOLUTION[1]}")
    print(f"  - FPS: {Config.FPS}")
    print(f"  - Segment Duration: {Config.SEGMENT_DURATION}s")
    print(f"  - Number of Workers: {Config.NUM_WORKERS}")
    print(f"  - Redis Queue: {Config.REDIS_QUEUE_NAME}")
    print()
    print("Example workflow:")
    print("  1. Start workers: python main.py workers")
    print("  2. Start ingestion: python main.py ingestion")
    print("  3. Or start both: python main.py both")


async def check_redis_connection():
    """Check if Redis is available"""
    try:
        queue_manager = VideoQueueManager()
        connected = await queue_manager.connect()
        await queue_manager.disconnect()
        return connected
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("Please ensure Redis is running on localhost:6379")
        print("Install Redis: brew install redis (macOS) or apt-get install redis-server (Ubuntu)")
        print("Start Redis: redis-server")
        return False


async def main():
    """Main entry point"""
    
    # Parse command line arguments
    mode = "both"  # default mode
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    
    if mode == "help":
        print_usage()
        return
    
    # Check Redis connection for modes that need it
    if mode in ["ingestion", "workers", "both", "monitor"]:
        if not await check_redis_connection():
            print("❌ Redis is required for this mode. Please start Redis server.")
            sys.exit(1)
    
    # Check for API key for modes that need it
    api_key = os.getenv("TWELVELABS_API_KEY") or Config.TWELVELABS_API_KEY
    if not api_key and mode in ["workers", "both"]:
        print("❌ Error: TWELVELABS_API_KEY is required for processing modes")
        print("Please set your API key:")
        print("  export TWELVELABS_API_KEY='your_api_key_here'")
        print("  or update config.py with your API key")
        sys.exit(1)
    
    # Ensure api_key is not None for the manager
    if api_key is None:
        api_key = ""  # Provide empty string as fallback
    
    # Create lifecycle manager with hardcoded user_id for testing
    user_id = "fab1e4f5-6e95-4729-9c0c-cd642e48a7be"
    manager = VideoLifecycleManager(api_key, user_id)
    
    try:
        if mode == "ingestion":
            await manager.start_ingestion_only()
        elif mode == "workers":
            await manager.start_workers_only()
        elif mode == "monitor":
            await manager.monitor_queue()
        elif mode == "both":
            await manager.start_both_systems()
        else:
            print(f"❌ Unknown mode: {mode}")
            print_usage()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n✅ System stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())