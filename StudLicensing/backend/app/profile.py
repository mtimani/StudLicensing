# ===========================================
# Imports
# ===========================================
import os
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from pydantic import BaseModel, Field
from typing import Annotated, Optional
from sqlalchemy_imageattach.entity import store_context
from PIL import Image
from io import BytesIO
from app.logger import logger
from app.auth import get_current_user, db_dependency
from app.models import Users, UserPicture



# ===========================================
# Profile router declaration
# ===========================================
router = APIRouter(
    prefix="/profile",
    tags=["profile"]
)



# ===========================================
# Database connection
# ===========================================
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



# ===========================================
# classes definition for various routes
# ===========================================

# UserProfileInfo class for updating the profile information of a user 
class UpdateProfileInfo(BaseModel):
    name: Optional[str] = Field(None, max_length=50, min_length=1)
    surname: Optional[str] = Field(None, max_length=50, min_length=1)



# ===========================================
# API Routes
# ===========================================

# Get profile information route => GET /profile/info
@router.get("/info")
def get_profile_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Query the database to find the current user entry and related information
    Based on get_current_user function that extract information from JWT 
    More specifically the user id is present in the JTW that allows to query the DB for a specific user
    """

    # 1. Fetch user from DB
    db_user = db.query(Users).filter(Users.id == current_user["id"]).first()

    # 2. Raise error if user not found
    if not db_user:
        logger.error(f'The user {current_user["username"]} has not been found.')
        raise HTTPException(
            status_code=403, 
            detail="User not found"
        )

    # 3. Return the user profile information found in the database
    logger.info(f'Successfully retrieved profile information for user {current_user["username"]}')
    return {
        "username": db_user.username,
        "name": db_user.name,
        "surname": db_user.surname,
    }

# Update profile information route => PUT /profile/info
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

    # 2. Raise error if user not found
    if not db_user:
        logger.error(f'The user {current_user["username"]} has not been found.')
        raise HTTPException(
            status_code=403, 
            detail="User not found"
        )

    # 3. Update fields if they are provided
    if update_data.name is not None:
        db_user.name = update_data.name

    if update_data.surname is not None:
        db_user.surname = update_data.surname

    # 4. Commit the changes to the database
    db.commit()
    db.refresh(db_user)

    # 5. Return to the user the updated values of profile information
    logger.info(f'Successfully updated profile information for user {current_user["username"]}')
    return {
        "detail": "Profile updated successfully",
        "user": {
            "username": db_user.username,
            "name": db_user.name,
            "surname": db_user.surname,
        }
    }

# Get profile picture route => GET /profile/picture
@router.get("/picture")
def get_profile_picture(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return the raw image data for the user's profile picture.
    Or return 403 if no picture is set.
    """

    # 1. Fetch user from DB
    db_user = db.query(Users).filter(Users.id == current_user["id"]).first()

    # 2. Raise error if user not found
    if not db_user:
        logger.error(f'The user {current_user["username"]} has not been found.')
        raise HTTPException(
            status_code=403, 
            detail="User not found"
        )

    # 3. Convert the dynamic relationship to a list so we can safely check
    pictures = list(db_user.profilePicture)

    # 4. Raise error if the profile picture not found
    if not pictures:
        logger.error(f'No profile picture found for the user {current_user["username"]}.')
        raise HTTPException(
            status_code=403, 
            detail="No profile picture found."
        )

    # 5. Extract the picture and open the picture from the store (located in /uploads)
    pic = pictures[0]
    try:
        with pic.store.open(pic) as f:
            image_bytes = f.read()
    except OSError as e:
        logger.error(f'Error accessing profile picture for user {current_user["username"]}: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve profile picture due to server error."
        )

    # 6. Return the picture as a raw file response or the correct image mimetype if it is set
    mimetype = pic.mimetype or "application/octet-stream"

    # 7. Return the image content to the user making the request
    logger.info(f'Successfully retrieved profile picture for user {current_user["username"]}')
    return Response(content=image_bytes, media_type=mimetype)

# Update profile picture route => PUT /profile/picture
@router.put("/picture", status_code=status.HTTP_200_OK)
async def update_profile_picture(
    current_user: dict = Depends(get_current_user),
    new_picture: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Update (or set) the user's profile picture. If an old picture exists, it is deleted
    (including the file on disk). Then the new one is stored.
    """

    # 1. Fetch user from DB
    db_user = db.query(Users).filter(Users.id == current_user["id"]).first()

    # 2. Raise error if user not found
    if not db_user:
        logger.error(f'The user {current_user["username"]} has not been found.')
        raise HTTPException(
            status_code=403, 
            detail="User not found"
        )

    # 3. Validate the new image
    profilePicture = new_picture
    if profilePicture is not None:
        # Check file extension.
        ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
        ext = os.path.splitext(profilePicture.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.error("The uploaded file is not a valid image.")
            raise HTTPException(
                status_code=403, 
                detail="Uploaded file is not a valid image."
            )
        
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
                logger.error("The uploaded file is not a valid image.")
                raise HTTPException(
                    status_code=403,
                    detail="Uploaded file is not a valid image."
                )
        else:
            mimetype = provided_mimetype

    file_data = await profilePicture.read()

    # 4. Validate the image using Pillow => Especially check the magick bytes at the beginning of the file
    try:
        bytes_io = BytesIO(file_data)
        image = Image.open(bytes_io)
        image.verify()  # Verify image integrity
        # Re-open to ensure it's usable afterwards:
        bytes_io.seek(0)
        image = Image.open(bytes_io)
        if image.format not in {"JPEG", "PNG"}:
            logger.error("The uploaded file is not a valid image.")
            raise HTTPException(
                status_code=403,
                detail="Uploaded file is not a valid image."
            )
        width, height = image.size
    except Exception as e:
        logger.error("The uploaded file is not a valid image.")
        raise HTTPException(
            status_code=403,
            detail="Uploaded file is not a valid image."
        )

    # 5. Remove the old picture (if any) inside a store_context
    from sqlalchemy_imageattach.entity import store_context
    from app.models import store

    with store_context(store):
        # Convert to list so we can iterate the existing pictures
        old_pictures = list(db_user.profilePicture)
        for old_pic in old_pictures:
            db.delete(old_pic)
        db.commit()  # This triggers the post-delete hook to remove old files from disk

        # 6. Create a new UserPicture record
        new_user_pic = UserPicture()
        new_user_pic.mimetype = mimetype
        new_user_pic.width = width
        new_user_pic.height = height
        new_user_pic.store = store
        new_user_pic.file = BytesIO(file_data)
        db_user.profilePicture = [new_user_pic]

        # 7. Commit to save new picture
        db.commit()
        db.refresh(db_user)

    # 8. Inform the user that the profile picture was successfully updated
    logger.info(f'Successfully updated the profile picture for user {current_user["username"]}')
    return {"detail": "Profile picture updated successfully."}