# ========================================================
# Imports
# ========================================================
from fastapi import APIRouter, Depends, HTTPException, Response, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Annotated, Optional
from app.database import SessionLocal
from app.auth import get_current_user
from app.logger import logger
from app.models import Users, UserTypeEnum, Company



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



# ===========================================
# API Routes
# ===========================================

# Update username route => POST /admin/update_username
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
        logger.error(f'The provided new_username {new_username} does not match the provided confirm_new_username {confirm_new_username}.')
        raise HTTPException(
            status_code=404, 
            detail=f"The provided new_username {new_username} does not match the provided confirm_new_username {confirm_new_username}."
        )
    if old_username is not None and old_username == new_username:
        logger.error(f'The provided old_username {old_username} cannot be the same as the new_username.')
        raise HTTPException(
            status_code=404, 
            detail=f"The provided old_username {old_username} cannot be the same as the new_username."
        )

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
                logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} and a company_id = {db_requesting_user.company_id} tried to modify the user {old_username} with id = with id = {db_user.id} belonging to companies = {client_company_ids}.')
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
    logger.info(f'The user {current_user["username"]} with id = {current_user["id"]} successfully updated the username of {old_username} with id = {db_user.id} to {new_username}.')
    return {
        "detail": "Username updated successfully",
        "user": {
            "username": new_username,
            "name": db_user.name,
            "surname": db_user.surname,
        }
    }

# Update user profile information route => POST /admin/update_user_profile_info
@router.post("/update_user_profile_info")
def update_user_profile_info(
    current_user: dict = Depends(get_current_user),
    username: EmailStr = Form(...),
    confirm_username: EmailStr = Form(...),
    name: Optional[str] = Form(
        None,
        min_length=1,
        max_length=50,
        description="First name (1-50 characters)",
    ),
    surname: Optional[str] = Form(
        None,
        min_length=1,
        max_length=50,
        description="Surname (1-50 characters)",
    ),
    db: Session = Depends(get_db)
):
    """
    Updates the username of a specific user (email address).
    """
    
    # 1. Get creator information
    creator_type = current_user["type"]
    creator_id = current_user["id"]

    # 2. Check if Form parameters are valid
    if username is not None and confirm_username is not None and username != confirm_username:
        logger.error(f'The provided username {username} does not match the provided confirm_username {confirm_username}.')
        raise HTTPException(
            status_code=404, 
            detail=f"The provided username {username} does not match the provided confirm_username {confirm_username}."
        )

    # 3. Fetch the user for which the username change is requested from DB
    db_user = db.query(Users).filter(Users.username == username).first()

    # 4. Raise error if user not found
    if not db_user:
        logger.error(f'The user {username} has not been found.')
        raise HTTPException(
            status_code=404, 
            detail="User profile modification forbidden."
        )

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
        logger.error(f'User {current_user["username"]} with id = {current_user["id"]} attempted to modify the profile information of {username} with id = {db_user.id}.')
        raise HTTPException(
            status_code=400,
            detail="User profile modification forbidden."
        )

    # 7. Fetch the requesting user from the DB if the user is of type company_admin
    if creator_type == UserTypeEnum.company_admin:
        db_requesting_user = db.query(Users).filter(Users.id == current_user["id"]).first()

        # 8. Raise error if user not found
        if not db_requesting_user:
            logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} has not been found.')
            raise HTTPException(
                status_code=404, 
                detail="User profile modification forbidden."
            )

    # 9. Perform user profile information modification, check if the same company id id the user is a company_admin
    if not same_company_required:
        # Case of Admin user
        if name is not None:
            db_user.name = name
        if surname is not None:
            db_user.surname = surname
    else:
        # Check if the company id is the same
        if user_type == UserTypeEnum.company_client:
            # Case of the modification of a company_client user
            client_company_ids = {c.id for c in db_user.companies}

            if db_requesting_user.company_id in client_company_ids:
                if name is not None:
                    db_user.name = name
                if surname is not None:
                    db_user.surname = surname
            else:
                logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} and a company_id = {db_requesting_user.company_id} tried to modify the user profile of the user {username} with id = with id = {db_user.id} belonging to companies = {client_company_ids}.')
                raise HTTPException(
                    status_code=404, 
                    detail="User profile modification forbidden."
                )
        else:
            # Case of the company_admin, company_commercial and company_developper users
            if db_user.company_id != db_requesting_user.company_id:
                logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} and a company_id = {db_requesting_user.company_id} tried to modify the user {username} with id = with id = {db_user.id} and a company_id = {db_user.company_id}.')
                raise HTTPException(
                    status_code=404, 
                    detail="User profile modification forbidden."
                )
            else:
                if name is not None:
                    db_user.name = name
                if surname is not None:
                    db_user.surname = surname
    
    # 10. Commit the changes to the database
    db.commit()
    db.refresh(db_user)

    # 11. Return to the user the updated username (email address)
    logger.info(f'The user {current_user["username"]} with id = {current_user["id"]} successfully updated the profile information of {username} with id = {db_user.id}.')
    return {
        "detail": "User profile information updated successfully",
        "user": {
            "username": username,
            "name": name,
            "surname": surname,
        }
    }

