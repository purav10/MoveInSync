from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from datetime import datetime, timedelta

app = FastAPI()
client = MongoClient("mongodb://localhost:27017/")
db = client.bus_booking_system
seats_collection = db.seats

@app.put("/book-seat/{seat_id}")
async def book_seat(seat_id: str, user_id: str):
    current_time = datetime.utcnow()

    # Find the seat and check if it is available
    seat = seats_collection.find_one({"_id": seat_id})

    if seat is None:
        raise HTTPException(status_code=404, detail="Seat not found")

    # Check if the seat is already booked or if the booking timestamp has expired
    if seat.get("booked_by") is None or seat.get("booking_timestamp") < current_time:
        # Book the seat
        update_result = seats_collection.update_one(
            {"_id": seat_id},
            {"$set": {"booked_by": user_id, "booking_timestamp": current_time + timedelta(minutes=5)}}
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to book the seat")

        return {"status": "success", "message": f"Seat {seat_id} booked by {user_id}"}
    else:
        # Seat is already booked
        raise HTTPException(status_code=400, detail="Seat is already booked")

@app.get("/check-seat/{seat_id}")
async def check_seat(seat_id: str):
    current_time = datetime.utcnow()
    seat = seats_collection.find_one({"_id": seat_id})

    if seat and (seat.get("booked_by") is None or seat.get("booking_timestamp") < current_time):
        return {"status": "available"}
    return {"status": "booked", "booked_by": seat.get("booked_by")}
