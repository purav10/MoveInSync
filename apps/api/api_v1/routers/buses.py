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
from datetime import datetime


class BusCreate(BaseModel):
    name: str
    distance: float
    cost: float
    time: float
    total_seats: int
    current_occupancy: int
    dates: list
    color: str
    Routes: list

class BusUpdate(BaseModel):
    add_date: datetime
    bus_id: str

class SeatBooking(BaseModel):
    bus_id: str
    seat_number: int

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
token_decoded = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwdXJhdmJpeWFuaSIsInBlcm1pc3Npb25zIjoiYWRtaW4ifQ.VeW6ER8S8Tag00w-AgzM-U9CzgTCyQEL_eLZvZ4AkVk"
async def get_current_user(abcd: token_decoded, db: AsyncIOMotorClient = Depends(get_database)):
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

async def update_color(bus_id: str, db: AsyncIOMotorClient):
    bus = await db["buses"].find_one({"_id": ObjectId(bus_id)})
    print("update color", bus)
    if bus:
        if bus["current_occupancy"] / bus["total_seats"] < 0.6:
            new_color = "green"
        elif bus["current_occupancy"] / bus["total_seats"] < 0.9:
            new_color = "yellow"
        else:
            new_color = "red"
        await db["buses"].update_one({"_id": ObjectId(bus_id)}, {"$set": {"color": new_color}})

@buses_router.post("/create_bus")  
async def create_bus(bus_data: BusCreate, db: AsyncIOMotorClient = Depends(get_database)):
    user = await get_current_user(token_decoded,db)
    if not user or not user.get("is_superuser"):
        raise HTTPException(status_code=status.HTTP_403_FORIDDEN, detail="Not authorized")

    bus = bus_data.dict()
    await db["buses"].insert_one(bus)
    for i in range (1, bus["total_seats"] + 1 - bus["current_occupancy"]):
        await db["seats"].insert_one({"bus_id": bus["_id"], "seat_number": i, "is_booked": False})
    await update_color(bus["_id"], db)
    return {"message": "Bus Created Successfully"}



@buses_router.post("/update_bus")
async def update_bus(update_data: BusUpdate, db: AsyncIOMotorClient = Depends(get_database)):
    user = await get_current_user(token_decoded,db)
    if not user or not user.get("is_superuser"):
        raise HTTPException(status_code=status.HTTP_403_FORIDDEN, detail="Not authorized")
    bus = await db["buses"].find_one({"_id": ObjectId(update_data.bus_id)})
    if not bus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bus not found")
    print(bus)
    if bus["dates"]==None:
        dates=[]
        dates.append(update_data.add_date)
        print(dates)
        await db["buses"].update_one({"_id": ObjectId(update_data.bus_id)}, {"$set": {"dates": dates}})
        return ;
    if update_data.add_date in bus["dates"]:
        return ;
    dates = bus["dates"]
    dates.append(update_data.add_date)
    print(dates)
    await db["buses"].update_one({"_id": ObjectId(update_data.bus_id)}, {"$set": {"dates": dates}})
    return {"message": "Bus Updated Successfully"}


@buses_router.get("/get_buses")
async def get_buses(db: AsyncIOMotorClient = Depends(get_database)):
    try:
        buses = await db["buses"].find().to_list(length=100)
        for bus in buses:
            bus['_id'] = str(bus['_id'])
            bus['dates'] = [date.isoformat() for date in bus['dates']]
        return JSONResponse(content=buses)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="An error occurred while fetching bus data.")