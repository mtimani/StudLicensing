# ========================================================
# Imports
# ========================================================
import os
import smtplib
import uuid
import re
from app.logger import logger, login_logger
from datetime import timedelta, datetime
from typing import Annotated, Optional
from sqlalchemy_imageattach.entity import store_context
from fastapi import APIRouter, Depends, HTTPException, Form, Request, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from starlette import status
from app.database import SessionLocal
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from dotenv import find_dotenv
from email.message import EmailMessage
from app.models import (
    Users, UserTypeEnum, Admin, 
    SessionTokens, ValidationTokens, PasswordResetTokens, 
    store
)



# ========================================================
# Environment variables
# ========================================================

# Load environment variables
dotenv_path = find_dotenv()
if not dotenv_path:
    raise FileNotFoundError("'.env' file not found. Please make sure the file exists in the project directory.")

# Retrieve environment variables.
SECRET_KEY = os.getenv('SECRET_KEY')
BACKEND_URL = os.getenv('BACKEND_URL', 'localhost:8000')
SUPERADMIN_ACCOUNT_USERNAME=os.getenv('SUPERADMIN_ACCOUNT_USERNAME')
SUPERADMIN_ACCOUNT_PASSWORD=os.getenv('SUPERADMIN_ACCOUNT_PASSWORD')

ALGORITHM = "HS256"

# Check that all required variables are set; if any is missing, raise an error.
if SECRET_KEY is None:
    raise ValueError("Environment variable 'SECRET_KEY' is not defined. Please add it to your .env file.")
if BACKEND_URL is None:
    raise ValueError("Environment variable 'BACKEND_URL' is not defined. Please add it to your .env file.")
if SUPERADMIN_ACCOUNT_USERNAME is None:
    raise ValueError("Environment variable 'SUPERADMIN_ACCOUNT_USERNAME' is not defined. Please add it to your .env file.")
if SUPERADMIN_ACCOUNT_PASSWORD is None:
    raise ValueError("Environment variable 'SUPERADMIN_ACCOUNT_PASSWORD' is not defined. Please add it to your .env file.")



# ========================================================
# Environment variables
# ========================================================
AUTHENTICATION_TIME = 20 # In minutes
VALIDATION_TOKEN_TIME = 24 # In hours
PASSWOED_RESET_TOKEN_TIME = 1 # In hours