# Add client_user to a company => POST /admin/add_client_user_to_company
@router.post("/add_client_user_to_company")
def add_client_user_to_company(
    current_user: dict = Depends(get_current_user),
    username: EmailStr = Form(...),
    confirm_username: EmailStr = Form(...),
    company_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Adds a client_user to an additional company.
    """
    
    # 1. Get creator information
    creator_type = current_user["type"]
    creator_id = current_user["id"]

    # 2. Check if the user is an Admin
    if creator_type != UserTypeEnum.admin:
        logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} tried to add the user {username} to the company with id = {company_id}.')
        raise HTTPException(
            status_code=404, 
            detail=f"Add user to company forbidden."
        )

    # 3. Check if username is equal to the confirm_username
    if username is not None and confirm_username is not None and username != confirm_username:
        logger.error(f'The provided username {username} does not match the provided confirm_username {confirm_username}.')
        raise HTTPException(
            status_code=404, 
            detail=f"The provided username {username} does not match the provided confirm_username {confirm_username}."
        )

    # 4. Fetch the user for which the company addition is requested from DB
    db_user = db.query(Users).filter(Users.username == username).first()

    # 5. Raise error if user not found
    if not db_user:
        logger.error(f'The user {username} has not been found.')
        raise HTTPException(
            status_code=404, 
            detail="Add user to company forbidden."
        )

    # 6. Verify that the account type of the modified account is company_client
    if db_user.userType != UserTypeEnum.company_client:
        logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} tried to add the user {username} with userType {db_user.userType} to the company with id = {company_id}.')
        raise HTTPException(
            status_code=404, 
            detail="Add user to company forbidden."
        )

    # 7. Check the company_id exists
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        logger.error(f"Provided company_id {company_id} does not correspond to any Company in DB.")
        raise HTTPException(
            status_code=400,
            detail="Add user to company forbidden."
        )

    # 8. Add company to the companies list of client_user
    if company not in db_user.companies:
        db_user.companies.append(company)
    else:
        logger.error(f"User {username} is already part of company_id {company_id}.")
        raise HTTPException(
            status_code=400,
            detail="Add user to company forbidden."
        )
    
    # 9. Commit the changes to the database
    db.commit()
    db.refresh(db_user)

    # 10. Return to the user the updated username (email address)
    logger.info(f'The user {current_user["username"]} with id = {current_user["id"]} successfully added the user {username} with id = {db_user.id} to the company {company.companyName} with id = {company_id}.')
    return {
        "detail": f"User {username} has successfully been added to the company {company.companyName} with id = {company_id}",
    }

# Remove client_user from a company => POST /admin/remove_client_user_from_company
@router.post("/remove_client_user_from_company")
def remove_client_user_from_company(
    current_user: dict = Depends(get_current_user),
    username: EmailStr = Form(...),
    confirm_username: EmailStr = Form(...),
    company_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Removes a client_user from a company.
    """
    
    # 1. Get creator information
    creator_type = current_user["type"]
    creator_id = current_user["id"]

    # 2. Check if the user is an Admin
    if creator_type != UserTypeEnum.admin:
        logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} tried to remove the user {username} from the company with id = {company_id}.')
        raise HTTPException(
            status_code=404, 
            detail=f"Remove user from company forbidden."
        )

    # 3. Check if username is equal to the confirm_username
    if username is not None and confirm_username is not None and username != confirm_username:
        logger.error(f'The provided username {username} does not match the provided confirm_username {confirm_username}.')
        raise HTTPException(
            status_code=404, 
            detail=f"The provided username {username} does not match the provided confirm_username {confirm_username}."
        )

    # 4. Fetch the user for which the company addition is requested from DB
    db_user = db.query(Users).filter(Users.username == username).first()

    # 5. Raise error if user not found
    if not db_user:
        logger.error(f'The user {username} has not been found.')
        raise HTTPException(
            status_code=404, 
            detail="Remove user from company forbidden."
        )

    # 6. Verify that the account type of the modified account is company_client
    if db_user.userType != UserTypeEnum.company_client:
        logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} tried to remove the user {username} with userType {db_user.userType} from the company with id = {company_id}.')
        raise HTTPException(
            status_code=404, 
            detail="Remove user from company forbidden."
        )

    # 7. Check the company_id exists
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        logger.error(f"Provided company_id {company_id} does not correspond to any Company in DB.")
        raise HTTPException(
            status_code=400,
            detail="Remove user from company forbidden."
        )

    # 8. Remove company from the companies list of client_user
    if company in db_user.companies:
        if len(db_user.companies) > 1:
            db_user.companies.remove(company)
        else:
            logger.error(f"Cannot remove the only remaining company from user {username}.")
            raise HTTPException(
                status_code=400,
                detail="Remove user from company forbidden."
            )
    else:
        logger.error(f"User {username} is not part of company_id {company_id}.")
        raise HTTPException(
            status_code=400,
            detail="Remove user from company forbidden."
        )
    
    # 9. Commit the changes to the database
    db.commit()
    db.refresh(db_user)

    # 10. Return to the user the updated username (email address)
    logger.info(f'The user {current_user["username"]} with id = {current_user["id"]} successfully removed the user {username} with id = {db_user.id} from the company {company.companyName} with id = {company_id}.')
    return {
        "detail": f"User {username} has successfully been removed from the company {company.companyName} with id = {company_id}",
    }