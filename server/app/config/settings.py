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
    openai_api_key: Optional[str] = None
    
    # Vector Database (Qdrant)
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    
    # Auth
    betterauth_secret: Optional[str] = None
    
    camera_index: Optional[str] = os.getenv("CAMERA_INDEX", "0")
    
    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_key: Optional[str] = os.getenv("SUPABASE_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 