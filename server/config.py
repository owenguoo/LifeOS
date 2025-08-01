"""
Configuration settings for video ingestion system
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    # TwelveLabs API settings
    TWELVELABS_API_KEY = os.getenv("TWELVELABS_API_KEY")
    # Video settings
    FPS = 10  # 10 FPS for faster processing while maintaining summary quality
    RESOLUTION = (1280, 720)  # 720p (width, height)
    SEGMENT_DURATION = 10  # seconds

    # Performance optimizations
    TWELVELABS_POLLING_INTERVAL = 1.0  # Reduced from 2s to 1s for faster uploads
    WORKER_TIMEOUT = 2  # Reduced queue timeout for better responsiveness

    # Camera settings (Mac FaceTime HD)
    CAMERA_INDEX = os.getenv("CAMERA_INDEX")

    # Queue settings
    MAX_FRAME_QUEUE_SIZE = 100

    # Error handling
    FRAME_CAPTURE_RETRY_DELAY = 0.1  # seconds
    SEGMENT_PROCESSING_RETRY_DELAY = 1.0  # seconds

    # Redis settings
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_QUEUE_NAME = "video_processing_queue"

    # Worker settings
    NUM_WORKERS = 3
    WORKER_BATCH_SIZE = 5

    # S3 settings
    S3_BUCKET_NAME = "lifeos-video-segments"
    S3_REGION = "us-east-1"


# Easy adjustment functions
def set_resolution(width, height):
    """Set video resolution"""
    Config.RESOLUTION = (width, height)


def set_fps(fps):
    """Set frames per second"""
    Config.FPS = fps


def set_segment_duration(seconds):
    """Set segment duration in seconds"""
    Config.SEGMENT_DURATION = seconds
