from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: str
    username: str


class AuthResponse(BaseModel):
    token: str
    user: User
