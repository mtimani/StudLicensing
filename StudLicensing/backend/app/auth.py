import os
from datetime import timedelta, datetime
from typing import Annotated, Optional
from sqlalchemy_imageattach.entity import store_context
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, EmailStr, ValidationError
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import Users, UserPicture, SessionTokens, store
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from dotenv import find_dotenv
from PIL import Image
from io import BytesIO
import uuid

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
ALGORITHM = "HS256"

# Check that all required variables are set; if any is missing, raise an error.
if SECRET_KEY is None:
    raise ValueError("Environment variable 'SECRET_KEY' is not defined. Please add it to your .env file.")

# Create JWT context
bcrypt_context = CryptContext(schemes = ['bcrypt'], deprecated = 'auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl = 'auth/token')

# User creation parameters
class CreateUserRequest(BaseModel):
    username: EmailStr
    name: str
    surname: str
    password: str

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
        # activated remains False until email validation
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

    return {"id": new_user.id, "username": new_user.username}

# Route to create user
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")
    
    access_token = create_access_token(
        user.username, 
        user.id, 
        timedelta(minutes=30), 
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

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)], db: Session = Depends(get_db)):
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

    return {"username": username, "id": user_id, "jti": jti}
    
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

    # If you want to remove session tokens manually:
    db.query(SessionTokens).filter_by(user_id=user_id).delete()
    db.commit()

    # Wrap the DB delete in a store_context so imageattach can cleanly remove files
    from sqlalchemy_imageattach.entity import store_context
    with store_context(store):
        db.delete(db_user)
        db.commit()

    return {"detail": "Account deleted successfully."}