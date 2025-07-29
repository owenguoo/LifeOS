from fastapi import APIRouter, Depends
from app.services.simple_auth import SimpleAuthService
from app.schemas.simple_auth import UserRegister, UserLogin, AuthResponse, User
from app.middleware.simple_auth import get_current_user


router = APIRouter()
auth_service = SimpleAuthService()


@router.post("/register", response_model=AuthResponse)
async def register(user_data: UserRegister):
    """Register a new user with username and password"""
    return await auth_service.register_user(user_data.username, user_data.password)


@router.post("/login", response_model=AuthResponse)
async def login(login_data: UserLogin):
    """Login user with username and password"""
    return await auth_service.login_user(login_data.username, login_data.password)


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user
