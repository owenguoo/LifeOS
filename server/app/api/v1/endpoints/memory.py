from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime
import time
import logging

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from app.schemas.memory import (
    MemoryCreateRequest,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryResponse,
    MemoryDeleteRequest,
    MemoryDeleteResponse,
    ChatbotQueryRequest,
    ChatbotQueryResponse,
)
from app.models.memory import MemoryPoint
from app.services.vector_store import vector_store
from app.services.embedding_service import embedding_service
from app.services.text_embedding_service import text_embedding_service
from app.services.openai_service import openai_service
from database.supabase_client import SupabaseManager
from app.middleware.simple_auth import get_current_user
from app.schemas.simple_auth import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Supabase manager
supabase_manager = SupabaseManager()

# User ID now comes from authentication


@router.post("/create", response_model=MemoryResponse)
async def create_memory(request: MemoryCreateRequest, current_user: User = Depends(get_current_user)):
    """Create a new memory with vector embedding"""
    try:
        # Process video file/URL to get embedding
        if request.content.startswith(("http://", "https://")):
            # Process video URL
            embedding_result = await embedding_service.process_video_embedding_pipeline(
                video_url=request.content
            )
        else:
            # Assume content is a file path
            embedding_result = await embedding_service.process_video_embedding_pipeline(
                file_path=request.content
            )

        if not embedding_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate video embedding",
            )

        # Extract the video embedding from the result
        embedding = embedding_result.get("video_embedding")
        if not embedding:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No video embedding found in result",
            )

        # Create memory point
        memory = MemoryPoint(
            user_id=UUID(current_user.id),
            content=request.content,  # This will be the video file path or URL
            content_type="video",  # Always video since we only store videos
            timestamp=datetime.utcnow(),
            metadata={},  # Not stored in vector payload
            tags=[],  # Not stored in vector payload
            source_id=None,  # Not stored in vector payload
            embedding=embedding,
        )

        # Store in vector database
        success = await vector_store.add_memory(memory)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store memory",
            )

        # Return response
        return MemoryResponse(
            id=memory.id,
            content=memory.content,
            content_type=memory.content_type,
            timestamp=memory.timestamp,
            metadata=memory.metadata,
            tags=memory.tags,
            source_id=memory.source_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/search", response_model=MemorySearchResponse)
async def search_memories(request: MemorySearchRequest, current_user: User = Depends(get_current_user)):
    """Search memories using semantic similarity"""
    try:
        start_time = time.time()

        # Generate embedding for search query using text embedding service
        query_embedding = await text_embedding_service.get_embedding(request.query)
        if not query_embedding:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate query embedding",
            )

        # Search memories
        results = await vector_store.search_memories(
            user_id="3561affa-b551-483c-be4d-a35c7b57a3fb",
            # user_id=UUID(current_user.id),
            query_vector=query_embedding,
            limit=request.limit,
            date_from=request.date_from,
            date_to=request.date_to,
            score_threshold=request.score_threshold or 0.01,
        )

        # Convert to response format and fetch Supabase data
        enriched_results = []
        for result in results:
            # Fetch full video data from Supabase using video_id
            video_data = await supabase_manager.get_video_analysis(result.video_id)

            if video_data:
                enriched_result = {
                    "id": str(result.id),
                    "video_id": result.video_id,
                    "timestamp": result.timestamp.isoformat(),
                    "score": result.score,
                    # Add Supabase data
                    "s3_url": video_data.get("s3_link"),
                    "detailed_summary": video_data.get("detailed_summary"),
                    "file_size": video_data.get("file_size"),
                    "processed_at": video_data.get("processed_at"),
                    "user_id": video_data.get("user_id"),
                }
            else:
                # Fallback if Supabase data not found
                enriched_result = {
                    "id": str(result.id),
                    "video_id": result.video_id,
                    "timestamp": result.timestamp.isoformat(),
                    "score": result.score,
                    "s3_url": None,
                    "detailed_summary": "Data not found",
                    "file_size": None,
                    "processed_at": None,
                    "user_id": None,
                }

            enriched_results.append(enriched_result)

        search_time = (time.time() - start_time) * 1000

        return MemorySearchResponse(
            results=enriched_results,
            total_found=len(results),
            query=request.query,
            search_time_ms=search_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/chatbot", response_model=ChatbotQueryResponse)
async def chatbot_query(request: ChatbotQueryRequest, current_user: User = Depends(get_current_user)):
    """Chatbot endpoint that refines user input and finds the best matching video"""
    try:
        start_time = time.time()

        # Step 1: Refine the user input using OpenAI
        refined_query = openai_service.refine_query(request.user_input)
        if not refined_query:
            # Fallback to original input if OpenAI fails
            refined_query = request.user_input

        # Step 2: Generate embedding for the refined query
        query_embedding = await text_embedding_service.get_embedding(refined_query)
        if not query_embedding:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate query embedding",
            )

        # Step 3: Search for top 10 matches
        results = await vector_store.search_memories(
            user_id=UUID(current_user.id),
            query_vector=query_embedding,
            limit=10,  # Get top 10 matches
            score_threshold=request.confidence_threshold or 0.01,
        )

        processing_time = (time.time() - start_time) * 1000

        # Step 4: Collect context from all relevant videos 
        if results and len(results) > 0:
            # Collect video contexts from all results
            video_contexts = []
            best_match = results[0]  # Keep track of the best match for backwards compatibility
            
            for result in results:
                # Fetch video data from Supabase using video_id
                video_data = await supabase_manager.get_video_analysis(result.video_id)
                
                if video_data:
                    context = {
                        "timestamp": result.timestamp.isoformat(),
                        "summary": video_data.get("detailed_summary", "No summary available"),
                        "confidence_score": result.score,
                        "video_id": result.video_id
                    }
                    video_contexts.append(context)
            
            # Step 5: Generate AI response using all video contexts
            ai_response = openai_service.generate_contextual_response(
                user_question=request.user_input,
                video_contexts=video_contexts
            )
            
            # If we have contexts, return comprehensive response
            if video_contexts:
                return ChatbotQueryResponse(
                    original_input=request.user_input,
                    refined_query=refined_query,
                    video_found=True,
                    ai_response=ai_response,
                    video_id=best_match.video_id,  # Still include best match for backwards compatibility
                    timestamp=best_match.timestamp.isoformat(),
                    summary=video_contexts[0].get("summary") if video_contexts else None,
                    confidence_score=best_match.score,
                    processing_time_ms=processing_time,
                )
            else:
                # Vector results found but no Supabase data
                return ChatbotQueryResponse(
                    original_input=request.user_input,
                    refined_query=refined_query,
                    video_found=True,
                    ai_response="I found some relevant videos but couldn't access their detailed summaries.",
                    video_id=best_match.video_id,
                    timestamp=best_match.timestamp.isoformat(),
                    summary="Video found but detailed summary not available",
                    confidence_score=best_match.score,
                    processing_time_ms=processing_time,
                )
        else:
            # No matching video found
            return ChatbotQueryResponse(
                original_input=request.user_input,
                refined_query=refined_query,
                video_found=False,
                ai_response="I couldn't find any relevant videos to answer your question.",
                processing_time_ms=processing_time,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chatbot query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/health")
async def health_check():
    """Health check for vector store and embedding service"""
    try:
        vector_health = await vector_store.health_check()
        video_embedding_health = embedding_service.health_check()
        text_embedding_health = text_embedding_service.health_check()
        openai_health = openai_service.health_check()

        return {
            "vector_store": "healthy" if vector_health else "unhealthy",
            "video_embedding_service": (
                "healthy" if video_embedding_health else "unhealthy"
            ),
            "text_embedding_service": (
                "healthy" if text_embedding_health else "unhealthy"
            ),
            "openai_service": "healthy" if openai_health else "unhealthy",
            "overall": (
                "healthy"
                if vector_health
                and video_embedding_health
                and text_embedding_health
                and openai_health
                else "unhealthy"
            ),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "vector_store": "unhealthy",
            "video_embedding_service": "unhealthy",
            "text_embedding_service": "unhealthy",
            "openai_service": "unhealthy",
            "overall": "unhealthy",
        }


@router.delete("/delete", response_model=MemoryDeleteResponse)
async def delete_memories(request: MemoryDeleteRequest):
    """Delete memories by their IDs"""
    try:
        successful, failed, errors = await vector_store.delete_memories(
            request.memory_ids
        )

        return MemoryDeleteResponse(
            deleted_count=successful, failed_count=failed, errors=errors
        )

    except Exception as e:
        logger.error(f"Error deleting memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/stats/collection")
async def get_collection_stats():
    """Get vector collection statistics"""
    try:
        stats = await vector_store.get_collection_stats()
        return stats

    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(memory_id: UUID):
    """Get a specific memory by ID"""
    try:
        memory = await vector_store.get_memory(memory_id)
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found"
            )

        return MemoryResponse(
            id=memory.id,
            content=memory.content,
            content_type=memory.content_type,
            timestamp=memory.timestamp,
            metadata=memory.metadata,
            tags=memory.tags,
            source_id=memory.source_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/recent-videos")
async def get_recent_videos():
    """Get recent videos"""
    try:
        # Query Supabase for recent videos
        recent_videos = await supabase_manager.get_recent_videos(limit=50)

        return {
            "total_videos": len(recent_videos),
            "recent_videos": recent_videos[:10],  # Show last 10
        }

    except Exception as e:
        logger.error(f"Error getting recent videos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent videos: {str(e)}",
        )
