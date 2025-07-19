from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)


class QdrantConnection:
    """Qdrant vector database connection manager"""
    
    def __init__(self):
        self.client = None
        self._connect()
    
    def _connect(self):
        """Initialize Qdrant client connection"""
        try:
            if settings.qdrant_api_key:
                self.client = QdrantClient(
                    url=settings.qdrant_url,
                    api_key=settings.qdrant_api_key
                )
            else:
                self.client = QdrantClient(url=settings.qdrant_url)
            
            logger.info(f"Connected to Qdrant at {settings.qdrant_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def get_client(self) -> QdrantClient:
        """Get the Qdrant client instance"""
        if not self.client:
            self._connect()
        return self.client
    
    def health_check(self) -> bool:
        """Check if Qdrant is healthy"""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


# Global Qdrant connection instance
qdrant_connection = QdrantConnection() 