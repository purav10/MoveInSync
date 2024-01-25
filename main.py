from fastapi import FastAPI, Depends
from starlette.requests import Request
import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager

from config import settings
# from app.db.mongodb_utils import get_database, close_database
from apps.api.api_v1.routers import (
    # users_router, 
    buses_router,
    auth_router
)
# from apps.core.auth import get_current_active_user


# MongoDB connection setup
@asynccontextmanager
async def mongodb_connection(app: FastAPI):
    app.mongodb_client = AsyncIOMotorClient(settings.DB_URL)
    app.mongodb = app.mongodb_client[settings.DB_NAME]
    yield
    app.mongodb_client.close()

app = FastAPI(lifespan=mongodb_connection)

# # Middleware to inject database into each request
# @app.middleware("http")
# async def db_session_middleware(request: Request, call_next):
#     request.state.db = get_database(app)
#     response = await call_next(request)
#     close_database(app)
#     return response

# Root endpoint
@app.get("/api/v1")
async def root():
    return {"message": "Hello from Bus Booking System"}

# # Routers
# app.include_router(
#     users_router,
#     prefix="/api/v1/users",
#     tags=["users"]
# )

app.include_router(
    buses_router,
    prefix="/api/v1/buses",
    tags=["buses"],
)

# app.include_router(
#     bookings_router,
#     prefix="/api/v1/bookings",
#     tags=["bookings"],
#     # Add dependencies if needed
# )

# app.include_router(
#     routes_router,
#     prefix="/api/v1/routes",
#     tags=["routes"],
#     # Add dependencies if needed
# )

app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["auth"]
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        reload=True,
        port=settings.PORT,
    )
