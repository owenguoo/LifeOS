"""
Highlights Integration for LifeOS Automations
Handles adding interesting content to highlights table
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import uuid4

from database.supabase_client import SupabaseManager

logger = logging.getLogger(__name__)


class HighlightsIntegration:
    """Handles highlights-related automations"""
    
    def __init__(self):
        self.supabase_manager = SupabaseManager()
        
    async def add_to_highlights(
        self, 
        video_id: str, 
        summary: str, 
        analysis: Dict[str, Any], 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add interesting content to highlights table
        
        Args:
            video_id: UUID of the video
            summary: Video summary text
            analysis: LLM analysis results
            metadata: Video metadata
            
        Returns:
            Dictionary with highlights processing results
        """
        try:
            logger.info(f"Processing highlights for video {video_id}")
            print(f"🎯 Highlights integration received metadata: {metadata}")
            
            # Get user_id from metadata
            user_id = metadata.get("user_id")
            print(f"👤 Extracted user_id: {user_id}")
            if not user_id:
                logger.error("No user_id found in metadata")
                print(f"❌ No user_id found in metadata: {metadata}")
                return {
                    "highlights_automation_triggered": False,
                    "reason": "No user_id provided",
                    "processing_timestamp": datetime.now().isoformat()
                }
            
            # Create highlight record
            highlight_data = {
                "video_id": video_id,
                "user_id": user_id,
                "created_at": datetime.now().isoformat()
            }
            
            # Insert into highlights table
            result = self.supabase_manager.client.table("highlights").insert(highlight_data).execute()
            
            if result.data:
                logger.info(f"Successfully added video {video_id} to highlights for user {user_id}")
                return {
                    "highlights_automation_triggered": True,
                    "processing_timestamp": datetime.now().isoformat(),
                    "highlight_id": result.data[0]["highlight_id"],
                    "message": f"Video {video_id} added to highlights"
                }
            else:
                logger.error(f"Failed to insert highlight into database")
                return {
                    "highlights_automation_triggered": False,
                    "reason": "Database insertion failed",
                    "processing_timestamp": datetime.now().isoformat()
                }
            
        except Exception as e:
            logger.error(f"Error adding to highlights: {e}")
            return {
                "highlights_automation_triggered": False,
                "reason": str(e),
                "processing_timestamp": datetime.now().isoformat()
            }
    
    def _generate_highlight_title(self, summary: str, analysis: Dict[str, Any]) -> str:
        """
        Generate a catchy title for the highlight
        
        Args:
            summary: Video summary
            analysis: LLM analysis
            
        Returns:
            Generated title
        """
        try:
            # Use the first sentence of summary as title, or generate from key moments
            key_moments = analysis.get("key_moments", [])
            categories = analysis.get("categories", [])
            
            if key_moments:
                return f"Highlight: {key_moments[0][:50]}..."
            elif categories:
                return f"{categories[0]} Moment"
            else:
                # Use first 50 characters of summary
                sentences = summary.split('. ')
                if sentences:
                    return sentences[0][:50] + ("..." if len(sentences[0]) > 50 else "")
                else:
                    return "Interesting Moment"
                    
        except Exception as e:
            logger.error(f"Error generating highlight title: {e}")
            return "Highlight"
    
    def _extract_tags(self, summary: str, analysis: Dict[str, Any]) -> List[str]:
        """
        Extract relevant tags from summary and analysis
        
        Args:
            summary: Video summary
            analysis: LLM analysis
            
        Returns:
            List of tags
        """
        try:
            tags = []
            
            # Add categories as tags
            categories = analysis.get("categories", [])
            tags.extend(categories)
            
            # Add predefined tags based on content
            # This is a simple implementation - in production, use NLP for better tag extraction
            
            summary_lower = summary.lower()
            
            # People tags
            if any(word in summary_lower for word in ["meeting", "call", "conversation"]):
                tags.append("meeting")
            
            # Location tags
            if any(word in summary_lower for word in ["office", "home", "restaurant", "travel"]):
                tags.append("location")
            
            # Activity tags
            if any(word in summary_lower for word in ["working", "coding", "presentation"]):
                tags.append("work")
            
            if any(word in summary_lower for word in ["exercise", "gym", "running", "walking"]):
                tags.append("fitness")
            
            if any(word in summary_lower for word in ["cooking", "eating", "food"]):
                tags.append("food")
            
            # Remove duplicates and return
            return list(set(tags))
            
        except Exception as e:
            logger.error(f"Error extracting tags: {e}")
            return []
    
    async def _store_highlight(self, highlight_data: Dict[str, Any]) -> bool:
        """
        Store highlight in the database
        
        Args:
            highlight_data: Highlight data to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.supabase_manager.client.table("highlights").insert(highlight_data).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error storing highlight: {e}")
            return False
    
    async def get_user_highlights(
        self, 
        user_id: str, 
        limit: int = 50, 
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get highlights for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of highlights to return
            category: Optional category filter
            
        Returns:
            List of highlights
        """
        try:
            # This would query the highlights table
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting user highlights: {e}")
            return []
    
    async def update_highlight(self, highlight_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing highlight
        
        Args:
            highlight_id: ID of the highlight to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # This would update the highlight in the database
            logger.info(f"Would update highlight {highlight_id} with: {updates}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating highlight {highlight_id}: {e}")
            return False
    
    async def delete_highlight(self, highlight_id: str) -> bool:
        """
        Delete a highlight
        
        Args:
            highlight_id: ID of the highlight to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # This would delete the highlight from the database
            logger.info(f"Would delete highlight {highlight_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting highlight {highlight_id}: {e}")
            return False
    
    async def get_highlight_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get highlight statistics for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with highlight statistics
        """
        try:
            # This would aggregate data from the highlights table
            return {
                "total_highlights": 0,
                "categories": {},
                "average_interest_score": 0.0,
                "most_recent": None
            }
            
        except Exception as e:
            logger.error(f"Error getting highlight stats: {e}")
            return {}