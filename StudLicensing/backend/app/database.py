import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import find_dotenv

# Load .env variables
dotenv_path = find_dotenv()
if not dotenv_path:
    raise FileNotFoundError("'.env' file not found. Please make sure the file exists in the project directory.")

# Retrieve environment variables.
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')

# Check that all required variables are set; if any is missing, raise an error.
if POSTGRES_USER is None:
    raise ValueError("Environment variable 'POSTGRES_USER' is not defined. Please add it to your .env file.")
if POSTGRES_PASSWORD is None:
    raise ValueError("Environment variable 'POSTGRES_PASSWORD' is not defined. Please add it to your .env file.")
if POSTGRES_DB is None:
    raise ValueError("Environment variable 'POSTGRES_DB' is not defined. Please add it to your .env file.")
if POSTGRES_PORT is None:
    raise ValueError("Environment variable 'POSTGRES_PORT' is not defined. Please add it to your .env file.")

# Postgres Connection
# Construct the SQLAlchemy database URL.
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:{POSTGRES_PORT}/{POSTGRES_DB}"
)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Session Management
SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

Base= declarative_base()