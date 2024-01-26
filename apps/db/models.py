from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, v):
        return {"type": "string"}


class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    bookings: List[PyObjectId] = []

class Bus(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    distance: float
    cost: float
    time: float
    color: str
    total_seats: int
    current_occupancy: int
    routes: List[str] = []

class Booking(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    bus_id: PyObjectId
    seat_number: int
    booking_date: datetime
    status: str

class Seat(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    seat_number: int
    is_booked: bool
    bus_id: PyObjectId
