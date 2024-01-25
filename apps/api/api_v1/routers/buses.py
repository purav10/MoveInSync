import datetime
from bson import ObjectId
from fastapi import Depends, HTTPException, Response, status, APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
import starlette
from apps.core import security as settings
from apps.core.security import decode_token
from apps.utils import get_database
from apps.db.models import Bus
from typing import List, Dict, Annotated, Optional
from fastapi.responses import JSONResponse


class BusCreate(BaseModel):
    name: str
    total_seats: int
    current_occupancy: int
    Routes: list

class SeatBooking(BaseModel):
    bus_id: str
    seat_number: int

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
token_decoded = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwdXJhdmJpeWFuaSIsInBlcm1pc3Npb25zIjoiYWRtaW4ifQ.VeW6ER8S8Tag00w-AgzM-U9CzgTCyQEL_eLZvZ4AkVk"
async def get_current_user(abcd: token_decoded, db: AsyncIOMotorClient = Depends(get_database)):
    print(abcd)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(abcd, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        user = await db["users"].find_one({"email": email})
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

buses_router = APIRouter()  

@buses_router.post("/create_bus")  
async def create_bus(bus_data: BusCreate, db: AsyncIOMotorClient = Depends(get_database)):
    user = await get_current_user(token_decoded,db)
    if not user or not user.get("is_superuser"):
        raise HTTPException(status_code=status.HTTP_403_FORIDDEN, detail="Not authorized")

    bus = bus_data.dict()
    await db["buses"].insert_one(bus)
    return {"message": "Bus Created Successfully"}

@buses_router.get("/get_buses")
async def get_buses(db: AsyncIOMotorClient = Depends(get_database)):
    try:
        buses = await db["buses"].find().to_list(length=100)
        for bus in buses:
            bus['_id'] = str(bus['_id'])
        return JSONResponse(content=buses)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="An error occurred while fetching bus data.")

@buses_router.get("/book_seat")
async def book_seat(booking : SeatBooking, db: AsyncIOMotorClient = Depends(get_database)):
    bus_id = (booking.bus_id)
    seat_number = (booking.seat_number)
    user = await get_current_user(token_decoded,db)
    print(user)
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORIDDEN, detail="Not authorized")

    bus = await db["buses"].find_one({"_id": ObjectId(bus_id)})
    print(bus)
    if not bus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bus not found")

    if booking.seat_number > bus["total_seats"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seat number is invalid")

    if booking.seat_number < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seat number is invalid")

    if bus["current_occupancy"] == bus["total_seats"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bus is full")

    seat = await db["seats"].find_one({"bus_id": bus_id, "seat_number": seat_number})
    if seat and seat["is_booked"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seat is already booked")

    booking = {
        "bus_id": bus_id,
        "user_id": user["email"],
        "seat_number": seat_number,
        "status": "booked"
    }
    await db["booking"].insert_one(booking)
    await db["seats"].update_one({"bus_id": bus_id, "seat_number": seat_number}, {"$set": {"is_booked": True}}, upsert=True)
    await db["buses"].update_one({"_id": ObjectId(bus_id)}, {"$inc": {"current_occupancy": 1}})
    print(db["buses"].find_one({"_id": ObjectId(bus_id)}))
    return {"message": "Seat booked successfully"}

@buses_router.get("/cancel_seat")
async def cancel_seat(booking : SeatBooking, db: AsyncIOMotorClient = Depends(get_database)):
    bus_id = (booking.bus_id)
    seat_number = (booking.seat_number)
    print(bus_id)
    print(seat_number)
    user = await get_current_user(token_decoded,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORIDDEN, detail="Not authorized")
    print(user)
    bus = await db["buses"].find_one({"_id": ObjectId(bus_id)})
    print(bus)
    if not bus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bus not found")

    if booking.seat_number > bus["total_seats"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seat number is invalid")

    if booking.seat_number < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seat number is invalid")

    if bus["current_occupancy"] == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bus is empty")

    seat = await db["seats"].find_one({"bus_id": bus_id, "seat_number": seat_number})
    if not seat or not seat["is_booked"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seat is not booked")

    booking = {
        "bus_id": bus_id,
        "user_id": user["email"],
        "seat_number": seat_number,
        "status": "cancelled"
    }
    await db["booking"].insert_one(booking)
    await db["seats"].update_one({"bus_id": bus_id, "seat_number": seat_number}, {"$set": {"is_booked": False}}, upsert=True)
    await db["buses"].update_one({"_id": ObjectId(bus_id)}, {"$inc": {"current_occupancy": -1}})
    return {"message": "Seat cancelled successfully"}