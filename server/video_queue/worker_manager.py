"""
Manager for coordinating multiple video processing workers
"""

import asyncio
import os
import signal
import sys
from typing import List
from config import Config
from video_processing.worker import VideoProcessingWorker
from video_queue.queue_manager import VideoQueueManager


class WorkerManager:
    """Manages multiple video processing workers"""

    def __init__(self, api_key: str, num_workers: int = None):
        self.api_key = api_key
        self.num_workers = num_workers or Config.NUM_WORKERS
        self.workers: List[VideoProcessingWorker] = []
        self.worker_tasks: List[asyncio.Task] = []
        self.queue_manager = VideoQueueManager()
        self.is_running = False

    async def start_workers(self):
        """Start all workers"""
        print(f"Starting {self.num_workers} video processing workers...")

        # Connect queue manager for monitoring
        await self.queue_manager.connect()

        # Create and start workers
        for worker_id in range(self.num_workers):
            worker = VideoProcessingWorker(
                worker_id=worker_id,
                api_key=self.api_key,
            )
            self.workers.append(worker)

            # Start worker as async task
            task = asyncio.create_task(worker.start())
            self.worker_tasks.append(task)

        self.is_running = True
        print(f"All {self.num_workers} workers started successfully")

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

        # Start monitoring
        await self.monitor_workers()

    async def stop_workers(self):
        """Stop all workers gracefully"""
        if not self.is_running:
            return

        print("Stopping all workers...")
        self.is_running = False

        # Stop all workers
        for worker in self.workers:
            await worker.stop()

        # Cancel all worker tasks
        for task in self.worker_tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.worker_tasks, return_exceptions=True), timeout=10.0
            )
        except asyncio.TimeoutError:
            print("Some workers took too long to stop, forcing shutdown...")

        # Disconnect queue manager
        await self.queue_manager.disconnect()

        print("All workers stopped")

    async def monitor_workers(self):
        """Monitor worker status and queue"""
        print("Starting worker monitoring...")

        while self.is_running:
            try:
                # Check queue size
                queue_size = await self.queue_manager.get_queue_size()

                # Count active workers
                active_workers = sum(1 for worker in self.workers if worker.is_running)

                # Get processing counts
                total_processed = sum(worker.processed_count for worker in self.workers)

                print(
                    f"Queue: {queue_size} items | Active workers: {active_workers}/{self.num_workers} | Processed: {total_processed}"
                )

                # Check if any worker tasks are done unexpectedly
                for i, task in enumerate(self.worker_tasks):
                    if task.done() and not task.cancelled():
                        exception = task.exception()
                        if exception:
                            print(f"Worker {i} crashed with exception: {exception}")
                            # Could restart worker here if needed

                # Sleep before next monitoring cycle
                await asyncio.sleep(10)

            except Exception as e:
                print(f"Error in worker monitoring: {e}")
                await asyncio.sleep(5)

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""

        def signal_handler(signum, frame):
            print(f"\nReceived signal {signum}, shutting down gracefully...")
            # Create task to stop workers
            asyncio.create_task(self.stop_workers())

        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def get_worker_stats(self) -> dict:
        """Get statistics from all workers"""
        stats = {
            "total_workers": self.num_workers,
            "active_workers": sum(1 for worker in self.workers if worker.is_running),
            "total_processed": sum(worker.processed_count for worker in self.workers),
            "queue_size": await self.queue_manager.get_queue_size(),
            "worker_details": [],
        }

        for worker in self.workers:
            worker_stats = {
                "worker_id": worker.worker_id,
                "is_running": worker.is_running,
                "processed_count": worker.processed_count,
                "index_id": worker.index_id,
            }
            stats["worker_details"].append(worker_stats)

        return stats

    async def add_video_to_queue(self, video_path: str, metadata: dict = {}) -> bool:
        """Add a video to the processing queue"""
        return await self.queue_manager.add_video_segment(video_path, metadata)

    async def add_batch_videos_to_queue(
        self, video_paths: List[str], metadata: dict = {}
    ) -> int:
        """Add multiple videos to the processing queue"""
        return await self.queue_manager.add_batch_segments(video_paths, metadata)


async def main():
    """Main entry point for running workers"""

    # Check for API key
    api_key = os.getenv("TWELVELABS_API_KEY") or Config.TWELVELABS_API_KEY
    if not api_key:
        print("❌ Error: TWELVELABS_API_KEY is required")
        print("Please set your API key:")
        print("  export TWELVELABS_API_KEY='your_api_key_here'")
        print("  or update config.py with your API key")
        sys.exit(1)

    # Get number of workers from command line or use default
    num_workers = Config.NUM_WORKERS
    if len(sys.argv) > 1:
        try:
            num_workers = int(sys.argv[1])
        except ValueError:
            print(f"Invalid number of workers: {sys.argv[1]}")
            sys.exit(1)

    # Create and start worker manager
    manager = WorkerManager(api_key=api_key, num_workers=num_workers)

    try:
        await manager.start_workers()
    except KeyboardInterrupt:
        print("\n✅ Worker manager stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        await manager.stop_workers()


if __name__ == "__main__":
    asyncio.run(main())
