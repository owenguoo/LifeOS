from typing import List, Dict, Any, Optional, Tuple, cast
from uuid import UUID
from datetime import datetime
import logging
import time

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    Range,
    MatchValue,
    Condition,
)

from app.config.connections import qdrant_connection
from app.models.memory import MemoryPoint, MemorySearchResult

logger = logging.getLogger(__name__)

# Collection configuration
COLLECTION_NAME = "lifeos_memories"
VECTOR_SIZE = 1024  # TwelveLabs Marengo-retrieval-2.7 embedding size
DISTANCE_METRIC = Distance.COSINE


class VectorStoreService:
    """Service for managing vector operations with Qdrant"""

    def __init__(self):
        self.client: QdrantClient = qdrant_connection.get_client()
        self.collection_name = COLLECTION_NAME
        self.vector_size = VECTOR_SIZE
        self.distance_metric = DISTANCE_METRIC

    async def initialize_collection(self) -> bool:
        """Initialize the memories collection if it doesn't exist"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")

                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size, distance=self.distance_metric
                    ),
                )

                # Create payload indexes for efficient filtering
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="user_id",
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )

                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="timestamp",
                    field_schema=models.PayloadSchemaType.DATETIME,
                )

                logger.info(f"Collection {self.collection_name} created successfully")
                return True
            else:
                logger.info(f"Collection {self.collection_name} already exists")
                return True

        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            return False

    async def add_memory(self, memory: MemoryPoint) -> bool:
        """Add a single memory to the vector store"""
        try:
            if not memory.embedding:
                logger.error("Memory must have an embedding to be stored")
                return False

            point = PointStruct(
                id=str(memory.id),
                vector=memory.embedding,
                payload={
                    "user_id": str(memory.user_id),
                    "video_id": str(
                        memory.id
                    ),  # This will be the UUID to connect to postgres
                    "timestamp": memory.timestamp.isoformat(),
                },
            )

            self.client.upsert(collection_name=self.collection_name, points=[point])

            logger.info(f"Memory {memory.id} added successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to add memory {memory.id}: {e}")
            return False

    async def search_memories(
        self,
        user_id: UUID,
        query_vector: List[float],
        limit: int = 10,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        score_threshold: float = 0.01,
    ) -> List[MemorySearchResult]:
        """Search memories using vector similarity"""
        try:
            start_time = time.time()

            # Build filter conditions
            filter_conditions = [
                FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))
            ]

            if date_from or date_to:
                range_filter = {}
                if date_from:
                    range_filter["gte"] = date_from.isoformat()
                if date_to:
                    range_filter["lte"] = date_to.isoformat()

                filter_conditions.append(
                    FieldCondition(key="timestamp", range=Range(**range_filter))
                )

            search_filter = (
                Filter(must=cast(List[Condition], filter_conditions))
                if filter_conditions
                else None
            )

            # Perform vector search
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
            )

            # Convert to MemorySearchResult objects
            results = []
            for point in search_result:
                try:
                    payload = point.payload
                    memory_result = MemorySearchResult(
                        id=UUID(str(point.id)),
                        video_id=str(payload.get("video_id", "")),
                        timestamp=datetime.fromisoformat(payload.get("timestamp", "")),
                        score=point.score,
                    )
                    results.append(memory_result)
                except Exception as e:
                    logger.error(f"Error parsing search result: {e}")
                    continue

            search_time = (time.time() - start_time) * 1000
            logger.info(
                f"Search completed in {search_time:.2f}ms, found {len(results)} results"
            )

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def get_memory(self, memory_id: UUID) -> Optional[MemoryPoint]:
        """Retrieve a specific memory by ID"""
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[str(memory_id)],
                with_payload=True,
                with_vectors=True,
            )

            if not result:
                return None

            point = result[0]
            payload = point.payload

            memory = MemoryPoint(
                id=UUID(str(point.id)),
                user_id=UUID(
                    payload.get("user_id"),
                ),
                content="",  # Not stored in vector payload
                content_type="video",  # Default since we only store videos
                timestamp=datetime.fromisoformat(payload.get("timestamp", "")),
                metadata={},  # Not stored in vector payload
                tags=[],  # Not stored in vector payload
                source_id=None,  # Not stored in vector payload
                embedding=point.vector,
            )

            return memory

        except Exception as e:
            logger.error(f"Failed to get memory {memory_id}: {e}")
            return None

    async def delete_memories(
        self, memory_ids: List[UUID]
    ) -> Tuple[int, int, List[str]]:
        """Delete memories by their IDs"""
        successful = 0
        failed = 0
        errors = []

        try:
            # Convert UUIDs to strings
            id_strings = [str(memory_id) for memory_id in memory_ids]

            # Delete points
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=id_strings),
            )

            successful = len(memory_ids)
            logger.info(f"Successfully deleted {successful} memories")

        except Exception as e:
            failed = len(memory_ids)
            errors.append(f"Failed to delete memories: {str(e)}")
            logger.error(f"Failed to delete memories: {e}")

        return successful, failed, errors

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "vector_size": info.config.params.vectors.size,
                "distance_metric": info.config.params.vectors.distance,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "status": info.status,
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}

    async def health_check(self) -> bool:
        """Check if the vector store is healthy"""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Vector store health check failed: {e}")
            return False


# Global vector store service instance
vector_store = VectorStoreService()
