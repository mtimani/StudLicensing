import json
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File, status
from sqlalchemy.orm import Session
from database import SessionLocal
from pydantic import BaseModel, Field
from typing import Annotated, Optional
from sqlalchemy_imageattach.entity import store_context
from PIL import Image
from io import BytesIO
import os


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

class UpdateProfileInfo(BaseModel):
    name: Optional[str] = Field(None, max_length=50, min_length=1)
    surname: Optional[str] = Field(None, max_length=50, min_length=1)

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

@router.put("/info", status_code=status.HTTP_200_OK)
def update_profile_info(
    current_user: dict = Depends(get_current_user),
    update_data: UpdateProfileInfo = ...,
    db: Session = Depends(get_db)
):
    """
    Updates the authenticated user's profile info (name, surname, password).
    Fields not provided remain unchanged.
    """
    # 1. Fetch user from DB
    db_user = db.query(Users).filter(Users.id == current_user["id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Update fields if they are provided
    if update_data.name is not None:
        db_user.name = update_data.name

    if update_data.surname is not None:
        db_user.surname = update_data.surname

    # 3. Commit changes
    db.commit()
    db.refresh(db_user)

    return {
        "detail": "Profile updated successfully",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "name": db_user.name,
            "surname": db_user.surname,
        }
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

@router.put("/picture", status_code=status.HTTP_200_OK)
async def update_profile_picture(
    current_user: dict = Depends(get_current_user),
    new_picture: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Updates (or sets) the user's profile picture. If an old picture exists, it is deleted
    (including the file on disk). Then the new one is stored.
    """
    db_user = db.query(Users).filter(Users.id == current_user["id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # -- 1) Validate the new image
    profilePicture = new_picture
    if profilePicture is not None:
        # Check file extension.
        ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
        ext = os.path.splitext(profilePicture.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
        
        # Check content type.
        ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif"}
        provided_mimetype = profilePicture.content_type
        if not provided_mimetype or provided_mimetype not in ALLOWED_MIME_TYPES:
            # If content_type is not provided or not acceptable, assign a default based on extension.
            if ext in {".jpg", ".jpeg"}:
                mimetype = "image/jpeg"
            elif ext == ".png":
                mimetype = "image/png"
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded file is not a valid image."
                )
        else:
            mimetype = provided_mimetype

    file_data = await profilePicture.read()

    # Validate the image using Pillow.
    try:
        bytes_io = BytesIO(file_data)
        image = Image.open(bytes_io)
        image.verify()  # Verify image integrity
        # Re-open to ensure it's usable afterwards:
        bytes_io.seek(0)
        image = Image.open(bytes_io)
        if image.format not in {"JPEG", "PNG"}:
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
        width, height = image.size
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Uploaded file is not a valid image.")

    # -- 2) Remove the old picture (if any) inside a store_context
    from sqlalchemy_imageattach.entity import store_context
    from models import store  # Your FileSystemStore(...) instance

    with store_context(store):
        # Convert to list so we can iterate the existing pictures
        old_pictures = list(db_user.profilePicture)
        for old_pic in old_pictures:
            db.delete(old_pic)
        db.commit()  # This triggers the post-delete hook to remove old files from disk

        # -- 3) Create a new UserPicture record
        new_user_pic = UserPicture()
        new_user_pic.mimetype = mimetype
        new_user_pic.width = width
        new_user_pic.height = height
        new_user_pic.store = store  # The configured FileSystemStore
        new_user_pic.file = BytesIO(file_data)
        db_user.profilePicture = [new_user_pic]

        # Commit to save new picture
        db.commit()
        db.refresh(db_user)

    return {"detail": "Profile picture updated successfully."}