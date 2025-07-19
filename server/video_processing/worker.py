"""
Async worker for processing video segments from Redis queue
"""
import asyncio
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
from twelvelabs import TwelveLabs
from video_queue.queue_manager import VideoQueueManager
from video_injestion.s3_storage import S3StorageManager
from database.supabase_client import SupabaseManager
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.models.memory import MemoryPoint


class VideoProcessingWorker:
    """Async worker that processes video segments from Redis queue"""
    
    def __init__(self, worker_id: int, api_key: str):
        self.worker_id = worker_id
        self.client = TwelveLabs(api_key=api_key)
        self.queue_manager = VideoQueueManager()
        self.s3_manager = S3StorageManager()
        self.supabase_manager = SupabaseManager()
        self.embedding_service = embedding_service
        self.vector_store = vector_store
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
                print("Getting video segment from queue")
                job = await self.queue_manager.get_video_segment(timeout=5)
                print("Got video segment from queue")
                
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
            
            # Generate linking UUID first to avoid bottleneck
            linking_uuid = self.supabase_manager.generate_linking_uuid()
            print(f"Worker {self.worker_id} generated linking UUID: {linking_uuid}")
            
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
            
            twelvelabs_video_id, s3_url = upload_tasks
            
            # Check if uploads succeeded
            if isinstance(twelvelabs_video_id, Exception) or not twelvelabs_video_id:
                return {"error": f"Failed to upload to TwelveLabs: {twelvelabs_video_id}"}
            
            if isinstance(s3_url, Exception) or not s3_url:
                print(f"⚠️ S3 upload failed: {s3_url}, continuing without S3 URL")
                s3_url = None
            
            # Analyze video (this awaits completion of both uploads)
            # Type assertion since we've already checked it's not an exception
            video_id = str(twelvelabs_video_id) if twelvelabs_video_id else ""
            analysis = await self.analyze_video(video_id, job.get("timestamp", time.time()), linking_uuid)
            
            # Add processing metadata
            analysis["worker_id"] = self.worker_id
            analysis["source_file"] = video_path
            analysis["s3_url"] = s3_url
            analysis["file_size"] = os.path.getsize(video_path)
            analysis["processed_at"] = datetime.now().isoformat()
            analysis["twelvelabs_video_id"] = twelvelabs_video_id
            analysis["linking_uuid"] = linking_uuid
            
            # Store in Supabase instead of local file
            user_id = job.get("user_id")
            supabase_uuid = await self.supabase_manager.insert_video_analysis(analysis, user_id)
            
            if supabase_uuid:
                print(f"Worker {self.worker_id} stored analysis in Supabase: {supabase_uuid}")
                analysis["supabase_stored"] = True
                
                # Asynchronously embed and store vector with retry (don't block processing)
                asyncio.create_task(
                    self.embed_and_store_video_with_retry(
                        video_path=video_path,
                        linking_uuid=linking_uuid,
                        timestamp=job.get("timestamp", time.time())
                    )
                )
            else:
                print(f"Worker {self.worker_id} failed to store in Supabase")
                analysis["supabase_stored"] = False
            
            return analysis
            
        except Exception as e:
            print(f"Worker {self.worker_id} error processing video segment: {e}")
            return {"error": str(e), "video_path": job.get("video_path", "unknown")}
    
    async def upload_video(self, video_path: str, metadata: Optional[Dict] = None) -> Optional[str]:
        """Upload video to TwelveLabs"""
        try:
            if not self.index_id:
                await self.ensure_index()
            
            print(f"Worker {self.worker_id} uploading video: {video_path}")
            
            # Create video indexing task
            if not self.index_id:
                raise ValueError("Index ID not available")
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
    
    async def analyze_video(self, video_id: str, timestamp: float, linking_uuid: str) -> Dict:
        """Analyze video using TwelveLabs Pegasus"""
        try:
            # Generate detailed summary
            generation_result = self.client.generate.text(
                video_id=video_id,
                prompt="Provide a detailed summary of what's happening in this video segment, including any people, objects, actions, and conversations."
            )
            
            # Return simplified format with linking UUID
            analysis_results = {
                "video_id": linking_uuid,  # Use linking UUID for consistency
                "timestamp": timestamp,
                "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                "detailed_summary": generation_result.data
            }
            
            return analysis_results
            
        except Exception as e:
            print(f"Worker {self.worker_id} error analyzing video: {e}")
            return {
                "video_id": linking_uuid,  # Use linking UUID even for errors
                "timestamp": timestamp,
                "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                "detailed_summary": f"Error: {str(e)}"
            }
    
    async def embed_and_store_video(self, video_path: str, linking_uuid: str, timestamp: float) -> bool:
        """Embed video and store in vector database"""
        try:
            print(f"Worker {self.worker_id} starting video embedding for: {video_path}")
            
            # Generate video embedding
            embedding_result = await self.embedding_service.process_video_embedding_pipeline(
                file_path=video_path
            )
            
            if not embedding_result:
                print(f"Worker {self.worker_id} failed to generate video embedding")
                return False
            
            # Extract the embedding from the task result following the tutorial
            task_result = embedding_result.get("embeddings")
            if not task_result:
                print(f"Worker {self.worker_id} no task result found")
                return False

            # Try to extract the embedding vector
            video_embedding = None
            
            if hasattr(task_result, 'video_embedding') and task_result.video_embedding:
                video_embedding_obj = task_result.video_embedding
                print(f"Worker {self.worker_id} found video_embedding attribute")
                
                if hasattr(video_embedding_obj, 'segments') and video_embedding_obj.segments:
                    first_segment = video_embedding_obj.segments[0]
                    if hasattr(first_segment, 'embeddings_float'):
                        video_embedding = first_segment.embeddings_float
                    else:
                        return False
                else:
                    return False
            else:
                return False
            
            if not video_embedding:
                print(f"Worker {self.worker_id} could not extract video embedding from task result")
                return False
            
            # Create memory point for vector storage
            memory = MemoryPoint(
                id=UUID(linking_uuid),  # Use the same UUID as Supabase
                user_id=UUID("8c0ba789-5f7f-4fce-a651-ce08fb6c0024"),  # Demo user ID
                content=video_path,
                content_type="video",
                timestamp=datetime.fromtimestamp(timestamp),
                metadata={},
                tags=[],
                source_id=None,
                embedding=video_embedding
            )
            
            # Store in vector database
            success = await self.vector_store.add_memory(memory)
            
            if success:
                print(f"Worker {self.worker_id} stored video embedding in Qdrant: {linking_uuid}")
                return True
            else:
                print(f"Worker {self.worker_id} failed to store video embedding")
                return False
                
        except Exception as e:
            print(f"Worker {self.worker_id} error embedding video: {e}")
            return False
    
    async def embed_and_store_video_with_retry(self, video_path: str, linking_uuid: str, timestamp: float, max_retries: int = 3) -> bool:
        """Embed video with retry logic"""
        for attempt in range(max_retries):
            try:
                success = await self.embed_and_store_video(video_path, linking_uuid, timestamp)
                if success:
                    return True
            except Exception as e:
                print(f"Worker {self.worker_id} embedding attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return False
    
