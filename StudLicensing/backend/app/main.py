# ===========================================
# Imports
# ===========================================

# Monkey patch for models to work
import collections
import collections.abc
if not hasattr(collections, "Iterator"):
    collections.Iterator = collections.abc.Iterator

# Imports
from app import models
#import app.auth
import time
import os
from app.logger import logger
from fastapi import FastAPI, status, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from app.auth import get_current_user, create_superadmin
from app.auth import router as auth_router
from app.profile import router as profile_router
from app.company import router as company_router
from datetime import datetime
from app.database import engine, SessionLocal
from typing import Annotated
from dotenv import find_dotenv
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware



# ===========================================
# Logging configuration
# ===========================================
logger.info("Starting FastAPI application...")



# ===========================================
# Standby for PostgreSQL database to be up
# ===========================================

# Function that checks and waits for the DB to be up
def wait_for_db(
    timeout: int = 60, 
    interval: int = 2
):
    """
    Wait for the PostgreSQL database to be ready.
    Attempts to obtain a raw connection every `interval` seconds, for up to `timeout` seconds.
    Raises an exception if the connection cannot be made in time.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            # Try to get a raw connection from the engine
            conn = engine.raw_connection()
            conn.close()
            return
        except Exception as e:
            time.sleep(interval)
    logger.error("Could not connect to the database within the timeout period.")
    raise Exception("Could not connect to the database within the timeout period.")

# Wait for the DB before proceeding with models creation
wait_for_db()



# ========================================================
# Environment variables
# ========================================================

# Load environment variables
dotenv_path = find_dotenv()
if not dotenv_path:
    logger.error("'.env' file not found. Please make sure the file exists in the project directory.")
    raise FileNotFoundError("'.env' file not found. Please make sure the file exists in the project directory.")

# Retrieve environment variables.
PRIVATE_IP = os.getenv('PRIVATE_IP')



# ===========================================
# FastAPI application creation
# ===========================================

# Create FastAPI application
app = FastAPI()

# CORS middleware to allow cross-origin requests from localhost:3000
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Dynamically add the private IP to the allowed origins
if PRIVATE_IP:
    ALLOWED_ORIGINS.append(f"http://{PRIVATE_IP}:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


# Mount the /uploads for static file storage => Profile pictures storage
app.mount("/uploads", StaticFiles(directory="/uploads"), name="uploads")


# ===========================================
# FastAPI error handling setup
# ===========================================

# Function Safe string => for safe string return during error handling
def safe_str(o):
    try:
        return str(o)
    except Exception:
        return repr(o)

# Error Handling function during request validation
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
):
    formatted_errors = []
    for error in exc.errors():
        # Get the message and convert it safely to a string.
        msg = safe_str(error.get("msg"))
        # Example: if the error is about email format, customize the message.
        if "username" in error.get("loc", []) and "email" in msg.lower():
            msg = "The username you entered is not a valid email address."
        formatted_errors.append({
            "loc": error.get("loc"),
            "msg": msg,
            "type": error.get("type")
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": formatted_errors},
    )

# General purpose error Handling function
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unknown error occurred."},
    )



# ===========================================
# FastAPI first level router imports 
# ===========================================

# Include Auth Router
app.include_router(auth_router)

# Include Profile Router
app.include_router(profile_router)

# Include Company Router
app.include_router(company_router)



# ===========================================
# PostgreSQL DataBase connection
# ===========================================
models.Base.metadata.create_all(bind=engine)

# Get Database connection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# ===========================================
# Dependencies setup
# ===========================================
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]



# ===========================================
# Generate the SuperAdmin user
# ===========================================
create_superadmin()



# ===========================================
# API Routes
# ===========================================

# Testing "/" main route that will be removed
@app.get("/", status_code=status.HTTP_200_OK)
async def user(
    user: user_dependency, 
    db: db_dependency
):
    if user is None:
        logger.info("Authentication Failed")
        raise HTTPException(status_code=401, detail='Authentication Failed')
    return {"User": user}