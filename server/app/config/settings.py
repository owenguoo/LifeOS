from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # App Settings
    app_name: str = "LifeOS Server"
    debug: bool = True
    environment: str = "development"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # S3 Storage
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    s3_bucket: str = "lifeos-media"
    
    # APIs
    twelvelabs_api_key: Optional[str] = os.getenv("TWELVELABS_API_KEY") 
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Vector Database (Qdrant)
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    
    # Supabase
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    
    # Auth
    jwt_secret: Optional[str] = None
    
    # Camera/Video Processing
    camera_index: Optional[str] = os.getenv("CAMERA_INDEX", "0")
    
    # Google Calendar Integration
    google_calendar_credentials_path: Optional[str] = None
    google_calendar_id: Optional[str] = None
    
    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_key: Optional[str] = os.getenv("SUPABASE_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 