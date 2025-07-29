import boto3
import os
import logging

logger = logging.getLogger(__name__)


class S3Service:
    """Service for handling S3 operations"""

    def __init__(self):
        self.s3_client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize S3 client with environment credentials"""
        try:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION", "us-east-2"),
            )
            logger.info("S3 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None

    def generate_presigned_url(self, s3_url: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for S3 object access

        Args:
            s3_url: The S3 URL (e.g., https://bucket.s3.region.amazonaws.com/key)
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL or original URL if generation fails
        """
        try:
            if not self.s3_client:
                logger.warning("S3 client not available, returning original URL")
                return s3_url

            # Parse S3 URL to extract bucket and key
            # URL format: https://bucket.s3.region.amazonaws.com/key
            if not s3_url.startswith("https://"):
                logger.warning(f"Invalid S3 URL format: {s3_url}")
                return s3_url

            # Remove https:// and split by first /
            url_parts = s3_url.replace("https://", "").split("/", 1)
            if len(url_parts) != 2:
                logger.warning(f"Could not parse S3 URL: {s3_url}")
                return s3_url

            # Extract bucket name from the hostname
            # Handle both formats: bucket.s3.region.amazonaws.com and bucket.s3.amazonaws.com
            hostname_parts = url_parts[0].split(".")
            if len(hostname_parts) >= 3 and hostname_parts[1] == "s3":
                bucket_name = hostname_parts[0]
            else:
                logger.warning(f"Could not extract bucket name from: {s3_url}")
                return s3_url

            object_key = url_parts[1]

            logger.info(
                f"Generating presigned URL for bucket: {bucket_name}, key: {object_key}"
            )

            # Generate presigned URL
            presigned_url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": object_key},
                ExpiresIn=expiration,
            )

            logger.info(f"Successfully generated presigned URL for {object_key}")
            return presigned_url

        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {s3_url}: {e}")
            return s3_url

    def health_check(self) -> bool:
        """Check if S3 service is healthy"""
        return self.s3_client is not None


# Global instance for use across the application
s3_service = S3Service()