# ========================================================
# Auth router declaration
# ========================================================
router = APIRouter (
    prefix='/auth',
    tags=['auth']
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
# JWT context setup
# ========================================================
bcrypt_context = CryptContext(schemes = ['bcrypt'], deprecated = 'auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl = 'auth/token')



# ========================================================
# Password policy function
# ========================================================

# Helper function to validate the password policy.
def validate_password_policy(password: str) -> None:
    """
    Checks if the password meets the required policy:
    - Minimum 7 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one symbol (non-alphanumeric character)
    """
    if len(password) < 7:
        raise ValueError("Password must be at least 7 characters long.")
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r'\d', password):
        raise ValueError("Password must contain at least one number.")
    if not re.search(r'[^a-zA-Z0-9]', password):
        raise ValueError("Password must contain at least one symbol.")



# ========================================================
# Create SuperAdmin user function
# ========================================================

# Helper function to create the SuperAdmin user.
def create_superadmin():
    """
    Creates the SuperAdmin user of StudLincensing.
    Checks if the user exists. If not the user is created
    """

    # 1. Establish a local session with the PostgreSQL database
    db: Session = SessionLocal()

    try:
        # 2. Check if the superadmin already exists
        logger.info("Checking if superadmin exists...")
        existing_admin = db.query(Admin).filter(Admin.username == SUPERADMIN_ACCOUNT_USERNAME).first()
        if existing_admin:
            logger.info("Superadmin already exists. No action taken.")
            return

        # 3. Create the superadmin user if the user does not exist
        hashed_password = bcrypt_context.hash(SUPERADMIN_ACCOUNT_PASSWORD)
        superadmin = Admin(
            username=SUPERADMIN_ACCOUNT_USERNAME,
            name="Super",
            surname="Admin",
            hashedPassword=hashed_password,
            creationDate=datetime.utcnow(),
            activated=True,
            userType=UserTypeEnum.admin
        )

        # 4. Commit the user to the Database
        db.add(superadmin)
        db.commit()
        db.refresh(superadmin)
        logger.info(f"Superadmin '{SUPERADMIN_ACCOUNT_USERNAME}' created successfully.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating superadmin: {e}")

    finally:
        db.close()



# ========================================================
# Classes definition for various routes
# ========================================================

# CreateUserRequest class used for user creation
class CreateUserRequest(BaseModel):
    username: EmailStr
    name: str
    surname: str
    user_type: UserTypeEnum
    company_id: Optional[int] = None # Only relevant if creator is Admin

# ChangePasswordRequest class used for changing a users' password
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str

# Token class used for JWT token creation
class Token(BaseModel):
    access_token: str
    token_type: str



# ========================================================
# Email sending functions
# ========================================================

# Send validation email to a user to check if the provided email is correct
def send_validation_email(
    to_email: str, 
    validation_link: str
) -> None:
    """
    Send an email to the specified address with the given validation link.
    SMTP configuration is loaded from environment variables.
    """

    # 1. Retrieve environment variables.
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = os.getenv('SMTP_PORT')
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    FROM_EMAIL = os.getenv('FROM_EMAIL')

    # 2. Check that all necessary configuration variables are provided.
    missing = [var for var in ['SMTP_SERVER', 'SMTP_PORT', 'SMTP_USERNAME', 'SMTP_PASSWORD', 'FROM_EMAIL']
               if os.getenv(var) is None]
    
    # 3. Raise an error if some of the environment variables were not set up
    if missing:
        raise ValueError(f"Missing SMTP configuration for: {', '.join(missing)}")

    # 4. Create the email message.
    msg = EmailMessage()
    msg['Subject'] = "[StudLicensing] Validate Your Email Address"
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    msg.set_content(
        f"Hello,\n\n"
        f"Please click the link below to validate your email address and set your password:\n\n"
        f"{validation_link}\n\n"
        f"This link will expire in 24 hours.\n\n"
        f"Thank you!"
    )

    # 5. Connect to the SMTP server and send the email.
    try:
        with smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT)) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Validation email successfully sent to {to_email}")
    except Exception as e:
        logger.error(f"Error sending validation email to {to_email}: {e}")

# Send password reset email to a user that forgot their password
def send_password_reset_email(
    to_email: str, 
    reset_link: str
) -> None:
    """
    Send a password reset email to the user with the provided reset link.
    """

    # 1. Retrieve environment variables.
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = os.getenv('SMTP_PORT')
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    FROM_EMAIL = os.getenv('FROM_EMAIL')
    
    # 2. Check that all necessary configuration variables are provided.
    missing = [var for var in ['SMTP_SERVER', 'SMTP_PORT', 'SMTP_USERNAME', 'SMTP_PASSWORD', 'FROM_EMAIL']
               if os.getenv(var) is None]

    # 3. Raise an error if some of the environment variables were not set up
    if missing:
        raise ValueError(f"Missing SMTP configuration for: {', '.join(missing)}")
    
    # 4. Create the email message.
    msg = EmailMessage()
    msg['Subject'] = "[StudLicensing] Password Reset Request"
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    msg.set_content(
        f"Hello,\n\n"
        f"We received a request to reset your password. Click the link below to reset it:\n\n"
        f"{reset_link}\n\n"
        f"This link will expire in one hour.\n\n"
        f"If you didn't request a password reset, please ignore this email.\n\n"
        f"Thank you!"
    )
    
    # 5. Connect to the SMTP server and send the email.
    try:
        with smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT)) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Password reset email successfully sent to {to_email}")
    except Exception as e:
        logger.error(f"Error sending password reset email to {to_email}: {e}")



# ========================================================
# Token creation functions (validation and password reset)
# ========================================================

