import json
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from database import SessionLocal
from typing import Annotated


# Import existing auth dependencies
from auth import get_current_user, db_dependency
from models import Users, UserPicture

router = APIRouter(
    prefix="/profile",
    tags=["profile"]
)

# Get Database connection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/info")
def get_profile_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return a JSON response containing user info (ID, username, name, surname).
    """
    db_user = db.query(Users).filter(Users.id == current_user["id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": db_user.id,
        "username": db_user.username,
        "name": db_user.name,
        "surname": db_user.surname,
    }

@router.get("/picture")
def get_profile_picture(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return the raw image data for the user's profile picture.
    Or return 404 if no picture is set.
    """
    db_user = db.query(Users).filter(Users.id == current_user["id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Convert the dynamic relationship to a list so we can safely check
    pictures = list(db_user.profilePicture)
    if not pictures:
        raise HTTPException(status_code=404, detail="No profile picture found.")

    pic = pictures[0]
    # With sqlalchemy-imageattach, open from the store:
    with pic.store.open(pic) as f:
        image_bytes = f.read()

    # Return as a raw file response
    # For images, it's common to return "image/jpeg" or "image/png"
    mimetype = pic.mimetype or "application/octet-stream"

    # We can just return a Response with the raw bytes:
    return Response(content=image_bytes, media_type=mimetype)