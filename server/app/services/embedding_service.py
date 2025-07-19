from typing import List, Optional
import logging
import httpx
from app.config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using OpenAI API"""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = "https://api.openai.com/v1"
        self.model = "text-embedding-ada-002"
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text"""
        try:
            if not self.api_key:
                logger.error("OpenAI API key not configured")
                return None
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "input": text,
                        "model": self.model
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    embedding = data["data"][0]["embedding"]
                    logger.info(f"Generated embedding for text (length: {len(text)})")
                    return embedding
                else:
                    logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        
        for text in texts:
            embedding = await self.get_embedding(text)
            embeddings.append(embedding)
        
        return embeddings
    
    def health_check(self) -> bool:
        """Check if the embedding service is healthy"""
        return self.api_key is not None


# Global embedding service instance
embedding_service = EmbeddingService() 
