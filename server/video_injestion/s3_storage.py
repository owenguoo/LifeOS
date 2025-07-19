"""
S3 storage handler for video segments
"""
import boto3
import os
from pathlib import Path
from typing import Optional, Dict
from botocore.exceptions import ClientError, NoCredentialsError
from server.config import Config


class S3StorageManager:
    """Handles uploading video segments to S3"""
    
    def __init__(self, bucket_name: str = None, region: str = "us-east-1"):
        self.bucket_name = bucket_name or Config.S3_BUCKET_NAME
        self.region = region
        self.s3_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize S3 client with credentials"""
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=self.region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            print(f"S3 client initialized for bucket: {self.bucket_name}")
        except NoCredentialsError:
            print("❌ AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
            self.s3_client = None
        except Exception as e:
            print(f"❌ Error initializing S3 client: {e}")
            self.s3_client = None
    
    def upload_video_segment(self, local_file_path: str, s3_key: str = None) -> Optional[str]:
        """
        Upload video segment to S3
        
        Args:
            local_file_path: Path to local video file
            s3_key: S3 object key (if None, uses filename)
        
        Returns:
            S3 URL if successful, None if failed
        """
        if not self.s3_client:
            print("❌ S3 client not initialized")
            return None
        
        if not os.path.exists(local_file_path):
            print(f"❌ File not found: {local_file_path}")
            return None
        
        try:
            # Generate S3 key if not provided
            if not s3_key:
                filename = Path(local_file_path).name
                s3_key = f"video_segments/{filename}"
            
            # Upload file
            print(f"📤 Uploading {local_file_path} to s3://{self.bucket_name}/{s3_key}")
            
            self.s3_client.upload_file(
                local_file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': 'video/mp4',
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            # Generate public URL
            s3_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            print(f"✅ Upload successful: {s3_url}")
            
            return s3_url
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                print(f"❌ Bucket '{self.bucket_name}' does not exist")
            else:
                print(f"❌ S3 upload failed: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error during S3 upload: {e}")
            return None
    
    def create_bucket_if_not_exists(self) -> bool:
        """Create S3 bucket if it doesn't exist"""
        if not self.s3_client:
            return False
        
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✅ Bucket '{self.bucket_name}' already exists")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    if self.region == 'us-east-1':
                        # us-east-1 doesn't need LocationConstraint
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    
                    # Set bucket policy for public read access to video files
                    self._set_bucket_policy()
                    
                    print(f"✅ Created bucket: {self.bucket_name}")
                    return True
                    
                except ClientError as create_error:
                    print(f"❌ Failed to create bucket: {create_error}")
                    return False
            else:
                print(f"❌ Error checking bucket: {e}")
                return False
    
    def _set_bucket_policy(self):
        """Set bucket policy for public read access to video files"""
        try:
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{self.bucket_name}/video_segments/*"
                    }
                ]
            }
            
            import json
            self.s3_client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            print("✅ Bucket policy set for public read access")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not set bucket policy: {e}")
    
    def get_bucket_info(self) -> Dict:
        """Get bucket information"""
        if not self.s3_client:
            return {"error": "S3 client not initialized"}
        
        try:
            response = self.s3_client.head_bucket(Bucket=self.bucket_name)
            return {
                "bucket_name": self.bucket_name,
                "region": self.region,
                "exists": True,
                "bucket_url": f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/"
            }
        except ClientError:
            return {
                "bucket_name": self.bucket_name,
                "region": self.region,
                "exists": False
            }