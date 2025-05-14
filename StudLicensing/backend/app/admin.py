# ========================================================
# Imports
# ========================================================
from fastapi import APIRouter, Depends, HTTPException, Response, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Annotated
from app.database import SessionLocal
from app.auth import get_current_user
from app.logger import logger
from app.models import Users, UserTypeEnum



# ========================================================
# Auth router declaration
# ========================================================
router = APIRouter (
    prefix='/admin',
    tags=['admin']
)



# ========================================================
# Database connection
# ========================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# ========================================================
# Dependencies setup
# ========================================================
db_dependency = Annotated[Session, Depends(get_db)]



# ========================================================
# Classes definition for various routes
# ========================================================

# UpdateUsernameRequest class used for user email modification
class UpdateUsernameRequest(BaseModel):
    old_username: EmailStr
    new_username: EmailStr
    confirm_new_username: EmailStr



# ===========================================
# API Routes
# ===========================================

# Get profile information route => GET /profile/info
@router.post("/update_username")
def update_username(
    current_user: dict = Depends(get_current_user),
    old_username: EmailStr = Form(...),
    new_username: EmailStr = Form(...),
    confirm_new_username: EmailStr = Form(...),
    db: Session = Depends(get_db)
):
    """
    Updates the username of a specific user (email address).
    """
    
    # 1. Get creator information
    creator_type = current_user["type"]
    creator_id = current_user["id"]

    # 2. Fetch the user for which the username change is requested from DB
    db_user = db.query(Users).filter(Users.username == old_username).first()

    # 3. Raise error if user not found
    if not db_user:
        logger.error(f'The user {old_username} has not been found.')
        raise HTTPException(
            status_code=404, 
            detail="Username modification forbidden."
        )

    # 4. Check if Form parameters are valid
    if new_username is not None and confirm_new_username != new_username:
        raise ValueError("new_username and confirm_new_username must match")
    if old_username is not None and old_username == new_username:
        raise ValueError("old_username and new_username cannot be the same")

    # 5. Check if the user is authorized to modify the username of the user
    allowed = False
    same_company_required = False
    user_type = db_user.userType

    if creator_type == UserTypeEnum.admin:
        allowed = True
    elif creator_type == UserTypeEnum.company_admin:
        if user_type in {
            UserTypeEnum.company_admin,
            UserTypeEnum.company_client,
            UserTypeEnum.company_commercial,
            UserTypeEnum.company_developper,
        }:
            allowed = True
            same_company_required = True

    # 6. Return error if the user is not allowed to modify the username
    if not allowed:
        logger.error(f'User {current_user["username"]} with id = {current_user["id"]} attempted to modify the username of {old_username} with id = {db_user.id}.')
        raise HTTPException(
            status_code=400,
            detail="Username modification forbidden."
        )

    # 7. Fetch the requesting user from the DB if the user is of type company_admin
    if creator_type == UserTypeEnum.company_admin:
        db_requesting_user = db.query(Users).filter(Users.id == current_user["id"]).first()

        # 8. Raise error if user not found
        if not db_requesting_user:
            logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} has not been found.')
            raise HTTPException(
                status_code=404, 
                detail="Username modification forbidden."
            )

    # 9. Check if the new_username already exists in DB
    db_check = db.query(Users).filter(Users.username == new_username).first()

    if db_check:
        logger.error(f'The user {new_username} is already in use by the user with id = {db_check.id}, you cannot modify the email to a username that is already in use.')
        raise HTTPException(
            status_code=404, 
            detail="Username modification forbidden."
        )

    # 10. Perform username modification, check if the same company id id the user is a company_admin
    if not same_company_required:
        # Case of Admin user
        db_user.username = new_username
    else:
        # Check if the company id is the same
        if user_type == UserTypeEnum.company_client:
            # Case of the modification of a company_client user
            client_company_ids = {c.id for c in db_user.companies}

            if db_requesting_user.company_id in client_company_ids:
                db_user.username = new_username
            else:
                logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} and a company_id = {db_requesting_user.company_id} tried to modify the user {old_username} with id = with id = {db_user.id} and a company_id = {client_company_ids}.')
                raise HTTPException(
                    status_code=404, 
                    detail="Username modification forbidden."
                )
        else:
            # Case of the company_admin, company_commercial and company_developper users
            if db_user.company_id != db_requesting_user.company_id:
                logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} and a company_id = {db_requesting_user.company_id} tried to modify the user {old_username} with id = with id = {db_user.id} and a company_id = {db_user.company_id}.')
                raise HTTPException(
                    status_code=404, 
                    detail="Username modification forbidden."
                )
            else:
                db_user.username = new_username
    
    # 11. Commit the changes to the database
    db.commit()
    db.refresh(db_user)

    # 12. Return to the user the updated username (email address)
    logger.info(f'Successfully updated the username of {old_username} with id = {db_user.id} to {new_username}')
    return {
        "detail": "Username updated successfully",
        "user": {
            "username": new_username,
            "name": db_user.name,
            "surname": db_user.surname,
        }
    }