# Create access token (used for user authentication)
def create_access_token(
    username: str, 
    user_id: int, 
    user_type: str,
    expires_delta: timedelta, 
    db: Session
):
    """
    Create a unique, time-limited JWT token used for user authentication.  
    Default expiration is set to the provided parameter value in minutes.
    """

    # 1. Create a unique token per JWT (jti) => to facilitate revocation (for logout purposes)
    jti = str(uuid.uuid4())

    # 2. Setup the expiration time of the token
    expire_time = datetime.utcnow() + expires_delta
    
    # 3. Build the session_token record that will be inserted to the database into the session_tokens table
    session_token = SessionTokens(
        jti=jti,
        user_id=user_id,
        expires_at=expire_time
    )

    # 4. Push the validation record to the Database
    db.add(session_token)
    db.commit()
    db.refresh(session_token)
    
    # 5. Create the JWT that will be used for authentication
    to_encode = {
        "sub": username,
        "id": user_id,
        "type": user_type,
        "jti": jti,
        "exp": expire_time
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    # 6. return the token to the calling function
    logger.info(f'A session token has been issued for the user with the ID = {user_id}')
    return encoded_jwt

# Create email validation token
def create_validation_token(
    db: Session, user_id: int, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a unique, time-limited email validation token.  
    Default expiration is set to 24 hours.
    """

    # 1. Setup expiry time of 24 hours
    expires_delta = expires_delta or timedelta(hours=VALIDATION_TOKEN_TIME)
    expire_time = datetime.utcnow() + expires_delta

    # 2. Create a unique token
    token_str = str(uuid.uuid4())

    # 3. Build the validation record that will be inserted to the database into the validation_tokens table
    validation_record = ValidationTokens(
        token=token_str,
        user_id=user_id,
        expires_at=expire_time
    )

    # 4. Push the validation record to the Database
    db.add(validation_record)
    db.commit()
    db.refresh(validation_record)

    # 5. return the token to the calling function
    logger.info(f'A validation token has been issued for the user with the ID = {user_id}')
    return token_str

# Create a password reset token
def create_password_reset_token(
    db: Session, user_id: int, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a unique, time-limited password reset token.  
    Default expiration is set to 1 hour.
    """

    # 1. Setup expiry time of 1 hour
    expires_delta = expires_delta or timedelta(hours=PASSWOED_RESET_TOKEN_TIME)
    expire_time = datetime.utcnow() + expires_delta

    # 2. Create a unique token
    token_str = str(uuid.uuid4())
    
    # 3. Build the password reset record that will be inserted to the database into the password_reset_tokens table
    reset_record = PasswordResetTokens(
        token=token_str,
        user_id=user_id,
        expires_at=expire_time
    )

    # 4. Push the validation record to the Database
    db.add(reset_record)
    db.commit()
    db.refresh(reset_record)

    # 5. return the token to the calling function
    logger.info(f'A password reset token has been issued for the user with the ID = {user_id}')
    return token_str



# ========================================================
# Authentication status related functions
# ========================================================

# Get current user information function
async def get_current_user(
    token: Annotated[str, Depends(oauth2_bearer)], 
    db: Session = Depends(get_db), response: Response = None
):
    """
    Function that allows other functions to check that the user is authentication and get basic user information from the JWT Token.
    """

    # 1. Retrieve the JWT token of the user and verify the authenticity of the token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        logger.error("User with invalid JWT tried to connect.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user.")

    # 2. Extract user information from the JWT
    username: str = payload.get("sub")
    user_id: int = payload.get("id")
    user_type: str = payload.get("type")
    jti: str = payload.get("jti")
    exp: int = payload.get("exp")

    # 3. Raise an error if the information contained in the JWT is not valid
    if not all([username, user_id, user_type, jti, exp]):
        logger.error("The information contained in the provided JWT is not valid. The signature of the JWT is valid.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user.")

    # 4. Check if jti (unique token identifier) is in the DB and active, raise an error if the information is invalid
    session_token = db.query(SessionTokens).filter_by(jti=jti).first()
    if not session_token or not session_token.is_active:
        logger.error("The JTI provided in the JWT token does not correspond to any active session_token.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user.")

    # 5. Check if the JWT token is expired
    if session_token.expires_at < datetime.utcnow():
        # Remove the JWT token from the DB if it is expired
        db.delete(session_token)
        db.commit()

        # Raise an error if the JWT token is expired
        logger.error("The JWT token has expired.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user.")

    # 6. Check if user activated (if the email address of the user has been validated)
    db_user = db.query(Users).filter(Users.id == user_id).first()

    # 7. Raise error if the user is not in the database
    if not db_user:
        logger.error("The user ID provided in the JWT does not correspond to any user ID in the database.")
        raise HTTPException(status_code=403, detail="Invalid user.")

    # 8. Raise an error if the users' email address has not been validated and inform the user with a non-generic error
    if not db_user.activated:
        logger.error("The user trying to login did not yet validate the email address and set a password.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please validate your email address first."
        )
    
    # 9. Check if there are less than 5 minutes remaining for the token and refresh the Token if it is the case
    time_left = (session_token.expires_at - datetime.utcnow()).total_seconds()
    if time_left < 300:  # 5 minutes = 300 seconds

        # 10. Generate a new expiration time (extend to new 20 minutes) and a new jti
        new_exp = datetime.utcnow() + timedelta(minutes=AUTHENTICATION_TIME)
        new_jti = str(uuid.uuid4())

        # 11. Update the token in the Database with a new session record with the new expiration and a new jti.
        session_token.jti = new_jti
        session_token.expires_at = new_exp
        db.commit()

        # 12. Create a new token payload and encode it.
        new_token_payload = {
            "sub": username,
            "id": user_id,
            "type": user_type,
            "jti": new_jti,
            "exp": new_exp
        }
        new_jwt = jwt.encode(new_token_payload, SECRET_KEY, algorithm=ALGORITHM)
        
        # 13. Attach the new token to the response so the client can use it.
        if response is not None:
            response.headers["X-Refresh-Token"] = new_jwt

        # 14. Update the jti variable to reflect the new token.
        jti = new_jti

    # 15. return the user information to the calling function
    return {"username": username, "id": user_id, "type": user_type, "jti": jti}

# Check if the provided login/password combination is valid
def authenticate_user(
    username: str, 
    password: str, 
    db
):
    """
    Function that allows to check if the provided login information is valid.
    """

    # 1. Query the database to retrieve user information
    user = db.query(Users).filter(Users.username == username).first()
    
    # 2. If the user does not exist => reurn false
    if not user:
        return False

    # 2. If the provided user password is incorrect => reurn false
    if not bcrypt_context.verify(password, user.hashedPassword):
        return False

    # 3. return the user if the provided login/password combination is valid
    return user



# ========================================================
# API Routes
# ========================================================

# Validate newly created user email => GET /auth/validate_email/{token}
@router.post("/validate_email/{token}", status_code=status.HTTP_200_OK)
async def validate_email(
    token: str,
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Validate the user's email and allow them to set their password during the process.
    """

    # 1. If passwords do not match => raise error
    if password != confirm_password:
        logger.error("Provided passwords do not match.")
        raise HTTPException(status_code=403, detail="Passwords do not match.")

    # 2. Enforce password policy
    try:
        validate_password_policy(password)
    except ValueError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )

    # 3. Retrieve validation token
    validation_record = db.query(ValidationTokens).filter_by(token=token).first()
    if not validation_record:
        logger.error("The validation token is invalid.")
        raise HTTPException(status_code=403, detail="Invalid validation token.")

    if validation_record.expires_at < datetime.utcnow():
        logger.error("The validation token has expired.")
        raise HTTPException(status_code=403, detail="Validation token has expired.")

    # 4. Retrieve user
    db_user = db.query(Users).filter(Users.id == validation_record.user_id).first()
    if not db_user:
        logger.error("The user associated to the validation token record cannot be found.")
        raise HTTPException(status_code=403, detail="User not found.")

    # 5. Activate user and set password
    db_user.activated = True
    db_user.hashedPassword = bcrypt_context.hash(password)

    # 6. Cleanup token
    db.delete(validation_record)
    db.commit()
    db.refresh(db_user)

    logger.info(f'Email validated and password set successfully for user with id {validation_record.user_id}.')
    return {"detail": "Email validated and password set successfully. You may now log in."}

# Change the user password => POST /auth/change_password
@router.post("/change_password", status_code=status.HTTP_200_OK)
async def change_password(
    data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allows a logged-in user to change their password, requiring new_password and confirm_password.
    If they match, re-hash and update the user's password in DB.
    """

    # 1. Check if new_password matches confirm_password
    if data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=403,
            detail="New password and confirm password do not match."
        )

    # 2. Fetch the user from DB
    db_user = db.query(Users).filter(Users.id == current_user["id"]).first()
    
    # 3. If the user was not found in the database, throw an error
    if not db_user:
        logger.error(f'User {current_user["username"]} does not exist.')
        raise HTTPException(status_code=403, detail="User not found.")

    # 4. Check if old password is correct
    if not bcrypt_context.verify(data.old_password, db_user.hashedPassword):
        logger.error(f'The old password provided for the user {current_user["username"]} is incorrect.')
        raise HTTPException(status_code=403, detail="Old password is incorrect.")

    # 5. Check if the new password is the same as the old password
    if data.old_password == data.new_password:
        logger.error(f'The new password must be different from the old password provided for the user {current_user["username"]}.')
        raise HTTPException(status_code=403, detail="New password must be different from the old password.")

    # 6. Enforce the password policy on the new password.
    try:
        validate_password_policy(data.new_password)
    except ValueError as e:
        logger.error(f'The new password policy is not respected for the provided password for the user {current_user["username"]}.')
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )

    # 7. Hash the new password and update the database with the new password of the user
    db_user.hashedPassword = bcrypt_context.hash(data.new_password)
    db.commit()
    db.refresh(db_user)

    # 8. return an explicit message that the password change has been successful for the user
    logger.info(f'Password modified successfully for user {current_user["username"]}.')
    return {"detail": "Password changed successfully."}

# Create access token route => POST /auth/token
@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: Session = Depends(get_db)
):
    """
    Function allowing to authenticate a user and to generate a JWT for the user that will be used to verify the authentication of the user.
    """

    # 1. Get user IP address
    client_ip = request.headers.get('X-Forwarded-For')
    if client_ip:
        client_ip = client_ip.split(',')[0].strip()
    else:
        client_ip = request.client.host

    # 2. Return the user information if the provided login/user information is valid
    user = authenticate_user(form_data.username, form_data.password, db)

    # 3. If the provided login/user information is not valid => Throw a non-generic error
    if not user:
        login_logger.warning(f"FAILED login attempt for username: {form_data.username} from IP: {client_ip}")
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")
    
    # 4. If the user is valid create a JWT for the user
    access_token = create_access_token(
        user.username, 
        user.id, 
        user.userType,
        timedelta(minutes=AUTHENTICATION_TIME), 
        db
    )
    
    # 5. Log the successful login attempt
    login_logger.info(f"SUCCESSFUL login for username: {user.username} (user_id: {user.id}) from IP: {client_ip}")

    # 6. return the JWT access token to the user
    return {"access_token": access_token, "token_type": "bearer"}

