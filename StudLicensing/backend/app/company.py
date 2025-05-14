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
    Create a new Company. Only accessible by Admin users.
    """
    # 1. Check that the user is an Admin
    if current_user["type"] != UserTypeEnum.admin:
        logger.error("Only Admin users can create Companies.")
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
    Delete an existing Company by ID. Only accessible by Admin users.
    """
    # 1. Check that the user is an Admin
    if current_user["type"] != UserTypeEnum.admin:
        logger.error("Only Admin users can delete Companies.")
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
    Accessible by Admin or CompanyAdmin of the same client.
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

# Search for a Company => POST /company/search
@router.post("/search")
def search_company(
    current_user: dict = Depends(get_current_user),
    company_name: Optional[str] = Form(None),
    company_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Search for a Company by name or ID (mutually exclusive).
    Only one of company_name or company_id should be provided.
    If neither is provided, return all companies.
    """

    # 1. Ensure that either company_name or company_id is provided, but not both
    if company_name and company_id:
        logger.error("Both company_name and company_id cannot be provided.")
        raise HTTPException(
            status_code=403, 
            detail="Provide either company_name or company_id, not both."
        )

    # 2. Check if the user performing the request is an admin
    if current_user["type"] != UserTypeEnum.admin:
        logger.error(f'The user {current_user["username"]} with id = {current_user["id"]} of type {current_user["type"]} tried to perform a company search.')
        raise HTTPException(
            status_code=403, 
            detail="Search request forbidden"
        )

    # 3. Initialize the query
    query = db.query(Company)
    
    # 4. Search by company_name if provided
    if company_name:
        query = query.filter(Company.companyName.ilike(f"%{company_name}%"))
    
    # 5. Search by company_id if provided
    if company_id is not None:
        if company_id == 0:
            logger.error(f'User {current_user["username"]} with id = {current_user["id"]} has requested a company that does not exist.')
            raise HTTPException(status_code=403, detail="No companies found.")
        query = query.filter(Company.id == company_id)

    # 6. If neither company_name nor company_id is provided, return all companies
    if not company_name and not company_id:
        companies = query.all()
        logger.info(f'User {current_user["username"]} with id = {current_user["id"]} requested the return of all companies.')
        return {"companies": [{"company_id": company.id, "company_name": company.companyName} for company in companies]}

    # 7. Execute the query and get the first result (if searching by company_name or company_id)
    companies = query.all()
    
    # 8. If no company is found, raise an HTTP exception
    if not companies:
        logger.error(f'User {current_user["username"]} with id = {current_user["id"]} has requested a company that does not exist.')
        raise HTTPException(status_code=403, detail="No companies found.")
    
    # 9. Return the company details
    logger.info(f"Found {len(companies)} companies matching the search criteria.")
    return {"companies": [{"company_id": company.id, "company_name": company.companyName} for company in companies]}