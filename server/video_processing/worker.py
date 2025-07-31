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
from config import Config
from database.supabase_client import SupabaseManager
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.models.memory import MemoryPoint
from automations.automation_controller import AutomationController
# from performance_monitor import performance_monitor  # Removed


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
        self.automation_controller = AutomationController()
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
                models=[{"name": "pegasus1.2", "options": ["visual", "audio"]}],
            )

            self.index_id = index.id
            print(
                f"Worker {self.worker_id} created new index: {index_name} (ID: {index.id})"
            )
            return True

        except Exception as e:
            print(f"Worker {self.worker_id} error creating index: {e}")
            return False

    async def process_loop(self):
        """Main processing loop"""
        print(f"Worker {self.worker_id} entering processing loop...")

        while self.is_running:
            try:
                # Get next video segment from queue with optimized timeout
                job = await self.queue_manager.get_video_segment()

                if job:
                    print(f"Worker {self.worker_id} processing: {job['video_path']}")
                    print(f"Worker {self.worker_id} job metadata: {job}")

                    result = await self.process_video_segment(job)

                    if result and "error" not in result:
                        self.processed_count += 1

                        # Track processing timing
                        # performance_monitor.track_segment_timing(  # Removed
                        #     result.get("video_id", f"job_{self.processed_count}"),
                        #     processing_start,
                        #     processing_end,
                        #     "total_processing"
                        # )

                        print(
                            f"Worker {self.worker_id} completed job {self.processed_count}: {job['video_path']}"
                        )
                    else:
                        print(
                            f"Worker {self.worker_id} failed to process: {job['video_path']}"
                        )

                        # Track failed processing
                        # performance_monitor.track_segment_timing(  # Removed
                        #     f"failed_job_{time.time()}",
                        #     processing_start,
                        #     processing_end,
                        #     "failed_processing"
                        # )

                else:
                    # No jobs available, short sleep
                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                print(f"Worker {self.worker_id} was cancelled")
                break
            except Exception as e:
                print(f"Worker {self.worker_id} error in processing loop: {e}")
                await asyncio.sleep(2)

    async def process_video_segment(
        self, job: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
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

            # Phase 1: Run TwelveLabs upload, S3 upload, and preprocessing in parallel
            upload_tasks = await asyncio.gather(
                self.upload_video_optimized(video_path, metadata),  # Optimized version
                asyncio.get_event_loop().run_in_executor(
                    None, self.s3_manager.upload_video_segment, video_path
                ),
                # Pre-generate embedding task concurrently
                self.embedding_service.create_video_embedding_task(
                    file_path=video_path
                ),
                return_exceptions=True,
            )

            twelvelabs_video_id, s3_url, embedding_task = upload_tasks

            # Check if uploads succeeded
            if isinstance(twelvelabs_video_id, Exception) or not twelvelabs_video_id:
                return {
                    "error": f"Failed to upload to TwelveLabs: {twelvelabs_video_id}"
                }

            if isinstance(s3_url, Exception) or not s3_url:
                print(f"⚠️ S3 upload failed: {s3_url}, continuing without S3 URL")
                s3_url = None

            # Analyze video and start embedding pipeline in parallel
            # Type assertion since we've already checked it's not an exception
            video_id = str(twelvelabs_video_id) if twelvelabs_video_id else ""

            # Phase 2: Start analysis with optimized async version
            analysis_task = asyncio.create_task(
                self.analyze_video_optimized(
                    video_id, job.get("timestamp", time.time()), linking_uuid
                )
            )

            # Start embedding processing if task was created successfully
            if embedding_task and not isinstance(embedding_task, Exception):
                embedding_future = asyncio.create_task(
                    self.process_embedding_task(
                        embedding_task,
                        video_path,
                        linking_uuid,
                        job.get("timestamp", time.time()),
                    )
                )
            else:
                embedding_future = None

            # Wait for analysis to complete
            analysis = await analysis_task

            # Add processing metadata
            analysis["worker_id"] = self.worker_id
            analysis["source_file"] = video_path
            analysis["s3_url"] = s3_url
            analysis["file_size"] = os.path.getsize(video_path)
            analysis["processed_at"] = datetime.now().isoformat()
            analysis["twelvelabs_video_id"] = twelvelabs_video_id
            analysis["linking_uuid"] = linking_uuid

            # Phase 3: Start Supabase storage and automations in parallel
            user_id = job.get("metadata", {}).get("user_id")
            timestamp = job.get("timestamp", time.time())
            
            # Start Supabase storage task
            supabase_task = asyncio.create_task(
                self.supabase_manager.insert_video_analysis(analysis, user_id)
            )
            
            # Start automation task if we have a summary
            automation_task = None
            summary = analysis.get("detailed_summary", "")
            if summary:
                automation_metadata = {
                    "video_id": linking_uuid,
                    "user_id": user_id,
                    "timestamp": analysis.get("datetime"),
                    "source": "video_processing",
                    "worker_id": self.worker_id,
                }
                automation_task = asyncio.create_task(
                    self.run_automations_with_retry(
                        video_id=linking_uuid,
                        summary=summary,
                        metadata=automation_metadata,
                    )
                )

            # Wait for Supabase storage (critical path)
            supabase_uuid = await supabase_task

            if supabase_uuid:
                print(f"Worker {self.worker_id} stored analysis in Supabase: {supabase_uuid}")
                analysis["supabase_stored"] = True
                
                # Continue embedding processing in background
                if embedding_future:
                    asyncio.create_task(
                        self.finalize_embedding(embedding_future, linking_uuid)
                    )
                else:
                    asyncio.create_task(
                        self.embed_and_store_video_with_retry(
                            video_path=video_path,
                            linking_uuid=linking_uuid,
                            timestamp=timestamp,
                        )
                    )
                
                # Log automation results (non-blocking)
                if automation_task:
                    asyncio.create_task(
                        self._log_automation_completion(automation_task, linking_uuid)
                    )
            else:
                print(f"Worker {self.worker_id} failed to store in Supabase")
                analysis["supabase_stored"] = False

            return analysis

        except Exception as e:
            print(f"Worker {self.worker_id} error processing video segment: {e}")
            return {"error": str(e), "video_path": job.get("video_path", "unknown")}

    async def upload_video_optimized(
        self, video_path: str, metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """Optimized async video upload to TwelveLabs with faster polling"""
        try:
            if not self.index_id:
                await self.ensure_index()

            if not self.index_id:
                raise ValueError("Index ID not available")
                
            print(f"Worker {self.worker_id} uploading video: {video_path}")

            # Create video indexing task
            task = self.client.task.create(index_id=self.index_id, file=video_path)
            print(f"Worker {self.worker_id} upload task created: {task.id}")

            # Optimized async polling with shorter intervals
            video_id = await self._wait_for_task_optimized(
                task, polling_interval=0.5  # Reduced from 1.0s to 0.5s
            )

            if video_id:
                print(f"Worker {self.worker_id} video processed: {video_id}")
                return video_id
            else:
                print(f"Worker {self.worker_id} video processing failed")
                return None

        except Exception as e:
            print(f"Worker {self.worker_id} error uploading video: {e}")
            return None

    async def upload_video(
        self, video_path: str, metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """Upload video to TwelveLabs"""
        try:
            if not self.index_id:
                await self.ensure_index()

            print(f"Worker {self.worker_id} uploading video: {video_path}")

            # Create video indexing task
            if not self.index_id:
                raise ValueError("Index ID not available")
            task = self.client.task.create(index_id=self.index_id, file=video_path)

            print(f"Worker {self.worker_id} upload task created: {task.id}")

            # Wait for processing to complete with async polling
            def print_status(task):
                print(f"Worker {self.worker_id} status: {task.status}")

            # Use async polling to avoid blocking the entire worker
            polling_interval = getattr(Config, "TWELVELABS_POLLING_INTERVAL", 1.0)
            video_id = await self._wait_for_task_async(
                task, polling_interval, print_status
            )

            if video_id:
                print(
                    f"Worker {self.worker_id} video processed successfully: {video_id}"
                )
                return video_id
            else:
                print(f"Worker {self.worker_id} video processing failed")
                return None

            # The async wait already handles the return logic

        except Exception as e:
            print(f"Worker {self.worker_id} error uploading video: {e}")
            return None

    async def _wait_for_task_async(
        self, task, sleep_interval: float, callback=None
    ) -> Optional[str]:
        """Async version of task.wait_for_done to prevent blocking"""
        max_wait_time = 180  # 3 minutes max wait
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            try:
                # Get fresh task status from API
                current_task = self.client.task.retrieve(task.id)

                if callback:
                    callback(current_task)

                if current_task.status == "ready":
                    return current_task.video_id
                elif current_task.status in ["failed", "error"]:
                    print(f"Worker {self.worker_id} task failed: {current_task.status}")
                    return None

                # Use asyncio.sleep instead of time.sleep to yield control
                await asyncio.sleep(sleep_interval)

            except Exception as e:
                print(f"Worker {self.worker_id} error checking task status: {e}")
                await asyncio.sleep(sleep_interval)

        print(f"Worker {self.worker_id} task timed out after {max_wait_time}s")
        return None

    async def _wait_for_task_optimized(
        self, task, polling_interval: float = 0.5
    ) -> Optional[str]:
        """Optimized async task waiting with adaptive polling"""
        max_wait_time = 180  # 3 minutes max wait
        start_time = time.time()
        consecutive_failures = 0
        
        # Adaptive polling: start fast, slow down if needed
        current_interval = polling_interval
        max_interval = 2.0

        while time.time() - start_time < max_wait_time:
            try:
                # Get fresh task status from API
                current_task = self.client.task.retrieve(task.id)
                consecutive_failures = 0  # Reset on success

                if current_task.status == "ready":
                    return current_task.video_id
                elif current_task.status in ["failed", "error"]:
                    print(f"Worker {self.worker_id} task failed: {current_task.status}")
                    return None
                elif current_task.status == "processing":
                    # Speed up polling during active processing
                    current_interval = min(polling_interval, current_interval)
                else:
                    # Slow down for pending states
                    current_interval = min(max_interval, current_interval * 1.2)

                await asyncio.sleep(current_interval)

            except Exception as e:
                consecutive_failures += 1
                print(f"Worker {self.worker_id} error checking task status: {e}")
                
                # Exponential backoff on failures
                failure_backoff = min(max_interval, 0.1 * (2 ** consecutive_failures))
                await asyncio.sleep(failure_backoff)

        print(f"Worker {self.worker_id} task timed out after {max_wait_time}s")
        return None

    async def analyze_video_optimized(
        self, video_id: str, timestamp: float, linking_uuid: str
    ) -> Dict:
        """Optimized async video analysis using TwelveLabs Pegasus with retry logic"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Run in executor to avoid blocking
                loop = asyncio.get_event_loop()
                generation_result = await loop.run_in_executor(
                    None,
                    lambda: self.client.generate.text(
                        video_id=video_id,
                        prompt="Provide a detailed summary of what's happening in this video segment, including any people, objects, actions, and conversations.",
                    )
                )

                return {
                    "video_id": linking_uuid,
                    "timestamp": timestamp,
                    "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                    "detailed_summary": generation_result.data,
                }

            except Exception as e:
                print(f"Worker {self.worker_id} analysis attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))  # Progressive backoff
                    continue
                
                # Final attempt failed
                return {
                    "video_id": linking_uuid,
                    "timestamp": timestamp,
                    "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                    "detailed_summary": f"Error after {max_retries} attempts: {str(e)}",
                }

    async def analyze_video(
        self, video_id: str, timestamp: float, linking_uuid: str
    ) -> Dict:
        """Analyze video using TwelveLabs Pegasus"""
        try:
            # Generate detailed summary
            generation_result = self.client.generate.text(
                video_id=video_id,
                prompt="Provide a detailed summary of what's happening in this video segment, including any people, objects, actions, and conversations.",
            )

            # Return simplified format with linking UUID
            analysis_results = {
                "video_id": linking_uuid,  # Use linking UUID for consistency
                "timestamp": timestamp,
                "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                "detailed_summary": generation_result.data,
            }

            return analysis_results

        except Exception as e:
            print(f"Worker {self.worker_id} error analyzing video: {e}")
            return {
                "video_id": linking_uuid,  # Use linking UUID even for errors
                "timestamp": timestamp,
                "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                "detailed_summary": f"Error: {str(e)}",
            }

    async def embed_and_store_video(
        self, video_path: str, linking_uuid: str, timestamp: float
    ) -> bool:
        """Embed video and store in vector database"""
        try:
            print(f"Worker {self.worker_id} starting video embedding for: {video_path}")

            # Generate video embedding
            embedding_result = (
                await self.embedding_service.process_video_embedding_pipeline(
                    file_path=video_path
                )
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

            if hasattr(task_result, "video_embedding") and task_result.video_embedding:
                video_embedding_obj = task_result.video_embedding
                print(f"Worker {self.worker_id} found video_embedding attribute")

                if (
                    hasattr(video_embedding_obj, "segments")
                    and video_embedding_obj.segments
                ):
                    first_segment = video_embedding_obj.segments[0]
                    if hasattr(first_segment, "embeddings_float"):
                        video_embedding = first_segment.embeddings_float
                    else:
                        return False
                else:
                    return False
            else:
                return False

            if not video_embedding:
                print(
                    f"Worker {self.worker_id} could not extract video embedding from task result"
                )
                return False

            # Create memory point for vector storage
            # TODO: Get user_id from metadata
            user_id = "3561affa-b551-483c-be4d-a35c7b57a3fb"

            memory = MemoryPoint(
                id=UUID(linking_uuid),  # Use the same UUID as Supabase
                user_id=UUID(user_id),
                content=video_path,
                content_type="video",
                timestamp=datetime.fromtimestamp(timestamp),
                metadata={},
                tags=[],
                source_id=None,
                embedding=video_embedding,
            )

            # Store in vector database
            success = await self.vector_store.add_memory(memory)

            if success:
                print(
                    f"Worker {self.worker_id} stored video embedding in Qdrant: {linking_uuid}"
                )
                return True
            else:
                print(f"Worker {self.worker_id} failed to store video embedding")
                return False

        except Exception as e:
            print(f"Worker {self.worker_id} error embedding video: {e}")
            return False

    async def embed_and_store_video_with_retry(
        self, video_path: str, linking_uuid: str, timestamp: float, max_retries: int = 3
    ) -> bool:
        """Embed video with retry logic"""
        for attempt in range(max_retries):
            try:
                success = await self.embed_and_store_video(
                    video_path, linking_uuid, timestamp
                )
                if success:
                    return True
            except Exception as e:
                print(
                    f"Worker {self.worker_id} embedding attempt {attempt + 1} failed: {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff

        return False

    async def process_embedding_task(
        self, embedding_task, video_path: str, linking_uuid: str, timestamp: float
    ) -> bool:
        """Process pre-created embedding task to completion"""
        try:
            # Wait for embedding completion
            final_status = await self.embedding_service.wait_for_embedding_completion(
                embedding_task
            )

            if final_status != "ready":
                print(f"Worker {self.worker_id} embedding task failed: {final_status}")
                return False

            # Retrieve embeddings
            embeddings = await self.embedding_service.retrieve_video_embeddings(
                embedding_task
            )

            if not embeddings:
                return False

            # Store in vector database
            return await self.store_embedding_in_vector_db(
                embeddings, linking_uuid, timestamp, video_path
            )

        except Exception as e:
            print(f"Worker {self.worker_id} error processing embedding task: {e}")
            return False

    async def finalize_embedding(self, embedding_future, linking_uuid: str) -> None:
        """Finalize embedding processing when ready"""
        try:
            success = await embedding_future
            if success:
                print(
                    f"Worker {self.worker_id} embedding pipeline completed for: {linking_uuid}"
                )
            else:
                print(
                    f"Worker {self.worker_id} embedding pipeline failed for: {linking_uuid}"
                )
        except Exception as e:
            print(f"Worker {self.worker_id} error finalizing embedding: {e}")

    async def store_embedding_in_vector_db(
        self, embeddings, linking_uuid: str, timestamp: float, video_path: str
    ) -> bool:
        """Store embeddings in vector database"""
        try:
            task_result = embeddings.get("embeddings")
            if not task_result:
                return False

            video_embedding = None

            if hasattr(task_result, "video_embedding") and task_result.video_embedding:
                video_embedding_obj = task_result.video_embedding

                if (
                    hasattr(video_embedding_obj, "segments")
                    and video_embedding_obj.segments
                ):
                    first_segment = video_embedding_obj.segments[0]
                    if hasattr(first_segment, "embeddings_float"):
                        video_embedding = first_segment.embeddings_float

            if not video_embedding:
                return False

            # Create memory point for vector storage
            # Get user_id from job metadata or use a default
            user_id = "3561affa-b551-483c-be4d-a35c7b57a3fb"
            if not user_id:
                return {"error": "No user_id provided in job metadata"}

            memory = MemoryPoint(
                id=UUID(linking_uuid),
                user_id=UUID(user_id),
                content=video_path,
                content_type="video",
                timestamp=datetime.fromtimestamp(timestamp),
                metadata={},
                tags=[],
                source_id=None,
                embedding=video_embedding,
            )

            success = await self.vector_store.add_memory(memory)

            if success:
                print(
                    f"Worker {self.worker_id} stored video embedding in Qdrant: {linking_uuid}"
                )

            return success

        except Exception as e:
            print(f"Worker {self.worker_id} error storing embedding: {e}")
            return False

    async def run_automations_with_retry(
        self, video_id: str, summary: str, metadata: dict, max_retries: int = 2
    ) -> bool:
        """Run automations with retry logic"""
        for attempt in range(max_retries):
            try:
                print(
                    f"Worker {self.worker_id} running automations for: {video_id} (attempt {attempt + 1})"
                )

                automation_result = (
                    await self.automation_controller.process_video_summary(
                        video_id=video_id, summary=summary, metadata=metadata
                    )
                )

                if automation_result and "error" not in automation_result:
                    triggered_automations = automation_result.get(
                        "automations_triggered", []
                    )
                    print(
                        f"Worker {self.worker_id} automation success: {len(triggered_automations)} automations triggered"
                    )
                    return True
                else:
                    print(
                        f"Worker {self.worker_id} automation failed: {automation_result}"
                    )

            except Exception as e:
                print(
                    f"Worker {self.worker_id} automation attempt {attempt + 1} failed: {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # Short retry delay

        print(f"Worker {self.worker_id} automation failed after {max_retries} attempts")
        return False
    
    async def _log_automation_completion(self, automation_task, linking_uuid: str):
        """Log automation completion without blocking main processing"""
        try:
            result = await automation_task
            if result:
                triggered = result.get("automations_triggered", [])
                print(f"Worker {self.worker_id} automations completed for {linking_uuid}: {len(triggered)} triggered")
            else:
                print(f"Worker {self.worker_id} automations failed for {linking_uuid}")
        except Exception as e:
            print(f"Worker {self.worker_id} automation error for {linking_uuid}: {e}")
