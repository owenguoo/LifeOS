from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class MemoryPoint(BaseModel):
    """Represents a single memory point in the vector database"""
    
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    content: str
    content_type: str = Field(..., description="Type of content: 'video', 'audio', 'text', 'interaction'")
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    source_id: Optional[str] = None
    embedding: Optional[List[float]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class MemorySearchResult(BaseModel):
    """Result from memory search"""
    
    id: UUID
    video_id: str  # UUID to connect to postgres table
    timestamp: datetime
    score: float
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

