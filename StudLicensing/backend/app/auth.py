import os
import smtplib
import uuid
from datetime import timedelta, datetime
from typing import Annotated, Optional
from sqlalchemy_imageattach.entity import store_context
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, EmailStr, ValidationError
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import Users, UserPicture, SessionTokens, ValidationTokens, PasswordResetTokens, store
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from dotenv import find_dotenv
from PIL import Image
from io import BytesIO
from email.message import EmailMessage

# Load .env variables
dotenv_path = find_dotenv()
if not dotenv_path:
    raise FileNotFoundError("'.env' file not found. Please make sure the file exists in the project directory.")

# Login Route
router = APIRouter (
    prefix='/auth',
    tags=['auth']
)

# Retrieve environment variables.
SECRET_KEY = os.getenv('SECRET_KEY')
BACKEND_URL = os.getenv('BACKEND_URL', 'localhost:8000')
ALGORITHM = "HS256"

# Check that all required variables are set; if any is missing, raise an error.
if SECRET_KEY is None:
    raise ValueError("Environment variable 'SECRET_KEY' is not defined. Please add it to your .env file.")
if BACKEND_URL is None:
    raise ValueError("Environment variable 'BACKEND_URL' is not defined. Please add it to your .env file.")

# Create JWT context
bcrypt_context = CryptContext(schemes = ['bcrypt'], deprecated = 'auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl = 'auth/token')

# User creation parameters
class CreateUserRequest(BaseModel):
    username: EmailStr
    name: str
    surname: str
    password: str

# Change password parameters
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str

# Token creation parameters
class Token(BaseModel):
    access_token: str
    token_type: str

# Get Database connection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# Send validation email
def send_validation_email(to_email: str, validation_link: str) -> None:
    """
    Send an email to the specified address with the given validation link.
    SMTP configuration is loaded from environment variables.
    """
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = os.getenv('SMTP_PORT')
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    FROM_EMAIL = os.getenv('FROM_EMAIL')

    # Check that all necessary configuration variables are provided.
    missing = [var for var in ['SMTP_SERVER', 'SMTP_PORT', 'SMTP_USERNAME', 'SMTP_PASSWORD', 'FROM_EMAIL']
               if os.getenv(var) is None]
    if missing:
        raise ValueError(f"Missing SMTP configuration for: {', '.join(missing)}")

    # Create the email message.
    msg = EmailMessage()
    msg['Subject'] = "[StudLicensing] Validate Your Email Address"
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    msg.set_content(
        f"Hello,\n\n"
        f"Please click the link below to validate your email address:\n\n"
        f"{validation_link}\n\n"
        f"This link will expire in 24 hours.\n\n"
        f"Thank you!"
    )

    # Connect to the SMTP server and send the email.
    try:
        with smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT)) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"Validation email successfully sent to {to_email}")
    except Exception as e:
        print(f"Error sending validation email to {to_email}: {e}")

