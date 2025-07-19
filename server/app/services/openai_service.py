import logging
from openai import OpenAI
from typing import Optional
from app.config.settings import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI API interactions"""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            logger.warning("OpenAI API key not configured")
            self.client = None
    
    def health_check(self) -> bool:
        """Check if OpenAI service is healthy"""
        return self.api_key is not None
    
    def refine_query(self, user_input: str) -> Optional[str]:
        """
        Refine user input into a better search query using OpenAI
        
        Args:
            user_input: The original user input/question
            
        Returns:
            Refined query string or None if failed
        """
        if not self.api_key or not self.client:
            logger.error("OpenAI API key not configured")
            return None
        
        try:
            system_prompt = """
            You are a query refinement assistant for a video memory system. 
            Your job is to take a user's question or input and convert it into 
            a clear, searchable query that would help find relevant video content.
            
            Rules:
            1. Keep the refined query concise but descriptive
            2. Focus on key concepts, actions, or objects mentioned
            3. Use natural language that would match video content descriptions
            4. If the input is already a good search query, return it as-is
            5. Remove unnecessary words but keep the core meaning
            
            Examples:
            - "What was I doing yesterday?" → "yesterday activities"
            - "Show me when I was cooking" → "cooking"
            - "Find videos of me working on my computer" → "working on computer"
            - "When did I last exercise?" → "exercise workout"
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Refine this input into a search query: {user_input}"}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            refined_query = response.choices[0].message.content
            if refined_query:
                refined_query = refined_query.strip()
                logger.info(f"Refined query: '{user_input}' → '{refined_query}'")
                return refined_query
            else:
                logger.warning("Empty response from OpenAI")
                return user_input
            
        except Exception as e:
            logger.error(f"Error refining query with OpenAI: {e}")
            # Fallback: return the original input
            return user_input


# Global instance
openai_service = OpenAIService() 