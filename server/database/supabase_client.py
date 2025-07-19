"""
Supabase client for video analysis data storage
"""
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from supabase import create_client, Client
from config import Config


class SupabaseManager:
    """Manages Supabase database operations for video analysis data"""
    
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.client: Client = create_client(self.url, self.key)
        self.table_name = "videos"
    
    def generate_linking_uuid(self) -> str:
        """Generate UUID for linking JSON and vector db records"""
        return str(uuid.uuid4())
    
    async def insert_video_analysis(self, analysis_data: Dict[str, Any], user_id: Optional[str] = None) -> Optional[str]:
        """
        Insert video analysis data into Supabase videos table
        
        Args:
            analysis_data: Dictionary containing video analysis results
            user_id: UUID of the user who owns this video
            
        Returns:
            UUID of the inserted record or None if failed
        """
        try:
            # Map to your videos table schema
            video_record = {
                'video_id': analysis_data.get('linking_uuid'),
                'timestamp': analysis_data.get('datetime'),  # Using datetime for timestamp
                'datetime': analysis_data.get('datetime'),
                'detailed_summary': analysis_data.get('detailed_summary'),
                's3_link': analysis_data.get('s3_url'),
                'file_size': analysis_data.get('file_size'),
                'processed_at': analysis_data.get('processed_at'),
                'user_id': user_id
            }
            
            # Insert into Supabase
            result = self.client.table(self.table_name).insert(video_record).execute()
            
            if result.data:
                return analysis_data.get('linking_uuid')
            else:
                print(f"Failed to insert video analysis: {result}")
                return None
                
        except Exception as e:
            print(f"Error inserting video analysis: {e}")
            return None
    
    async def get_video_analysis(self, video_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve video analysis data by video_id
        
        Args:
            video_id: UUID to search for
            user_id: Optional user ID to filter by (for security)
            
        Returns:
            Analysis data dictionary or None if not found
        """
        try:
            query = self.client.table(self.table_name).select("*").eq("video_id", video_id)
            
            # Add user filter if provided
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            print(f"Error retrieving video analysis: {e}")
            return None
    
    async def get_user_videos(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all videos for a specific user
        
        Args:
            user_id: User UUID to filter by
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of video analysis dictionaries
        """
        try:
            result = (self.client.table(self.table_name)
                     .select("*")
                     .eq("user_id", user_id)
                     .order("created_at", desc=True)
                     .range(offset, offset + limit - 1)
                     .execute())
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error retrieving user videos: {e}")
            return []
    
    async def update_vector_status(self, linking_uuid: str, vector_status: str, vector_id: Optional[str] = None) -> bool:
        """
        Update the vector embedding status for a record
        
        Args:
            linking_uuid: UUID of the record to update
            vector_status: Status of vector processing ('pending', 'processing', 'completed', 'failed')
            vector_id: Optional vector database ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                'vector_status': vector_status,
                'vector_updated_at': datetime.now().isoformat()
            }
            
            if vector_id:
                update_data['vector_id'] = vector_id
            
            result = self.client.table(self.table_name).update(update_data).eq("linking_uuid", linking_uuid).execute()
            
            return bool(result.data)
            
        except Exception as e:
            print(f"Error updating vector status: {e}")
            return False
    
    def check_table_exists(self) -> bool:
        """
        Check if the videos table exists and is accessible
        
        Returns:
            True if table exists and is accessible, False otherwise
        """
        try:
            result = self.client.table(self.table_name).select("video_id").limit(1).execute()
            return True
        except Exception as e:
            print(f"Error accessing videos table: {e}")
            return False