# Create email validation token
def create_validation_token(db: Session, user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    expires_delta = expires_delta or timedelta(hours=24)
    expire_time = datetime.utcnow() + expires_delta
    token_str = str(uuid.uuid4())  # a unique token string; you can also choose to use jwt here if desired.
    validation_record = ValidationTokens(
        token=token_str,
        user_id=user_id,
        expires_at=expire_time
    )
    db.add(validation_record)
    db.commit()
    db.refresh(validation_record)
    return token_str

def create_password_reset_token(db: Session, user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a unique, time-limited password reset token.  
    Default expiration is set to 1 hour.
    """
    expires_delta = expires_delta or timedelta(hours=1)
    expire_time = datetime.utcnow() + expires_delta
    token_str = str(uuid.uuid4())
    
    reset_record = PasswordResetTokens(
        token=token_str,
        user_id=user_id,
        expires_at=expire_time
    )
    db.add(reset_record)
    db.commit()
    db.refresh(reset_record)
    return token_str

def send_password_reset_email(to_email: str, reset_link: str) -> None:
    """
    Send a password reset email to the user with the provided reset link.
    """
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = os.getenv('SMTP_PORT')
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    FROM_EMAIL = os.getenv('FROM_EMAIL')
    
    missing = [var for var in ['SMTP_SERVER', 'SMTP_PORT', 'SMTP_USERNAME', 'SMTP_PASSWORD', 'FROM_EMAIL']
               if os.getenv(var) is None]
    if missing:
        raise ValueError(f"Missing SMTP configuration for: {', '.join(missing)}")
    
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
    
    try:
        with smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT)) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"Password reset email successfully sent to {to_email}")
    except Exception as e:
        print(f"Error sending password reset email to {to_email}: {e}")

# Get current user
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)], db: Session = Depends(get_db), response: Response = None):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user.")

    username: str = payload.get("sub")
    user_id: int = payload.get("id")
    jti: str = payload.get("jti")
    exp: int = payload.get("exp")

    if not all([username, user_id, jti, exp]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user.")

    # Check if jti is in DB and active
    session_token = db.query(SessionTokens).filter_by(jti=jti).first()
    if not session_token or not session_token.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user.")

    if session_token.expires_at < datetime.utcnow():
        # Mark DB record as inactive if you wish
        session_token.is_active = False
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user.")

    # Check if user activated
    db_user = db.query(Users).filter(Users.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Invalid user.")

    if not db_user.activated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please validate your email address first."
        )
    
    # Check if there are less than 5 minutes remaining for the token.
    time_left = (session_token.expires_at - datetime.utcnow()).total_seconds()
    if time_left < 300:  # 5 minutes = 300 seconds
        new_exp = datetime.utcnow() + timedelta(minutes=20)
        new_jti = str(uuid.uuid4())

        # Update the token session record with the new expiration and new jti.
        session_token.jti = new_jti
        session_token.expires_at = new_exp
        db.commit()

        # Create a new token payload and encode it.
        new_token_payload = {
            "sub": username,
            "id": user_id,
            "jti": new_jti,
            "exp": new_exp
        }
        new_jwt = jwt.encode(new_token_payload, SECRET_KEY, algorithm=ALGORITHM)
        # Attach the new token to the response so the client can use it.
        if response is not None:
            response.headers["X-Refresh-Token"] = new_jwt

        # Update the jti variable to reflect the new token.
        jti = new_jti

    return {"username": username, "id": user_id, "jti": jti}

# Route to create user
@router.post("/account_create", status_code=status.HTTP_201_CREATED)
async def create_user(    
    username: str = Form(...),
    name: str = Form(...),
    surname: str = Form(...),
    password: str = Form(...),
    profilePicture: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    # Create a new user instance and validate the input using Pydantic.
    try:
        validated_data = CreateUserRequest(
            username=username,
            name=name,
            surname=surname,
            password=password
        )
    except ValidationError as ve:
        raise RequestValidationError(ve.errors())
    
    # Now create an instance of the SQLAlchemy Users model with validated data.
    new_user = Users(
        username=validated_data.username,
        name=validated_data.name,
        surname=validated_data.surname,
        hashedPassword=bcrypt_context.hash(validated_data.password),
        creationDate=datetime.utcnow().date(),
        activated=False
    )

    # Process the profile picture if provided.
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
        
        # Create UserPicture instance (assuming your models support it).
        user_picture = UserPicture()
        user_picture.file = BytesIO(file_data)
        user_picture.mimetype = mimetype
        user_picture.width = width
        user_picture.height = height
        user_picture.store = store
        new_user.profilePicture = [user_picture]

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create a validation token and store it in the DB.
    validation_token_str = create_validation_token(db, new_user.id)
    validation_link = f"http://{BACKEND_URL}/auth/validate_email/{validation_token_str}"
    send_validation_email(new_user.username, validation_link)

    return {"id": new_user.id, "username": new_user.username}

# Endpoint to validate the account via the token.
@router.get("/validate_email/{token}", status_code=status.HTTP_200_OK)
async def validate_email(token: str, db: Session = Depends(get_db)):
    validation_record = db.query(ValidationTokens).filter_by(token=token).first()
    if not validation_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid validation token.")

    if validation_record.is_used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This validation token has already been used.")

    if validation_record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Validation token has expired.")

    # Mark the user as activated
    db_user = db.query(Users).filter(Users.id == validation_record.user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    db_user.activated = True
    # Mark token as used
    validation_record.is_used = True
    db.commit()
    db.refresh(db_user)
    return {"detail": "Email validated successfully. You may now log in."}

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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match."
        )

    # 2. Fetch the user from DB
    db_user = db.query(Users).filter(Users.id == current_user["id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")

    # 3. Check if old password is correct
    if not bcrypt_context.verify(data.old_password, db_user.hashedPassword):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect.")

    # 4. Check if the new password is the same as the old password
    if data.old_password == data.new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different from the old password.")

    # 5. Hash the new password and update
    db_user.hashedPassword = bcrypt_context.hash(data.new_password)
    db.commit()
    db.refresh(db_user)

    return {"detail": "Password changed successfully."}

# Route to create user
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")
    
    access_token = create_access_token(
        user.username, 
        user.id, 
        timedelta(minutes=20), 
        db
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashedPassword):
        return False
    return user

def revoke_token(jti: str, exp_timestamp: float):
    """
    Put the jti in a store until it expires.
    For demo, we'll just store it in memory with its expiry time.
    """
    REVOKED_TOKENS.add(jti)

def create_access_token(username: str, user_id: int, expires_delta: timedelta, db: Session):
    # Unique token per JWT => to facilitate revocation (for logout purposes)
    jti = str(uuid.uuid4())
    expire_time = datetime.utcnow() + expires_delta
    
    # Insert into DB
    session_token = SessionTokens(
        jti=jti,
        user_id=user_id,
        expires_at=expire_time
    )
    db.add(session_token)
    db.commit()
    db.refresh(session_token)
    
    # Create JWT
    to_encode = {
        "sub": username,
        "id": user_id,
        "jti": jti,
        "exp": expire_time
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
    
@router.post("/logout")
async def logout(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    jti = user["jti"]
    session_token = db.query(SessionTokens).filter_by(jti=jti).first()
    if not session_token:
        raise HTTPException(status_code=400, detail="Token not found.")
    
    # Mark it inactive
    session_token.is_active = False
    db.commit()
    return {"detail": "Successfully logged out."}

@router.delete("/account_delete", status_code=status.HTTP_200_OK)
async def delete_account(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["id"]

    # Query the user
    db_user = db.query(Users).filter(Users.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Remove session tokens manually
    db.query(SessionTokens).filter_by(user_id=user_id).delete()
    db.commit()

    # Remove validation tokens manually
    db.query(ValidationTokens).filter_by(user_id=user_id).delete()
    db.commit()

    # Remove password reset tokens manually
    db.query(PasswordResetTokens).filter_by(user_id=user_id).delete()
    db.commit()

    # Wrap the DB delete in a store_context so imageattach can cleanly remove files
    with store_context(store):
        db.delete(db_user)
        db.commit()

    return {"detail": "Account deleted successfully."}

@router.post("/forgot_password", status_code=status.HTTP_200_OK)
async def forgot_password(email: EmailStr = Form(...), db: Session = Depends(get_db)):
    """
    Request a password reset.
    This endpoint accepts an email address, and if a user with that email exists,
    generates a time-limited password reset token and sends a reset link via email.
    For security reasons, the response does not reveal whether the email exists.
    """
    user = db.query(Users).filter(Users.username == email).first()
    if user:
        reset_token = create_password_reset_token(db, user.id)
        reset_link = f"http://{BACKEND_URL}/auth/reset_password/{reset_token}"
        send_password_reset_email(user.username, reset_link)
    # Always return the same generic message to avoid user enumeration.
    return {"detail": "If an account with that email exists, a password reset link has been sent."}

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
    if new_password != confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match.")

    reset_record = db.query(PasswordResetTokens).filter_by(token=token).first()
    if not reset_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password reset token.")

    if reset_record.is_used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password reset token has already been used.")

    if reset_record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password reset token has expired.")

    user = db.query(Users).filter(Users.id == reset_record.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # Update the user's password.
    user.hashedPassword = bcrypt_context.hash(new_password)
    reset_record.is_used = True
    db.commit()
    return {"detail": "Password has been reset successfully."}