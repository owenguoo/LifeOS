import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from supabase import create_client, Client
from fastapi import HTTPException, status

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()


class SimpleAuthService:
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        self.jwt_secret = os.getenv('JWT_SECRET', 'your-secret-key')
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        self.client: Client = create_client(self.url, self.key)

    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def create_jwt_token(self, user_id: str, username: str) -> str:
        """Create JWT token"""
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')

    def verify_jwt_token(self, token: str) -> Optional[dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    async def register_user(self, username: str, password: str) -> dict:
        """Register a new user"""
        try:
            # Check if username already exists
            existing = self.client.table("users").select("username").eq("username", username).execute()
            if existing.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )

            # Hash password and create user
            password_hash = self.hash_password(password)
            
            result = self.client.table("users").insert({
                "username": username,
                "password_hash": password_hash
            }).execute()

            if result.data:
                user = result.data[0]
                token = self.create_jwt_token(user['id'], user['username'])
                
                return {
                    "token": token,
                    "user": {
                        "id": user['id'],
                        "username": user['username']
                    }
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user"
                )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration error: {str(e)}"
            )

    async def login_user(self, username: str, password: str) -> dict:
        """Login user with username and password"""
        try:
            # Get user by username
            result = self.client.table("users").select("*").eq("username", username).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            user = result.data[0]
            
            # Verify password
            if not self.verify_password(password, user['password_hash']):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            # Create JWT token
            token = self.create_jwt_token(user['id'], user['username'])
            
            return {
                "token": token,
                "user": {
                    "id": user['id'],
                    "username": user['username']
                }
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login error: {str(e)}"
            )

    async def get_user_from_token(self, token: str) -> Optional[dict]:
        """Get user info from JWT token"""
        payload = self.verify_jwt_token(token)
        if not payload:
            return None

        try:
            result = self.client.table("users").select("id, username").eq("id", payload['user_id']).execute()
            if result.data:
                return result.data[0]
            return None
        except:
            return None