# Logout a user => POST /auth/logout  
@router.post("/logout")
async def logout(
    request: Request,
    user: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Function allowing to logout a user and to remove the JWT for the logged-out user.
    """

    # 1. Get user IP address
    client_ip = request.headers.get('X-Forwarded-For')
    if client_ip:
        client_ip = client_ip.split(',')[0].strip()
    else:
        client_ip = request.client.host

    # 2. Retrieve the unique identifier for the provided JWT
    jti = user["jti"]

    # 3. Retrieve the session token with the specified unique identifier from the Database
    session_token = db.query(SessionTokens).filter_by(jti=jti).first()

    # 4. Return an error if the JWT has not been found in the Database
    if not session_token:
        logger.error("The JWT token provided in the request does not have an associated session_token record.")
        raise HTTPException(status_code=403, detail="Token not found.")
    
    # 5. Remove the JWT token from the DB if it is expired
    db.delete(session_token)
    db.commit()

    # 6. Log the successful logout of the user
    login_logger.info(f"SUCCESSFUL logout for username: {user['username']} (user_id: {user['id']}) from IP: {client_ip}")

    # 7. return a message specifying that the user has been logged out
    return {"detail": "Successfully logged out."}

# Delete a user account => DELETE /auth/account_delete
@router.delete("/account_delete", status_code=status.HTTP_200_OK)
async def delete_account(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Function allowing to delete an existing user, also removing all the existing Session, Validation and PasswordReset Tokens.
    """

    # 1. Get the user id from the provided user JWT
    user_id = current_user["id"]

    # 2. Query the database in order to find the user that is going to be removed
    db_user = db.query(Users).filter(Users.id == user_id).first()

    # 3. Raise an error if the user has not been found in the database
    if not db_user:
        logger.error(f'The user {current_user["username"]} cannot be found in the database.')
        raise HTTPException(status_code=403, detail="User not found.")

    # 4. Remove session tokens manually
    db.query(SessionTokens).filter_by(user_id=user_id).delete()
    db.commit()

    # 5. Remove validation tokens manually
    db.query(ValidationTokens).filter_by(user_id=user_id).delete()
    db.commit()

    # 6. Remove password reset tokens manually
    db.query(PasswordResetTokens).filter_by(user_id=user_id).delete()
    db.commit()

    # 7. Wrap the DB delete in a store_context so imageattach can cleanly remove files (profile image removal)
    with store_context(store):
        db.delete(db_user)
        db.commit()

    # 8. return a message specifying that the user has been deleted successfully
    logger.info(f'The user {current_user["username"]} has been successfully deleted.')
    return {"detail": "Account deleted successfully."}

# Forgot password route => POST /auth/forgot_password
@router.post("/forgot_password", status_code=status.HTTP_200_OK)
async def forgot_password(
    email: EmailStr = Form(...),
    db: Session = Depends(get_db)
):
    """
    Request a password reset.
    This endpoint accepts an email address, and if a user with that email exists,
    generates a time-limited password reset token and sends a reset link via email.
    For security reasons, the response does not reveal whether the email exists.
    """

    # 1. Find the user associated to the specified email address
    user = db.query(Users).filter(Users.username == email).first()
    
    # 2. If the user exists
    if user:
        # Create a password reset token
        reset_token = create_password_reset_token(db, user.id)

        # Send the password reset token to the user
        reset_link = f"http://{BACKEND_URL}/auth/reset_password/{reset_token}"
        send_password_reset_email(user.username, reset_link)
        logger.info(f'Password reset token has been sent to the user {user.username}.')
    else:
        logger.error(f'The user {user.username} does not exist, the password reset link has not been sent.')
    
    # 3. Always return the same generic message to avoid user enumeration
    return {"detail": "If an account with that email exists, a password reset link has been sent."}

# Reset password route => POST /auth/reset_password
@router.post("/reset_password", status_code=status.HTTP_200_OK)
async def reset_password(
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Reset the user's password using the provided token.
    Validates that the token exists, is not expired or already used, and that the new passwords match.
    """

    # 1. If the new_password does not match the confirm_password => throw a non-generic error
    if new_password != confirm_password:
        logger.error("The provided passwords do not match")
        raise HTTPException(status_code=403, detail="Passwords do not match.")

    # 2. Query the database to retrieve the reset_record with the provided password reset token
    reset_record = db.query(PasswordResetTokens).filter_by(token=token).first()

    # 3. If the password reset token does not exist in the Database => throw a non-generic error
    if not reset_record:
        logger.error("The provided password_reset token does not exist in the database.")
        raise HTTPException(status_code=403, detail="Invalid password reset token.")

    # 4. If the password reset token is expired => throw a non-generic error
    if reset_record.expires_at < datetime.utcnow():
        logger.error("The provided password_reset token has expired.")
        raise HTTPException(status_code=403, detail="Password reset token has expired.")

    # 5. Enforce the password policy on the new password.
    try:
        validate_password_policy(new_password)
    except ValueError as e:
        logger.error("The provided passwords do not respect the enforced password policy.")
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )

    # 6. Query the database to retrieve the user associated with the provided password reset token
    user = db.query(Users).filter(Users.id == reset_record.user_id).first()

    # 7. If the user associated with the provided password reset token is not found => throw a non-generic error
    if not user:
        logger.error("The user associated with the provided password reset token cannot be found in the database.")
        raise HTTPException(status_code=403, detail="User not found.")

    # 8. Update the user's password and remove the password reset token entry from the database
    user.hashedPassword = bcrypt_context.hash(new_password)
    db.delete(reset_record)
    db.commit()

    # 9. Return a meessage specifying that the users' password has been successfully reset
    logger.info(f'The password of the user with the ID = {reset_record.user_id} has successfully been reset.')
    return {"detail": "Password has been reset successfully."}