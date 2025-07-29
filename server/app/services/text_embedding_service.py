from typing import List, Optional
import logging
from twelvelabs import TwelveLabs
from app.config.settings import settings

logger = logging.getLogger(__name__)


class TextEmbeddingService:
    """Service for generating text embeddings using TwelveLabs API"""

    def __init__(self):
        if not settings.twelvelabs_api_key:
            raise ValueError("TwelveLabs API key is required for text embeddings")
        self.client = TwelveLabs(api_key=settings.twelvelabs_api_key)

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Generate text embedding using TwelveLabs"""
        try:
            # Create text embedding using TwelveLabs
            text_segment = self.client.embed.create(
                model_name="Marengo-retrieval-2.7", text=text
            )

            if (
                text_segment
                and text_segment.text_embedding
                and text_segment.text_embedding.segments
            ):
                embedding = text_segment.text_embedding.segments[0].embeddings_float
                logger.info(f"Generated text embedding for: {text[:50]}...")
                return embedding
            else:
                logger.error("No embedding data returned from TwelveLabs")
                return None

        except Exception as e:
            logger.error(f"Failed to generate text embedding: {e}")
            return None

    def health_check(self) -> bool:
        """Check if the text embedding service is healthy"""
        return settings.twelvelabs_api_key is not None


# Global text embedding service instance
text_embedding_service = TextEmbeddingService()
