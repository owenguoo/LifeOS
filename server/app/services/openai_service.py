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
    
    def generate_contextual_response(self, user_question: str, video_contexts: list) -> Optional[str]:
        """
        Generate a response to the user's question based on video context summaries
        
        Args:
            user_question: The original user question
            video_contexts: List of dicts with video context (summary, timestamp, etc.)
            
        Returns:
            Generated response string or None if failed
        """
        if not self.api_key or not self.client:
            logger.error("OpenAI API key not configured")
            return None
        
        if not video_contexts:
            return "I couldn't find any relevant videos to answer your question."
        
        try:
            # Format the context from video summaries
            context_text = ""
            for i, context in enumerate(video_contexts, 1):
                timestamp = context.get('timestamp', 'Unknown time')
                summary = context.get('summary', 'No summary available')
                confidence = context.get('confidence_score', 0)
                context_text += f"\nVideo {i} ({timestamp}, confidence: {confidence:.2f}):\n{summary}\n"
            
            system_prompt = """
            You are an AI assistant helping a user understand their video memories. You will be given:
            1. A user's question about their activities or memories
            2. Context from relevant video summaries that were found based on the question
            
            Your job is to:
            - Answer the user's question using the provided video context
            - Be conversational and helpful
            - Reference specific details from the videos when relevant
            - If the context doesn't fully answer the question, acknowledge what you can and cannot determine
            - Keep responses concise but informative
            - Use a natural, friendly tone as if you're helping them remember their own activities
            
            Always base your response on the provided video context rather than making assumptions.
            """
            
            user_prompt = f"""
            Question: {user_question}
            
            Video Context:
            {context_text}
            
            Please provide a helpful response based on this video context.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            generated_response = response.choices[0].message.content
            if generated_response:
                generated_response = generated_response.strip()
                logger.info(f"Generated contextual response for question: '{user_question}'")
                return generated_response
            else:
                logger.warning("Empty response from OpenAI")
                return "I found some relevant videos but couldn't generate a proper response."
            
        except Exception as e:
            logger.error(f"Error generating contextual response with OpenAI: {e}")
            return "I found some relevant videos but encountered an error while generating a response."


# Global instance
openai_service = OpenAIService() 