# ===========================================
# Imports
# ===========================================

# Monkey patch for models to work
import collections
import collections.abc
if not hasattr(collections, "Iterator"):
    collections.Iterator = collections.abc.Iterator

# Imports
import models
import auth
import time
from fastapi import FastAPI, status, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from auth import router, get_current_user
from profile import router as profile_router
from datetime import datetime
from database import engine, SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session



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
    raise Exception("Could not connect to the database within the timeout period.")

# Wait for the DB before proceeding with models creation
wait_for_db()



# ===========================================
# FastAPI application creation
# ===========================================

# Create FastAPI application
app = FastAPI()

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
app.include_router(auth.router)

# Include Profile Router
app.include_router(profile_router)



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
# API Routes
# ===========================================

# Testing "/" main route that will be removed
@app.get("/", status_code=status.HTTP_200_OK)
async def user(
    user: user_dependency, 
    db: db_dependency
):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    return {"User": user}