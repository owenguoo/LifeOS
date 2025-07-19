"""
Async worker for processing video segments from Redis queue
"""
import asyncio
import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from twelvelabs import TwelveLabs
from config import Config
from video_queue.queue_manager import VideoQueueManager
from video_injestion.s3_storage import S3StorageManager


class VideoProcessingWorker:
    """Async worker that processes video segments from Redis queue"""
    
    def __init__(self, worker_id: int, api_key: str, output_dir: str = "video_processing/processed_data"):
        self.worker_id = worker_id
        self.client = TwelveLabs(api_key=api_key)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.queue_manager = VideoQueueManager()
        self.s3_manager = S3StorageManager()
        self.index_id = None
        self.is_running = False
        self.processed_count = 0
        
    async def start(self):
        """Start the worker"""
        print(f"Worker {self.worker_id} starting...")
        self.is_running = True
        
        # Connect to queue
        if not await self.queue_manager.connect():
            print(f"Worker {self.worker_id} failed to connect to queue")
            return
        
        # Ensure S3 bucket exists
        self.s3_manager.create_bucket_if_not_exists()
        
        # Create or get index
        await self.ensure_index()
        
        # Start processing loop
        await self.process_loop()
    
    async def stop(self):
        """Stop the worker"""
        print(f"Worker {self.worker_id} stopping...")
        self.is_running = False
        await self.queue_manager.disconnect()
    
    async def ensure_index(self) -> bool:
        """Ensure TwelveLabs index exists"""
        try:
            index_name = "video_analysis_index"
            
            # Check if index already exists
            indexes = self.client.index.list()
            for index in indexes:
                if index.name == index_name:
                    self.index_id = index.id
                    print(f"Worker {self.worker_id} using existing index: {index_name}")
                    return True
            
            # Create new index
            index = self.client.index.create(
                name=index_name,
                models=[
                    {
                        "name": "pegasus1.2",
                        "options": ["visual", "audio"]
                    }
                ]
            )
            
            self.index_id = index.id
            print(f"Worker {self.worker_id} created new index: {index_name} (ID: {index.id})")
            return True
            
        except Exception as e:
            print(f"Worker {self.worker_id} error creating index: {e}")
            return False
    
    async def process_loop(self):
        """Main processing loop"""
        print(f"Worker {self.worker_id} entering processing loop...")
        
        while self.is_running:
            try:
                # Get next video segment from queue
                job = await self.queue_manager.get_video_segment(timeout=5)
                
                if job:
                    print(f"Worker {self.worker_id} processing: {job['video_path']}")
                    result = await self.process_video_segment(job)
                    
                    if result and "error" not in result:
                        self.processed_count += 1
                        print(f"Worker {self.worker_id} completed job {self.processed_count}: {job['video_path']}")
                    else:
                        print(f"Worker {self.worker_id} failed to process: {job['video_path']}")
                
                else:
                    # No jobs available, short sleep
                    await asyncio.sleep(1)
                    
            except asyncio.CancelledError:
                print(f"Worker {self.worker_id} was cancelled")
                break
            except Exception as e:
                print(f"Worker {self.worker_id} error in processing loop: {e}")
                await asyncio.sleep(2)
    
    async def process_video_segment(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single video segment"""
        try:
            video_path = job["video_path"]
            metadata = job.get("metadata", {})
            
            # Check if file exists
            if not os.path.exists(video_path):
                return {"error": f"Video file not found: {video_path}"}
            
            # Run TwelveLabs upload and S3 upload in parallel
            upload_tasks = await asyncio.gather(
                self.upload_video(video_path, metadata),
                asyncio.get_event_loop().run_in_executor(
                    None, 
                    self.s3_manager.upload_video_segment, 
                    video_path
                ),
                return_exceptions=True
            )
            
            video_id, s3_url = upload_tasks
            
            # Check if uploads succeeded
            if isinstance(video_id, Exception) or not video_id:
                return {"error": f"Failed to upload to TwelveLabs: {video_id}"}
            
            if isinstance(s3_url, Exception) or not s3_url:
                print(f"⚠️ S3 upload failed: {s3_url}, continuing without S3 URL")
                s3_url = None
            
            # Analyze video
            analysis = await self.analyze_video(video_id, job.get("timestamp", time.time()))
            
            # Add processing metadata
            analysis["worker_id"] = self.worker_id
            analysis["source_file"] = video_path
            analysis["s3_url"] = s3_url
            analysis["file_size"] = os.path.getsize(video_path)
            analysis["processed_at"] = datetime.now().isoformat()
            
            # Save analysis
            analysis_filename = f"analysis_{Path(video_path).stem}_worker{self.worker_id}.json"
            analysis_path = await self.save_analysis(analysis, analysis_filename)
            analysis["analysis_file"] = analysis_path
            
            return analysis
            
        except Exception as e:
            print(f"Worker {self.worker_id} error processing video segment: {e}")
            return {"error": str(e), "video_path": job.get("video_path", "unknown")}
    
    async def upload_video(self, video_path: str, metadata: Dict = None) -> Optional[str]:
        """Upload video to TwelveLabs"""
        try:
            if not self.index_id:
                await self.ensure_index()
            
            print(f"Worker {self.worker_id} uploading video: {video_path}")
            
            # Create video indexing task
            task = self.client.task.create(
                index_id=self.index_id,
                file=video_path
            )
            
            print(f"Worker {self.worker_id} upload task created: {task.id}")
            
            # Wait for processing to complete
            def print_status(task):
                print(f"Worker {self.worker_id} status: {task.status}")
            
            task.wait_for_done(
                sleep_interval=2,
                callback=print_status
            )
            
            if task.status == "ready":
                print(f"Worker {self.worker_id} video processed successfully: {task.video_id}")
                return task.video_id
            else:
                print(f"Worker {self.worker_id} video processing failed: {task.status}")
                return None
                
        except Exception as e:
            print(f"Worker {self.worker_id} error uploading video: {e}")
            return None
    
    async def analyze_video(self, video_id: str, timestamp: float) -> Dict:
        """Analyze video using TwelveLabs Pegasus"""
        try:
            # Generate detailed summary
            generation_result = self.client.generate.text(
                video_id=video_id,
                prompt="Provide a detailed summary of what's happening in this video segment, including any people, objects, actions, and conversations."
            )
            
            # Return simplified format
            analysis_results = {
                "video_id": str(uuid.uuid4()),  # Generate unique UUID
                "timestamp": timestamp,
                "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                "detailed_summary": generation_result.data
            }
            
            return analysis_results
            
        except Exception as e:
            print(f"Worker {self.worker_id} error analyzing video: {e}")
            return {
                "video_id": str(uuid.uuid4()),
                "timestamp": timestamp,
                "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                "detailed_summary": f"Error: {str(e)}"
            }
    
    async def save_analysis(self, analysis: Dict, filename: str = None) -> str:
        """Save analysis results to JSON file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"analysis_{timestamp}_worker{self.worker_id}.json"
            
            filepath = self.output_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
            
            print(f"Worker {self.worker_id} analysis saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"Worker {self.worker_id} error saving analysis: {e}")
            return None