# ===========================================
# Imports
# ===========================================
from fastapi import APIRouter, Depends, HTTPException, status, Form
from pydantic import BaseModel, Field
from typing import Annotated, Optional
from app.database import SessionLocal
from sqlalchemy.orm import Session
from app.logger import logger
from app.auth import get_current_user
from app.models import Company, Users, UserTypeEnum



# ===========================================
# Company router declaration
# ===========================================
router = APIRouter(
    prefix="/company",
    tags=["company"]
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
# Classes definition for Company operations
# ===========================================

# CompanyCreateModel class for creating a new Company
class CompanyCreateModel(BaseModel):
    companyName: str = Field(..., max_length=100)

    @classmethod
    def as_form(cls, companyName: str = Form(...)):
        return cls(companyName=companyName)

# CompanyUpdateModel class for updating an existing Company
class CompanyUpdateModel(BaseModel):
    companyName: Optional[str] = Field(None, max_length=100)

    @classmethod
    def as_form(cls, companyName: Optional[str] = Form(None)):
        return cls(companyName=companyName)



# ===========================================
# API Routes
# ===========================================

# Create Company => POST /company/create
@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_company(
    client_data: Annotated[CompanyCreateModel, Depends(CompanyCreateModel.as_form)],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new Company. Only accessible by SLAdmin users.
    """
    # 1. Check that the user is an SLAdmin
    if current_user["type"] != UserTypeEnum.admin:
        logger.error("Only SLAdmin users can create Companys.")
        raise HTTPException(status_code=403, detail="Error creating client.")

    # 2. Create and add the new Company to the database
    new_client = Company(companyName=client_data.companyName)
    db.add(new_client)
    db.commit()
    db.refresh(new_client)

    # 3. Return the result
    logger.info(f"Company created successfully with company name: {new_client.companyName}")
    return {"detail": "Company created successfully", "company": new_client.companyName}


# Delete Company => DELETE /company/delete/{client_id}
@router.delete("/delete/{client_id}", status_code=status.HTTP_200_OK)
def delete_company(
    client_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an existing Company by ID. Only accessible by SLAdmin users.
    """
    # 1. Check that the user is an SLAdmin
    if current_user["type"] != UserTypeEnum.admin:
        logger.error("Only SLAdmin users can delete Companys.")
        raise HTTPException(status_code=403, detail="Error deleting client.")

    # 2. Find the Company in the database
    client = db.query(Company).filter(Company.id == client_id).first()
    if not client:
        logger.error(f"Companys {client_id} does not exist.")
        raise HTTPException(status_code=403, detail="Error deleting client.")

    # 3. Delete the Company
    db.delete(client)
    db.commit()

    # 4. Return the result
    logger.info(f"Company {client.companyName} deleted successfully.")
    return {"detail": "Company deleted successfully"}


# Update Company => PUT /company/update/{client_id}
@router.put("/update/{client_id}", status_code=status.HTTP_200_OK)
def update_company(
    client_id: int,
    client_data: Annotated[CompanyUpdateModel, Depends(CompanyUpdateModel.as_form)],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing Company by ID.
    Accessible by SLAdmin or CompanyAdmin of the same client.
    """
    # 1. Retrieve the client from the DB
    client = db.query(Company).filter(Company.id == client_id).first()
    if not client:
        logger.error(f"Companys {client_id} does not exist.")
        raise HTTPException(status_code=403, detail="Error modifying client.")

    # 2. Check if current user is authorized to update this client
    if current_user["type"] == UserTypeEnum.admin:
        pass  # always allowed
    elif current_user["type"] == UserTypeEnum.company_admin:
        # 3. Verify that the CompanyAdmin is from the same company
        user = db.query(Users).filter(Users.id == current_user["id"]).first()
        if not user or getattr(user, "company_id", None) != client_id:
            logger.error(f"User {current_user['name']} of type {current_user['type']} tried to modify Company {client_id} from another company.")
            raise HTTPException(status_code=403, detail="Error modifying client.")
    else:
        logger.error("No permission to update this Company.")
        raise HTTPException(status_code=403, detail="Error modifying client.")

    # 4. Apply updates
    if client_data.companyName is not None:
        client.companyName = client_data.companyName

    # 5. Commit the changes to the DB
    db.commit()
    db.refresh(client)

    # 6. Return the result
    logger.info(f"Company {client.id} updated successfully with new company name: {client.companyName}")
    return {"detail": "Company updated successfully", "id": client.id, "companyName": client.companyName}