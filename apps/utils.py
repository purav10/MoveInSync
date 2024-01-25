from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

# Database Utility
def get_database(request: Request) -> AsyncIOMotorClient:
    return request.app.mongodb

# Password Hashing Utility
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
