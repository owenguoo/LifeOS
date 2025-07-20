from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import UUID


class MemoryCreateRequest(BaseModel):
    """Request schema for creating a memory"""
    
    content: str = Field(..., min_length=1, description="Memory content")
    content_type: str = Field(..., description="Type of content: 'video', 'audio', 'text', 'interaction'")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    source_id: Optional[str] = None


class MemorySearchRequest(BaseModel):
    """Request schema for memory search"""
    
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    content_types: Optional[List[str]] = Field(default=None, description="Filter by content types")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")
    score_threshold: Optional[float] = Field(default=0.01, ge=0.0, le=1.0, description="Minimum similarity score")


class MemorySearchResponse(BaseModel):
    """Response schema for memory search"""
    
    results: List[Dict[str, Any]]
    total_found: int
    query: str
    search_time_ms: float


class ChatbotQueryRequest(BaseModel):
    """Request schema for chatbot query"""
    
    user_input: str = Field(..., min_length=1, description="User's question or input")
    confidence_threshold: Optional[float] = Field(default=0.01, ge=0.0, le=1.0, description="Minimum confidence score for video match")


class ChatbotQueryResponse(BaseModel):
    """Response schema for chatbot query"""
    
    original_input: str
    refined_query: str
    video_found: bool
    ai_response: Optional[str] = None
    video_id: Optional[str] = None
    timestamp: Optional[str] = None
    summary: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_time_ms: float


class MemoryResponse(BaseModel):
    """Response schema for a single memory"""
    
    id: UUID
    content: str
    content_type: str
    timestamp: datetime
    metadata: Dict[str, Any]
    tags: List[str]
    source_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class MemoryDeleteRequest(BaseModel):
    """Request schema for deleting memories"""
    
    memory_ids: List[UUID] = Field(..., description="List of memory IDs to delete")


class MemoryDeleteResponse(BaseModel):
    """Response schema for memory deletion"""
    
    deleted_count: int
    failed_count: int
    errors: List[str] = Field(default_factory=list) 