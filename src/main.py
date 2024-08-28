from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from src.api import router as api_router

from src.database import engine, Base
from dotenv import load_dotenv
import os

load_dotenv() 

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

# Initialize database tables
Base.metadata.create_all(bind=engine)

# Include the main API router
app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to VetLink MarketPlace API"}
