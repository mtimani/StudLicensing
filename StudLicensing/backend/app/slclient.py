# ===========================================
# Imports
# ===========================================
from fastapi import APIRouter, Depends, HTTPException, status, Form
from pydantic import BaseModel, Field
from typing import Annotated, Optional
from database import SessionLocal
from sqlalchemy.orm import Session
from logger import logger
from auth import get_current_user
from models import SLClient, Users, UserTypeEnum



# ===========================================
# SLClient router declaration
# ===========================================
router = APIRouter(
    prefix="/slclient",
    tags=["slclient"]
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
# Classes definition for SLClient operations
# ===========================================

# SLClientCreateModel class for creating a new SLClient
class SLClientCreateModel(BaseModel):
    companyName: str = Field(..., min_length=3, max_length=100)

    @classmethod
    def as_form(cls, companyName: str = Form(...)):
        return cls(companyName=companyName)

# SLClientUpdateModel class for updating an existing SLClient
class SLClientUpdateModel(BaseModel):
    companyName: Optional[str] = Field(None, min_length=3, max_length=100)

    @classmethod
    def as_form(cls, companyName: Optional[str] = Form(None)):
        return cls(companyName=companyName)



# ===========================================
# API Routes
# ===========================================

# Create SLClient => POST /slclient/create
@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_slclient(
    client_data: Annotated[SLClientCreateModel, Depends(SLClientCreateModel.as_form)],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new SLClient. Only accessible by SLAdmin users.
    """
    # 1. Check that the user is an SLAdmin
    if current_user["type"] != UserTypeEnum.sladmin:
        logger.error("Only SLAdmin users can create SLClients.")
        raise HTTPException(
            status_code=403, 
            detail="Error creating client."
        )

    # 2. Create and add the new SLClient to the database
    new_client = SLClient(companyName=client_data.companyName)
    db.add(new_client)
    db.commit()
    db.refresh(new_client)

    # 3. Return the result
    logger.info(f"SLClient created successfully with company name: {new_client.companyName}")
    return {"detail": "SLClient created successfully", "company": new_client.companyName}


# Delete SLClient => DELETE /slclient/delete/{client_id}
@router.delete("/delete/{client_id}", status_code=status.HTTP_200_OK)
def delete_slclient(
    client_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an existing SLClient by ID. Only accessible by SLAdmin users.
    """
    # 1. Check that the user is an SLAdmin
    if current_user["type"] != UserTypeEnum.sladmin:
        logger.error("Only SLAdmin users can delete SLClients.")
        raise HTTPException(
            status_code=403, 
            detail="Error deleting client."
        )

    # 2. Find the SLClient in the database
    client = db.query(SLClient).filter(SLClient.id == client_id).first()
    if not client:
        logger.error(f"SLClients {client_id} does not exist.")
        raise HTTPException(
            status_code=403,
            detail="Error deleting client."
        )

    # 3. Delete the SLClient
    db.delete(client)
    db.commit()

    # 4. Return the result
    logger.info(f"SLClient {client.companyName} deleted successfully.")
    return {"detail": "SLClient deleted successfully"}


# Update SLClient => PUT /slclient/update/{client_id}
@router.put("/update/{client_id}", status_code=status.HTTP_200_OK)
def update_slclient(
    client_id: int,
    client_data: Annotated[SLClientUpdateModel, Depends(SLClientUpdateModel.as_form)],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing SLClient by ID.
    Accessible by SLAdmin or SLClientAdmin of the same client.
    """
    # 1. Retrieve the client from the DB
    client = db.query(SLClient).filter(SLClient.id == client_id).first()
    if not client:
        logger.error(f"SLClients {client_id} does not exist.")
        raise HTTPException(
            status_code=403, 
            detail="Error modifying client."
        )

    # 2. Check if current user is authorized to update this client
    if current_user["type"] == UserTypeEnum.sladmin:
        pass  # always allowed
    elif current_user["type"] == UserTypeEnum.slclientadmin:
        # 3. Verify that the SLClientAdmin is from the same company
        user = db.query(Users).filter(Users.id == current_user["id"]).first()
        if not user or getattr(user, "company_id", None) != client_id:
            logger.error(f"User {current_user['name']} of type {current_user['type']} tried to modify SLClient {client_id} from another company.")
            raise HTTPException(
                status_code=403, 
                detail="Error modifying client."
            )
    else:
        logger.error(f'User {current_user["username"]} of type {current_user["type"]} tried to update the SLClient {client_id}.')
        raise HTTPException(
            status_code=403, 
            detail="Error modifying client."
        )

    # 4. Apply updates
    if client_data.companyName is not None:
        client.companyName = client_data.companyName

    # 5. Commit the changes to the DB
    db.commit()
    db.refresh(client)

    # 6. Return the result
    logger.info(f"SLClient {client.id} updated successfully with new company name: {client.companyName}")
    return {"detail": "SLClient updated successfully", "id": client.id, "companyName": client.companyName}