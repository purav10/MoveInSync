from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from motor.motor_asyncio import AsyncIOMotorClient

from apps.core import security
from apps.utils import get_database, verify_password, hash_password

auth_router = APIRouter()

async def authenticate_user(db, username: str, password: str):
    user = await Request.app.db["users"].find_one({"email": username})
    if user and verify_password(password, user["hashed_password"]):
        return user 
    return None

async def sign_up_new_user(db, username: str, password: str):
    existing_user = await db["users"].find_one({"email": username})
    if existing_user:
        return None

    hashed_password = hash_password(password)
    user_dict = {
        "email": username,
        "hashed_password": hashed_password,
        "is_active": True,
        "is_superuser": False
    }
    await db["users"].insert_one(user_dict)
    return user_dict

@auth_router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncIOMotorClient = Depends(get_database)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    permissions = "admin" if user.get("is_superuser") else "user"
    access_token = security.create_access_token(
        data={"sub": user["email"], "permissions": permissions},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/signup")
async def signup(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncIOMotorClient = Depends(get_database)):
    user = await sign_up_new_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account already exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    permissions = "admin" if user.get("is_superuser") else "user"
    access_token = security.create_access_token(
        data={"sub": user["email"], "permissions": permissions},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}