from typing import List, Optional, Dict, Any, Callable
import logging
import asyncio
from twelvelabs import TwelveLabs
from app.config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating video embeddings using TwelveLabs API"""
    
    def __init__(self):
        if not settings.twelvelabs_api_key:
            raise ValueError("TwelveLabs API key is required")
        self.client = TwelveLabs(api_key=settings.twelvelabs_api_key)
    
    async def create_video_embedding_task(
        self, 
        file_path: Optional[str] = None,
        video_url: Optional[str] = None,
        start_offset_sec: Optional[float] = None,
        end_offset_sec: Optional[float] = None,
        clip_length: Optional[float] = None,
        scopes: Optional[List[str]] = None
    ) -> Optional[Any]:
        """Create a video embedding task using TwelveLabs"""
        try:
            print(f"   📁 Using file: {file_path}" if file_path else f"   🌐 Using URL: {video_url}")
            
            # Default scopes if not provided
            if scopes is None:
                scopes = ['clip', 'video']
            
            print(f"   🎯 Embedding scopes: {scopes}")
            
            # Create embedding task parameters
            if file_path:
                params = {
                    "video_file": file_path,
                    "video_embedding_scopes": scopes
                }
            else:
                params = {
                    "video_url": video_url,
                    "video_embedding_scopes": scopes
                }
            
            # Add optional parameters if provided
            if start_offset_sec is not None:
                params["video_start_offset_sec"] = start_offset_sec
            if end_offset_sec is not None:
                params["video_end_offset_sec"] = end_offset_sec
            if clip_length is not None:
                params["video_clip_length"] = int(clip_length)
            
            # Create the embedding task using the correct API path
            print("   🤖 Calling TwelveLabs API to create embedding task...")
            task = self.client.embed.task.create(
                model_name="Marengo-retrieval-2.7",
                **params
            )
            
            if task:
                print(f"   ✅ Created task: id={task.id} model_name={task.model_name} status={task.status}")
                logger.info(f"Created video embedding task: {task.id}")
                return task
            else:
                logger.error("Failed to create embedding task - no task returned")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create video embedding task: {e}")
            return None
    
    async def get_embedding_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a video embedding task"""
        try:
            status = self.client.embed.task.status(task_id)
            
            if status:
                logger.info(f"Task {task_id} status: {status.status}")
                return {
                    "task_id": task_id,
                    "status": status.status,
                    "progress": getattr(status, 'progress', None),
                    "created_at": getattr(status, 'created_at', None),
                    "updated_at": getattr(status, 'updated_at', None)
                }
            else:
                logger.error(f"Failed to get status for task {task_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get embedding task status: {e}")
            return None
    
    async def wait_for_embedding_completion(
        self, 
        task, 
        sleep_interval: int = 5,
        callback: Optional[Callable] = None
    ) -> Optional[str]:
        """Wait for a video embedding task to complete"""
        try:
            print(f"   ⏰ Waiting for task completion (checking every {sleep_interval}ms)...")
            
            # Define callback function to monitor status
            def on_task_update(task_obj):
                print(f"   🔍 Status={task_obj.status}")
            
            # Wait for completion using the task object directly
            final_status = task.wait_for_done(
                sleep_interval=sleep_interval,
                callback=on_task_update
            )
            
            print(f"   ✅ Task completed with status: {final_status}")
            logger.info(f"Task completed with status: {final_status}")
            return final_status
            
        except Exception as e:
            logger.error(f"Failed to wait for embedding completion: {e}")
            return None
    
    async def retrieve_video_embeddings(
        self, 
        task,
        embedding_options: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve video embeddings for a completed task"""
        try:
            # Default embedding options if not provided
            if embedding_options is None:
                embedding_options = ['visual-text', 'audio']
            
            print(f"   📊 Retrieving embeddings with options: {embedding_options}")
            
            print("   🔄 Retrieving embeddings from TwelveLabs...")
            # Retrieve embeddings using the task object directly
            embeddings_task = task.retrieve(
                embedding_option=embedding_options
            )
            
            if embeddings_task:
                logger.info(f"Retrieved embeddings for task {task.id}")
                return {
                    "task_id": task.id,
                    "embeddings": embeddings_task,
                    "clips": getattr(embeddings_task, 'clips', []),
                    "video_embedding": getattr(embeddings_task, 'video_embedding', None)
                }
            else:
                logger.error(f"Failed to retrieve embeddings for task {task.id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve video embeddings: {e}")
            return None
    
    async def process_video_embedding_pipeline(
        self, 
        file_path: Optional[str] = None,
        video_url: Optional[str] = None,
        start_offset_sec: Optional[float] = None,
        end_offset_sec: Optional[float] = None,
        clip_length: Optional[float] = None,
        embedding_options: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Complete pipeline: create task, wait for completion, and retrieve embeddings"""
        print("🚀 Starting video embedding pipeline...")
        
        # Validate that either file_path or video_url is provided
        if not file_path and not video_url:
            raise ValueError("Either file_path or video_url must be provided")
        if file_path and video_url:
            raise ValueError("Only one of file_path or video_url should be provided")
        
        try:
            # Step 1: Create embedding task
            print("📝 Step 1: Creating video embedding task...")
            task = await self.create_video_embedding_task(
                file_path=file_path,
                video_url=video_url,
                start_offset_sec=start_offset_sec,
                end_offset_sec=end_offset_sec,
                clip_length=clip_length
            )
            
            if not task:
                print("❌ Failed to create embedding task")
                return None
            
            print(f"✅ Step 1 complete: Created task with ID: {task.id}")
            
            # Step 2: Wait for completion
            print("⏳ Step 2: Waiting for embedding task to complete...")
            final_status = await self.wait_for_embedding_completion(task)
            
            if final_status != "ready":
                print(f"❌ Step 2 failed: Embedding task failed with status: {final_status}")
                logger.error(f"Embedding task failed with status: {final_status}")
                return None
            
            print("✅ Step 2 complete: Embedding task finished successfully")
            
            # Step 3: Retrieve embeddings
            print("📊 Step 3: Retrieving video embeddings...")
            embeddings = await self.retrieve_video_embeddings(
                task=task,
                embedding_options=embedding_options
            )
            
            if embeddings:
                print("✅ Step 3 complete: Successfully retrieved embeddings")
                print("🎉 Pipeline completed successfully!")
            else:
                print("❌ Step 3 failed: Failed to retrieve embeddings")
            
            return embeddings
            
        except Exception as e:
            print(f"❌ Pipeline failed with error: {e}")
            logger.error(f"Failed to process video embedding pipeline: {e}")
            return None
    
    def health_check(self) -> bool:
        """Check if the embedding service is healthy"""
        return settings.twelvelabs_api_key is not None


# Global embedding service instance
embedding_service = EmbeddingService()

# if __name__ == "__main__":
#     import os
#     # Get the directory where this script is located
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     # Construct the full path to the test video
#     test_video_path = os.path.join(script_dir, "test.mp4")
    
#     result = asyncio.run(embedding_service.process_video_embedding_pipeline(
#         file_path=test_video_path,
#     ))
#     print(result)