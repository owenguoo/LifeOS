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
    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_key: Optional[str] = os.getenv("SUPABASE_KEY")
    supabase_anon_key: Optional[str] = os.getenv("SUPABASE_ANON_KEY")

    # Auth
    jwt_secret: Optional[str] = os.getenv("JWT_SECRET", "your-jwt-secret-key")

    # Camera/Video Processing
    camera_index: Optional[str] = os.getenv("CAMERA_INDEX", "0")
    fps: int = int(os.getenv("VIDEO_FPS", "10"))
    resolution: tuple = (
        int(os.getenv("VIDEO_WIDTH", "1280")),
        int(os.getenv("VIDEO_HEIGHT", "720")),
    )
    segment_duration: int = int(os.getenv("SEGMENT_DURATION", "10"))

    # Worker Settings
    num_workers: int = int(os.getenv("NUM_WORKERS", "3"))
    worker_batch_size: int = int(os.getenv("WORKER_BATCH_SIZE", "5"))

    # Google Calendar Integration
    google_calendar_credentials_path: Optional[str] = os.getenv(
        "GOOGLE_CALENDAR_CREDENTIALS_PATH"
    )
    google_calendar_id: Optional[str] = os.getenv("GOOGLE_CALENDAR_ID")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
