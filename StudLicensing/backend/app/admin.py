# ========================================================
# Imports
# ========================================================
import os
from fastapi import APIRouter, Depends, HTTPException, Response, Form, File, UploadFile, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Annotated, Optional
from datetime import timedelta, datetime
from sqlalchemy_imageattach.entity import store_context
from PIL import Image
from io import BytesIO
from app.database import SessionLocal
from app.auth import get_current_user, create_validation_token, send_validation_email, BACKEND_URL, FRONTEND_URL
from app.logger import logger
from app.models import (
    Users, UserPicture, UserTypeEnum, 
    Admin, CompanyAdmin, CompanyClient, 
    CompanyCommercial, CompanyDevelopper, Company,
    SessionTokens, ValidationTokens, PasswordResetTokens,
    store
)



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

# Create user account => POST /auth/account_create
@router.post("/account_create", status_code=status.HTTP_201_CREATED)
async def create_user(    
    username: EmailStr = Form(...),
    name: str = Form(...),
    surname: str = Form(...),
    user_type: UserTypeEnum = Form(...),
    company_id: Optional[int] = Form(None),
    profilePicture: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a user account according to role hierarchy.
    No password is set during account creation; a reset link is emailed.
    """

    # 1. Get creator information
    creator_type = current_user["type"]
    creator_id = current_user["id"]

    # 2. Forbid non-admins from providing company_id
    if creator_type != UserTypeEnum.admin and company_id is not None:
        logger.error(f"User of type '{creator_type}' attempted to specify company_id={company_id}, which is forbidden.")
        raise HTTPException(
            status_code=403,
            detail="Account creation forbidden."
        )

    # 3. Check if creator has permission to create the requested user type
    allowed = False
    same_company_required = False

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
    elif creator_type in {
        UserTypeEnum.company_commercial,
        UserTypeEnum.company_developper,
    } and user_type == UserTypeEnum.company_client:
        allowed = True
        same_company_required = True

    # 4. Forbid basic account creation
    if user_type == UserTypeEnum.basic:
        logger.error("Attempted to create a user of forbidden type 'basic'.")
        raise HTTPException(
            status_code=403,
            detail="Account creation forbidden."
        )

    # 5. Forbid sladmin account creation if the company id is provided
    if user_type == UserTypeEnum.admin and company_id is not None:
        logger.error("Attempted to create an 'sladmin' with a company_id, which is not allowed.")
        raise HTTPException(
            status_code=403,
            detail="Account creation forbidden."
        )

    # 6. Throw error if the creation of account is not possible
    if not allowed:
        logger.warning(f"Account creation not allowed: User {current_user['username']} (ID: {current_user['id']}) with account type {creator_type} tried to create a user of type {user_type} for company {company_id}")
        raise HTTPException(
            status_code=403,
            detail="Account creation forbidden."
        )
        
    # 7. Check if CompanyClient user already exists => update company table correspondance to add user to a new company
    if user_type == UserTypeEnum.company_client:
        existing_client = db.query(CompanyClient).filter(CompanyClient.username == username).first()
        if existing_client:
            # Admins can update without needing a company association
            if creator_type != UserTypeEnum.admin:
                # Non-admins should inherit their company_id
                creator = db.query(Users).filter(Users.id == creator_id).first()
                if not creator or not hasattr(creator, "company_id") or creator.company_id is None:
                    logger.error("The account trying to create a new account is not associated with a company.")
                    raise HTTPException(
                        status_code=403,
                        detail="Account creation forbidden."
                    )
                company_id = creator.company_id
            # Update the companies field without sending validation email
            if company_id:
                company = db.query(Company).filter(Company.id == company_id).first()
                if not company:
                    logger.error(f"Provided company_id {company_id} does not correspond to any Company in DB.")
                    raise HTTPException(
                        status_code=403,
                        detail="Account creation forbidden."
                    )
                if company not in existing_client.companies:
                    existing_client.companies.append(company)
                    db.commit()
                logger.info(f"The new company {company_id} has been added for user {username}")
                return {"detail": "CompanyClient company associations updated successfully."}
    
    # 8. Determine company_id
    if creator_type == UserTypeEnum.admin:
        if user_type != UserTypeEnum.admin and company_id is None:
            logger.error("Company ID must be provided by Admin when creating client-related accounts.")
            raise HTTPException(
                status_code=403,
                detail="Account creation forbidden."
            )
        company_id = company_id
    else:
        # Non-admins should inherit their company_id
        creator = db.query(Users).filter(Users.id == creator_id).first()
        if not creator or not hasattr(creator, "company_id") or creator.company_id is None:
            logger.error("The account trying to create a new account is not associated with a company.")
            raise HTTPException(
                status_code=403,
                detail="Account creation forbidden."
            )
        company_id = creator.company_id

    # 9. Check the company_id exists
    if user_type != UserTypeEnum.admin:
        if not db.query(Company).filter(Company.id == company_id).first():
            logger.error(f"Provided company_id {company_id} does not correspond to any Company in DB.")
            raise HTTPException(
                status_code=403,
                detail="Account creation forbidden."
            )

    # 10. Map user type to subclass
    user_class_map = {
        UserTypeEnum.admin: Admin,
        UserTypeEnum.company_admin: CompanyAdmin,
        UserTypeEnum.company_client: CompanyClient,
        UserTypeEnum.company_commercial: CompanyCommercial,
        UserTypeEnum.company_developper: CompanyDevelopper,
    }
    UserClass = user_class_map.get(user_type)
    if not UserClass:
        logger.error("Unsupported user type.")
        raise HTTPException(
            status_code=403,
            detail="Account creation forbidden."
        )

    # 11. Check if username/email already exists in DB
    existing_user = db.query(Users).filter(Users.username == username).first()
    if existing_user:
        logger.error(f"User with email '{username}' already exists.")
        raise HTTPException(
            status_code=403,
            detail="Account creation forbidden."
        )

    # 12. Construct user kwargs
    user_kwargs = {
        "username": username,
        "name": name,
        "surname": surname,
        "creationDate": datetime.utcnow(),
        "activated": False,
        "userType": user_type
    }
    if user_type not in {UserTypeEnum.admin, UserTypeEnum.company_client}:
        user_kwargs["company_id"] = company_id

    # 13. For new CompanyClient, do not associate company directly in kwargs to avoid premature list initialization issues
    if user_type == UserTypeEnum.company_client and company_id:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            logger.error(f"Provided company_id {company_id} does not correspond to any Company in DB.")
            raise HTTPException(status_code=403, detail="Invalid company ID.")
    
    new_user = UserClass(**user_kwargs)

    # 14. Process the profile picture if provided.
    if profilePicture is not None:
        # Check file extension.
        ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
        ext = os.path.splitext(profilePicture.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.error("Uploaded file is not a valid image.")
            raise HTTPException(status_code=403, detail="Uploaded file is not a valid image.")
        
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
                logger.error("Uploaded file is not a valid image.")
                raise HTTPException(
                    status_code=403,
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
                logger.error("Uploaded file is not a valid image.")
                raise HTTPException(status_code=403, detail="Uploaded file is not a valid image.")
            width, height = image.size
        except Exception as e:
            logger.error("Uploaded file is not a valid image.")
            raise HTTPException(status_code=403, detail=f"Uploaded file is not a valid image.")
        
        # Create UserPicture instance
        user_picture = UserPicture()
        user_picture.file = BytesIO(file_data)
        user_picture.mimetype = mimetype
        user_picture.width = width
        user_picture.height = height
        user_picture.store = store
        new_user.profilePicture = [user_picture]

    # 15. Push the new user to the PostgreSQL database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 15.5. For CompanyClient, associate the company after user creation to check actual database state
    if user_type == UserTypeEnum.company_client and company_id:
        company = db.query(Company).filter(Company.id == company_id).first()
        if company and company not in new_user.companies:
            new_user.companies.append(company)
            db.commit()
            db.refresh(new_user)

    # 16. Create a validation token and store it in the Database
    validation_token_str = create_validation_token(db, new_user.id)
    
    # 17. Send the validation email to the newly created user
    validation_link = f"http://{FRONTEND_URL}/validate-email/{validation_token_str}"
    send_validation_email(new_user.username, validation_link)

    # 18. return the newly created user information to the user
    logger.info(f"The user {new_user.username} has been successfully created.")
    return {"username": new_user.username}

# Delete a user account => POST /admin/delete_user
@router.post("/delete_user")
async def delete_user(
    current_user: dict = Depends(get_current_user),
    username: EmailStr = Form(...),
    confirm_username: EmailStr = Form(...),
    db: Session = Depends(get_db)
):
    """
    Function allowing to delete an existing user, also removing all the existing Session, Validation and PasswordReset Tokens.
    """
    # 1. Get creator information
    creator_type = current_user["type"]
    creator_id = current_user["id"]
    # 2. Check if username is equal to the confirm_username
    if username is not None and confirm_username is not None and username != confirm_username:
        logger.error(f'The provided username {username} does not match the provided confirm_username {confirm_username}.')
        raise HTTPException(
            status_code=403,
            detail=f"The provided username {username} does not match the provided confirm_username {confirm_username}."
        )
    # 3. Query the database in order to find the user that is going to be removed
    db_user = db.query(Users).filter(Users.username == username).first()
    # 4. Raise error if user not found
    if not db_user:
        logger.error(f'The user {username} has not been found.')
        raise HTTPException(
            status_code=403,
            detail="Delete user account forbidden."
        )
    # 5. Prevent self-deletion for admin users
    if current_user["id"] == db_user.id and creator_type == UserTypeEnum.admin:
        logger.error(f'The admin user {current_user["username"]} with id = {current_user["id"]} attempted to delete themselves, which is forbidden.')
        raise HTTPException(
            status_code=403,
            detail="Delete user account forbidden."
        )
    # 6. Check if user performing the request has the permission to delete the specified user account
    allowed = False
    same_company_required = False
    if creator_type == UserTypeEnum.admin:
        allowed = True
    elif creator_type == UserTypeEnum.company_admin:
        if db_user.userType in {
            UserTypeEnum.company_admin,
            UserTypeEnum.company_client,
            UserTypeEnum.company_commercial,
            UserTypeEnum.company_developper,
        }:
            allowed = True
            same_company_required = True
    # 7. Throw error if the removal of account is forbidden
    if not allowed:
        logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} of type = {current_user["type"]} tried to delete the user {username} of type = {db_user.userType}.')
        raise HTTPException(
            status_code=403,
            detail="Delete user account forbidden."
        )
    # 8. Case of requesting user company_admin and the company_user to be removed is a member of several companies
    if creator_type == UserTypeEnum.company_admin:
        # Get the company_id of the company_admin performing the request
        requestor_db_user = db.query(Users).filter(Users.username == current_user["username"]).first()
        if not requestor_db_user:
            logger.error(f'The user {current_user["username"]} has not been found.')
            raise HTTPException(
                status_code=403,
                detail="Delete user account forbidden."
            )
        # Get the company object of the user requesting the deletion of another user
        company = db.query(Company).filter(Company.id == requestor_db_user.company_id).first()
        if not company:
            logger.error(f"The company_id {requestor_db_user.company_id} does not correspond to any Company in DB.")
            raise HTTPException(
                status_code=403,
                detail="Delete user account forbidden."
            )
        if db_user.userType == UserTypeEnum.company_client:
            # Check if the company_admin is in the same company as the company_client scheduled for removal
            if company not in db_user.companies:
                client_company_ids = {c.id for c in db_user.companies}
                logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} of type = {current_user["type"]} from company with the id = {requestor_db_user.company_id} tried to delete the user {username} of type = {db_user.userType} belonging to companies = {client_company_ids}.')
                raise HTTPException(
                    status_code=403,
                    detail="Delete user account forbidden."
                )
            else:
                # Case of company_user belonging to several companies => remove from company
                if len(db_user.companies) > 1:
                    db_user.companies.remove(company)
                    db.commit()
                    db.refresh(db_user)
                    logger.info(f'The user {current_user["username"]} with id = {current_user["id"]} has removed the user {db_user.username} with id = {db_user.id} from the company {company.companyName}.')
                    return {"detail": "Account deleted successfully."}
                # Case of company_user belonging to one company => delete user
                else:
                    # Remove session tokens manually
                    db.query(SessionTokens).filter_by(user_id=db_user.id).delete()
                    db.commit()
                    # Remove validation tokens manually
                    db.query(ValidationTokens).filter_by(user_id=db_user.id).delete()
                    db.commit()
                    # Remove password reset tokens manually
                    db.query(PasswordResetTokens).filter_by(user_id=db_user.id).delete()
                    db.commit()
                    # Cleanly delete the user
                    with store_context(store):
                        db.delete(db_user)
                        db.commit()
                    logger.info(f'The user {current_user["username"]} with id = {current_user["id"]} has successfully deleted the user {db_user.username} with id = {db_user.id}.')
                    return {"detail": "Account deleted successfully."}
        else:
            # Check if the company_admin is in the same company as the user scheduled for removal
            if db_user.company_id != requestor_db_user.company_id:
                logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} of type = {current_user["type"]} from company with the id = {requestor_db_user.company_id} tried to delete the user {username} of type = {db_user.userType} belonging to the company = {db_user.company_id}.')
                raise HTTPException(
                    status_code=403,
                    detail="Delete user account forbidden."
                )
            # Remove session tokens manually
            db.query(SessionTokens).filter_by(user_id=db_user.id).delete()
            db.commit()
            # Remove validation tokens manually
            db.query(ValidationTokens).filter_by(user_id=db_user.id).delete()
            db.commit()
            # Remove password reset tokens manually
            db.query(PasswordResetTokens).filter_by(user_id=db_user.id).delete()
            db.commit()
            # Cleanly delete the user
            with store_context(store):
                db.delete(db_user)
                db.commit()
            logger.info(f'The user {current_user["username"]} with id = {current_user["id"]} has successfully deleted the user {db_user.username} with id = {db_user.id}.')
            return {"detail": "Account deleted successfully."}
    # 9. If the requestor is an admin => proceed to the removal of the user account
    # Remove session tokens manually
    db.query(SessionTokens).filter_by(user_id=db_user.id).delete()
    db.commit()
    # Remove validation tokens manually
    db.query(ValidationTokens).filter_by(user_id=db_user.id).delete()
    db.commit()
    # Remove password reset tokens manually
    db.query(PasswordResetTokens).filter_by(user_id=db_user.id).delete()
    db.commit()
    # Cleanly delete the user
    with store_context(store):
        db.delete(db_user)
        db.commit()
    logger.info(f'The user {current_user["username"]} with id = {current_user["id"]} has successfully deleted the user {db_user.username} with id = {db_user.id}.')
    return {"detail": "Account deleted successfully."}

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
            status_code=403, 
            detail="Username modification forbidden."
        )

    # 4. Check if Form parameters are valid
    if new_username is not None and confirm_new_username != new_username:
        logger.error(f'The provided new_username {new_username} does not match the provided confirm_new_username {confirm_new_username}.')
        raise HTTPException(
            status_code=403, 
            detail=f"The provided new_username {new_username} does not match the provided confirm_new_username {confirm_new_username}."
        )
    if old_username is not None and old_username == new_username:
        logger.error(f'The provided old_username {old_username} cannot be the same as the new_username.')
        raise HTTPException(
            status_code=403, 
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
            status_code=403,
            detail="Username modification forbidden."
        )

    # 7. Fetch the requesting user from the DB if the user is of type company_admin
    if creator_type == UserTypeEnum.company_admin:
        db_requesting_user = db.query(Users).filter(Users.id == current_user["id"]).first()

        # 8. Raise error if user not found
        if not db_requesting_user:
            logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} has not been found.')
            raise HTTPException(
                status_code=403, 
                detail="Username modification forbidden."
            )

    # 9. Check if the new_username already exists in DB
    db_check = db.query(Users).filter(Users.username == new_username).first()

    if db_check:
        logger.error(f'The user {new_username} is already in use by the user with id = {db_check.id}, you cannot modify the email to a username that is already in use.')
        raise HTTPException(
            status_code=403, 
            detail="Username modification forbidden."
        )

    # 10. Check if the target user is a company_client and is member of several companies => Forbid the operation
    if user_type == UserTypeEnum.company_client:
        company_count = len(db_user.companies)
        client_company_ids = {c.id for c in db_user.companies}
        if company_count > 1:
            logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} tried to modify the user {old_username} with id = with id = {db_user.id} belonging to companies = {client_company_ids}. Cannot change the username of a company_client belonging to several companies.')
            raise HTTPException(
                    status_code=403, 
                    detail="Username modification forbidden."
                )
        
    # 11. Perform username modification, check if the same company id id the user is a company_admin
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
                    status_code=403, 
                    detail="Username modification forbidden."
                )
        else:
            # Case of the company_admin, company_commercial and company_developper users
            if db_user.company_id != db_requesting_user.company_id:
                logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} and a company_id = {db_requesting_user.company_id} tried to modify the user {old_username} with id = with id = {db_user.id} and a company_id = {db_user.company_id}.')
                raise HTTPException(
                    status_code=403, 
                    detail="Username modification forbidden."
                )
            else:
                db_user.username = new_username
    
    # 12. Commit the changes to the database
    db.commit()
    db.refresh(db_user)

    # 13. Return to the user the updated username (email address)
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
            status_code=403, 
            detail=f"The provided username {username} does not match the provided confirm_username {confirm_username}."
        )

    # 3. Fetch the user for which the username change is requested from DB
    db_user = db.query(Users).filter(Users.username == username).first()

    # 4. Raise error if user not found
    if not db_user:
        logger.error(f'The user {username} has not been found.')
        raise HTTPException(
            status_code=403, 
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
            status_code=403,
            detail="User profile modification forbidden."
        )

    # 7. Fetch the requesting user from the DB if the user is of type company_admin
    if creator_type == UserTypeEnum.company_admin:
        db_requesting_user = db.query(Users).filter(Users.id == current_user["id"]).first()

        # 8. Raise error if user not found
        if not db_requesting_user:
            logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} has not been found.')
            raise HTTPException(
                status_code=403, 
                detail="User profile modification forbidden."
            )

    # 9. Check if the target user is a company_client and is member of several companies => Forbid the operation
    if user_type == UserTypeEnum.company_client:
        company_count = len(db_user.companies)
        client_company_ids = {c.id for c in db_user.companies}
        if company_count > 1:
            logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} tried to modify the user {username} with id = with id = {db_user.id} belonging to companies = {client_company_ids}. Cannot change the information of a company_client belonging to several companies.')
            raise HTTPException(
                    status_code=403, 
                    detail="Username profile modification forbidden."
                )

    # 10. Perform user profile information modification, check if the same company id id the user is a company_admin
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
                    status_code=403, 
                    detail="User profile modification forbidden."
                )
        else:
            # Case of the company_admin, company_commercial and company_developper users
            if db_user.company_id != db_requesting_user.company_id:
                logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} and a company_id = {db_requesting_user.company_id} tried to modify the user {username} with id = with id = {db_user.id} and a company_id = {db_user.company_id}.')
                raise HTTPException(
                    status_code=403, 
                    detail="User profile modification forbidden."
                )
            else:
                if name is not None:
                    db_user.name = name
                if surname is not None:
                    db_user.surname = surname
    
    # 11. Commit the changes to the database
    db.commit()
    db.refresh(db_user)

    # 12. Return to the user the updated username (email address)
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
            status_code=403, 
            detail=f"Add user to company forbidden."
        )

    # 3. Check if username is equal to the confirm_username
    if username is not None and confirm_username is not None and username != confirm_username:
        logger.error(f'The provided username {username} does not match the provided confirm_username {confirm_username}.')
        raise HTTPException(
            status_code=403, 
            detail=f"The provided username {username} does not match the provided confirm_username {confirm_username}."
        )

    # 4. Fetch the user for which the company addition is requested from DB
    db_user = db.query(Users).filter(Users.username == username).first()

    # 5. Raise error if user not found
    if not db_user:
        logger.error(f'The user {username} has not been found.')
        raise HTTPException(
            status_code=403, 
            detail="Add user to company forbidden."
        )

    # 6. Verify that the account type of the modified account is company_client
    if db_user.userType != UserTypeEnum.company_client:
        logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} tried to add the user {username} with userType {db_user.userType} to the company with id = {company_id}.')
        raise HTTPException(
            status_code=403, 
            detail="Add user to company forbidden."
        )

    # 7. Check the company_id exists
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        logger.error(f"Provided company_id {company_id} does not correspond to any Company in DB.")
        raise HTTPException(
            status_code=403,
            detail="Add user to company forbidden."
        )

    # 8. Add company to the companies list of client_user
    if company not in db_user.companies:
        db_user.companies.append(company)
        # Commit the changes to the database
        db.commit()
        db.refresh(db_user)
        logger.info(f'The user {current_user["username"]} with id = {current_user["id"]} successfully added the user {username} with id = {db_user.id} to the company {company.companyName} with id = {company_id}.')
    else:
        logger.info(f"User {username} is already part of company_id {company_id}, no action needed.")
        return {
            "detail": f"User {username} is already part of the company {company.companyName} with id = {company_id}"
        }
    
    # 9. Return to the user the updated username (email address)
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
            status_code=403, 
            detail=f"Remove user from company forbidden."
        )

    # 3. Check if username is equal to the confirm_username
    if username is not None and confirm_username is not None and username != confirm_username:
        logger.error(f'The provided username {username} does not match the provided confirm_username {confirm_username}.')
        raise HTTPException(
            status_code=403, 
            detail=f"The provided username {username} does not match the provided confirm_username {confirm_username}."
        )

    # 4. Fetch the user for which the company addition is requested from DB
    db_user = db.query(Users).filter(Users.username == username).first()

    # 5. Raise error if user not found
    if not db_user:
        logger.error(f'The user {username} has not been found.')
        raise HTTPException(
            status_code=403, 
            detail="Remove user from company forbidden."
        )

    # 6. Verify that the account type of the modified account is company_client
    if db_user.userType != UserTypeEnum.company_client:
        logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} tried to remove the user {username} with userType {db_user.userType} from the company with id = {company_id}.')
        raise HTTPException(
            status_code=403, 
            detail="Remove user from company forbidden."
        )

    # 7. Check the company_id exists
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        logger.error(f"Provided company_id {company_id} does not correspond to any Company in DB.")
        raise HTTPException(
            status_code=403,
            detail="Remove user from company forbidden."
        )

    # 8. Remove company from the companies list of client_user
    if company in db_user.companies:
        if len(db_user.companies) > 1:
            db_user.companies.remove(company)
        else:
            logger.error(f"Cannot remove the only remaining company from user {username}.")
            raise HTTPException(
                status_code=403,
                detail="Remove user from company forbidden."
            )
    else:
        logger.error(f"User {username} is not part of company_id {company_id}.")
        raise HTTPException(
            status_code=403,
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



# Search for a user => POST /admin/search_user
@router.post("/search_user")
def search_user(
    current_user: dict = Depends(get_current_user),
    searched_user: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Search for a User by email , first name, surname or a combination of first name and surname.
    Only admin, company_admin, company_commercial and company_commercial users can perform this search.
    Admin can search all
    Company_admin can search all from the same company
    Company_commercial and Company_developper can only clients from the same company
    """

    # 1. Check if the user performing the request is an admin, company_admin, company_commercial or company_commercial
    if current_user["type"] != UserTypeEnum.admin and \
       current_user["type"] != UserTypeEnum.company_admin and \
       current_user["type"] != UserTypeEnum.company_commercial and \
       current_user["type"] != UserTypeEnum.company_developper:
        logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} of type {current_user["type"]} tried to perform a user search.')
        raise HTTPException(
            status_code=403, 
            detail="Search request forbidden"
        )

    # 2. Allow empty string searches ⇒ normalize None/blank to ""
    searched_user = (searched_user or "").strip()

    # 3. Initialize the query
    query = db.query(Users)
    
    # 4. Prepare the filters query depending on the number of words in the searched_user
    filters = []
    if searched_user:
        # Split the searched_user into parts
        parts = searched_user.split()
        if len(parts) == 1:     
            # If only one part is provided, search by email or first name or surname
            filters.append(Users.username.ilike(f"%{searched_user}%"))
            filters.append(Users.name.ilike(f"%{searched_user}%"))
            filters.append(Users.surname.ilike(f"%{searched_user}%"))
            
        elif len(parts) == 2:
            # If two parts are provided, search by first name and surname in any order
            filters.append(and_(Users.name.ilike(f"%{parts[0]}%"), Users.surname.ilike(f"%{parts[1]}%")))
            filters.append(and_(Users.surname.ilike(f"%{parts[0]}%"), Users.name.ilike(f"%{parts[1]}%")))
        else:
            # Try all combinations of first name and surname
            for n in range(1, len(parts)):
                # Try with first name are firs n parts and surname is the remaining parts
                first_name = " ".join(parts[:n])
                surname = " ".join(parts[n:])
                filters.append(and_(Users.name.ilike(f"%{first_name}%"),Users.surname.ilike(f"%{surname}%")))

                #Try with surname as first n parts and first name is the remaining parts
                first_name = " ".join(parts[n:])
                surname = " ".join(parts[:n])
                filters.append(and_(Users.name.ilike(f"%{first_name}%"),Users.surname.ilike(f"%{surname}%")))

    #5 Prepare the company and user type related extra filter depending on the searching user type    
    ## Get company of current user if company_admin, company_commercial or company_developper 
    current_user_company = None
    same_company_required = False
    if current_user["type"] in {UserTypeEnum.company_admin, UserTypeEnum.company_commercial, UserTypeEnum.company_developper}:
            current_user_info = db.query(Users).filter(Users.id == current_user["id"]).first()
            current_user_company = current_user_info.company_id if current_user_info else None
            same_company_required = True if current_user_info else False
            
    current_user_based_filter = []   
    if current_user["type"] in {UserTypeEnum.company_commercial, UserTypeEnum.company_developper}:
        # Filter by userType to only include company_client users
        current_user_based_filter.append(Users.userType == UserTypeEnum.company_client)
 
    # 6. Combine the filters with the current_user_based_filter
    #query = query.filter(and_(or_(*filters),and_(*current_user_based_filter)))
    if filters:
        combined_filter = or_(*filters)
    else:
        combined_filter = True

    if current_user_based_filter:
        user_based_filter = and_(*current_user_based_filter)
    else:
        user_based_filter = True

    query = query.filter(and_(combined_filter, user_based_filter))

        
    # 7. Execute the query and get the results
    resulting_users = query.all()
    
    # 8. Filter the results by company if the user is a company_admin, company_commercial or company_developper
    filtered_resulting_users = []
    if same_company_required and current_user_company is not None:
        for user in resulting_users :
            if user.userType in {UserTypeEnum.company_admin, UserTypeEnum.company_commercial, UserTypeEnum.company_developper}:
                if user.company_id == current_user_company:
                    filtered_resulting_users.append(user)
            elif user.userType == UserTypeEnum.company_client:
                if current_user_company in [company.id for company in user.companies]:
                    filtered_resulting_users.append(user)
    elif current_user["type"] == UserTypeEnum.admin:
        filtered_resulting_users= resulting_users
    

    # 9. If no company is found, raise an HTTP exception
    if not filtered_resulting_users:
        logger.error(f'User {current_user["username"]} with id = {current_user["id"]} has requested a user that does not exist within the users it can search.')
        raise HTTPException(status_code=403, detail="No users found.")
    
    # 10. Return the company details
    logger.info(f"Found {len(filtered_resulting_users)} companies matching the search criteria.")
    return {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "surname": user.surname,
                "user_type": user.userType,
                "company": [company.id for company in user.companies] if user.userType == UserTypeEnum.company_client else getattr(user, "company_id", None)
            } for user in filtered_resulting_users
        ]
    }