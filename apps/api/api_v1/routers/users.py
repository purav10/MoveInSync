import heapq
from fastapi import APIRouter, Body, Depends, HTTPException, status
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Dict
from apps.utils import get_database
from apps.core import security as settings
from pydantic import BaseModel
from bson import ObjectId
from .buses import update_color
from datetime import datetime

class SeatBooking(BaseModel):
    bus_id: str
    seat_number: int
    boarding_date: datetime
    
class RouteForm(BaseModel):
    source: str
    destination: str


users_router = APIRouter()

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
        

@users_router.get("/book_seat")
async def book_seat(booking : SeatBooking, db: AsyncIOMotorClient = Depends(get_database)):
    bus_id = (booking.bus_id)
    seat_number = (booking.seat_number)
    boarding_date = (booking.boarding_date)
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
        "booking_date": datetime.now(),
        "boarding_date": boarding_date,
        "status": "booked"
    }
    await db["booking"].insert_one(booking)
    await db["seats"].update_one({"bus_id": bus_id, "seat_number": seat_number}, {"$set": {"is_booked": True}}, upsert=True)
    await db["buses"].update_one({"_id": ObjectId(bus_id)}, {"$inc": {"current_occupancy": 1}})
    print(db["buses"].find_one({"_id": ObjectId(bus_id)}))
    await update_color(bus_id, db)
    return {"message": "Seat booked successfully"}

@users_router.get("/cancel_seat")
async def cancel_seat(booking : SeatBooking, db: AsyncIOMotorClient = Depends(get_database)):
    bus_id = (booking.bus_id)
    seat_number = (booking.seat_number)
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
    await update_color(bus_id, db)
    return {"message": "Seat cancelled successfully"}

@users_router.get("/bookings")
async def get_bookings(db: AsyncIOMotorClient = Depends(get_database)):
    user = await get_current_user(token_decoded,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORIDDEN, detail="Not authorized")
    bookings = await db["booking"].find({"user_id": user["email"]}).to_list(length=100)
    for booking in bookings:
        booking["_id"] = str(booking["_id"])
    print(bookings)
    return bookings


@users_router.post("/route")
async def route(form_data: RouteForm = Body(...), db: AsyncIOMotorClient = Depends(get_database)):
    start = form_data.source
    end = form_data.destination
    times = {start: (0, [])}
    queue = [(0, start, [])]

    neighbors = await db["buses"].find({"Routes.0": start}).to_list(length=100)
    while queue:
        (time, current_node, path) = heapq.heappop(queue)

        # Don't process if we've already found a shorter path
        if times[current_node][0] < time:
            continue

        path = path + [current_node]

        # If we've reached the end, return the path
        if current_node == end:
            eta = 0
            distance = 0
            buses =[]
            for i in range(len(path)-1):
                bus = await db["buses"].find_one({"Routes.0": path[i], "Routes.1": path[i+1]})
                if bus:
                    buses.append(bus["name"])
                distance += bus["distance"]
                eta += bus["time"]
            return {"bus_name": buses, "time": eta, "distance": distance, "stops": path, "start_location": start, "end_location": end}
        # Get neighbors from the database
        neighbors = await db["buses"].find({"Routes.0": current_node}).to_list(length=100000000)
        for neighbor in neighbors:
            old_time = times.get(neighbor["Routes"][1], (float('inf'), []))[0]
            new_time = time + neighbor["time"]
            print(old_time, new_time)
            if new_time < old_time:
                times[neighbor["Routes"][1]] = (new_time, path)
                heapq.heappush(queue, (new_time, neighbor["Routes"][1], path))

    raise HTTPException(status_code=404, detail="Path not found")


@users_router.get("/get_seats", response_model=List[Dict])
async def get_seats(bus_id: str, db: AsyncIOMotorClient = Depends(get_database)):
    seats = await db["seats"].find({"bus_id": bus_id}).to_list(length=100)
    return seats

@users_router.get("/get_buses", response_model=List[Dict])
async def get_buses(db: AsyncIOMotorClient = Depends(get_database)):
    buses = await db["buses"].find().to_list(length=100)
    return buses
