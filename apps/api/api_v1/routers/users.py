from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Dict
from apps.utils import get_database

user_router = APIRouter()


@user_router.get("/get_bookings_by_bus", response_model=List[Dict])
async def get_bookings_by_bus(bus_id: str, db: AsyncIOMotorClient = Depends(get_database)):
    bookings = await db["booking"].find({"bus_id": bus_id}).to_list(length=100)
    return bookings

@user_router.get("/get_bookings", response_model=List[Dict])
async def get_bookings(user_id: str, db: AsyncIOMotorClient = Depends(get_database)):
    bookings = await db["booking"].find({"user_id": user_id}).to_list(length=100)
    return bookings

