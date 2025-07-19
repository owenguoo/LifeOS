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
    MemoryDeleteResponse
)
from app.models.memory import MemoryPoint
from app.services.vector_store import vector_store
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Temporary user ID for demo purposes (in real app, this would come from auth)
DEMO_USER_ID = UUID("8c0ba789-5f7f-4fce-a651-ce08fb6c0024")


@router.post("/create", response_model=MemoryResponse)
async def create_memory(request: MemoryCreateRequest):
    """Create a new memory with vector embedding"""
    try:
        # Generate embedding for the content
        embedding = await embedding_service.get_embedding(request.content)
        if not embedding:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate embedding"
            )
        
        # Create memory point
        memory = MemoryPoint(
            user_id=DEMO_USER_ID,  # In real app, get from auth context
            content=request.content,
            content_type=request.content_type,
            timestamp=datetime.utcnow(),
            metadata=request.metadata,
            tags=request.tags,
            source_id=request.source_id,
            embedding=embedding
        )
        
        # Store in vector database
        success = await vector_store.add_memory(memory)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store memory"
            )
        
        # Return response
        return MemoryResponse(
            id=memory.id,
            content=memory.content,
            content_type=memory.content_type,
            timestamp=memory.timestamp,
            metadata=memory.metadata,
            tags=memory.tags,
            source_id=memory.source_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/search", response_model=MemorySearchResponse)
async def search_memories(request: MemorySearchRequest):
    """Search memories using semantic similarity"""
    try:
        start_time = time.time()
        
        # Generate embedding for search query
        query_embedding = await embedding_service.get_embedding(request.query)
        if not query_embedding:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate query embedding"
            )
        
        # Search memories
        results = await vector_store.search_memories(
            user_id=DEMO_USER_ID,  # In real app, get from auth context
            query_vector=query_embedding,
            limit=request.limit,
            content_types=request.content_types,
            tags=request.tags,
            date_from=request.date_from,
            date_to=request.date_to,
            score_threshold=request.score_threshold or 0.5
        )
        
        # Convert to response format
        response_results = []
        for result in results:
            response_results.append({
                "id": str(result.id),
                "content": result.content,
                "content_type": result.content_type,
                "timestamp": result.timestamp.isoformat(),
                "metadata": result.metadata,
                "tags": result.tags,
                "score": result.score,
                "source_id": result.source_id
            })
        
        search_time = (time.time() - start_time) * 1000
        
        return MemorySearchResponse(
            results=response_results,
            total_found=len(results),
            query=request.query,
            search_time_ms=search_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/health")
async def health_check():
    """Health check for vector store and embedding service"""
    try:
        vector_health = await vector_store.health_check()
        embedding_health = embedding_service.health_check()
        
        return {
            "vector_store": "healthy" if vector_health else "unhealthy",
            "embedding_service": "healthy" if embedding_health else "unhealthy",
            "overall": "healthy" if vector_health and embedding_health else "unhealthy"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "vector_store": "unhealthy",
            "embedding_service": "unhealthy",
            "overall": "unhealthy"
        }





@router.delete("/delete", response_model=MemoryDeleteResponse)
async def delete_memories(request: MemoryDeleteRequest):
    """Delete memories by their IDs"""
    try:
        successful, failed, errors = await vector_store.delete_memories(request.memory_ids)
        
        return MemoryDeleteResponse(
            deleted_count=successful,
            failed_count=failed,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Error deleting memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
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
            detail="Internal server error"
        )
        
        
@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(memory_id: UUID):
    """Get a specific memory by ID"""
    try:
        memory = await vector_store.get_memory(memory_id)
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )
        
        return MemoryResponse(
            id=memory.id,
            content=memory.content,
            content_type=memory.content_type,
            timestamp=memory.timestamp,
            metadata=memory.metadata,
            tags=memory.tags,
            source_id=memory.source_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting memory {memory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )