from fastapi import APIRouter, HTTPException, status, Depends
from database import db_manager
from models import OrganizationCreate, OrganizationUpdate, OrganizationDelete, TokenData
from auth import auth_utils
from dependencies import get_current_admin
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/org", tags=["Organization"])


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_organization(org_data: OrganizationCreate):
    """Create new organization with admin user and dedicated collection"""
    # Check if organization already exists
    existing_org = db_manager.master_db.organizations.find_one(
        {"organization_name": org_data.organization_name}
    )
    
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization '{org_data.organization_name}' already exists"
        )
    
    # Check if admin email already exists
    existing_admin = db_manager.master_db.admins.find_one(
        {"email": org_data.email}
    )
    
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Admin with email '{org_data.email}' already exists"
        )
    
    # Create organization collection
    collection_name = db_manager.create_organization_collection(org_data.organization_name)
    
    # Create organization record
    org_id = ObjectId()
    
    # Hash password and create admin user
    hashed_password = auth_utils.hash_password(org_data.password)
    admin_id = ObjectId()
    
    # Create admin user document
    admin_user_doc = {
        "_id": admin_id,
        "email": org_data.email,
        "hashed_password": hashed_password,
        "organization_id": org_id,
        "created_at": datetime.utcnow()
    }
    
    # Create organization document
    org_doc = {
        "_id": org_id,
        "organization_name": org_data.organization_name,
        "collection_name": collection_name,
        "admin_email": org_data.email,
        "admin_id": admin_id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Insert into master database
    db_manager.master_db.admins.insert_one(admin_user_doc)
    db_manager.master_db.organizations.insert_one(org_doc)
    
    return {
        "message": "Organization created successfully",
        "organization_id": str(org_id),
        "organization_name": org_data.organization_name,
        "collection_name": collection_name,
        "admin_email": org_data.email,
        "admin_id": str(admin_id)
    }


@router.get("/get")
async def get_organization(organization_name: str):
    """Get organization details by name"""
    organization = db_manager.master_db.organizations.find_one(
        {"organization_name": organization_name}
    )
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization '{organization_name}' not found"
        )
    
    # Convert ObjectId to string for JSON serialization
    organization["_id"] = str(organization["_id"])
    if organization.get("admin_id"):
        organization["admin_id"] = str(organization["admin_id"])
    
    return {
        "organization": organization
    }


@router.put("/update")
async def update_organization(org_data: OrganizationUpdate):
    """Update organization name with data migration to new collection"""
    # Find existing organization by admin email
    admin = db_manager.master_db.admins.find_one({"email": org_data.email})
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found"
        )
    
    # Verify password
    if not auth_utils.verify_password(org_data.password, admin["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Get current organization
    current_org = db_manager.master_db.organizations.find_one(
        {"admin_id": admin["_id"]}
    )
    
    if not current_org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check if new organization name already exists (and it's not the same org)
    if current_org["organization_name"] != org_data.organization_name:
        existing_org = db_manager.master_db.organizations.find_one(
            {"organization_name": org_data.organization_name}
        )
        
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization '{org_data.organization_name}' already exists"
            )
        
        # Create new collection
        new_collection_name = db_manager.create_organization_collection(org_data.organization_name)
        old_collection_name = current_org["collection_name"]
        
        # Migrate data from old collection to new collection
        old_collection = db_manager.master_db[old_collection_name]
        new_collection = db_manager.master_db[new_collection_name]
        
        # Copy all documents
        documents = list(old_collection.find())
        if documents:
            new_collection.insert_many(documents)
        
        # Update organization metadata
        db_manager.master_db.organizations.update_one(
            {"_id": current_org["_id"]},
            {
                "$set": {
                    "organization_name": org_data.organization_name,
                    "collection_name": new_collection_name,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Delete old collection
        db_manager.delete_organization_collection(old_collection_name)
        
        return {
            "message": "Organization updated successfully",
            "organization_id": str(current_org["_id"]),
            "old_name": current_org["organization_name"],
            "new_name": org_data.organization_name,
            "old_collection": old_collection_name,
            "new_collection": new_collection_name,
            "documents_migrated": len(documents) if documents else 0
        }
    
    return {
        "message": "No changes needed",
        "organization_name": current_org["organization_name"]
    }


@router.delete("/delete")
async def delete_organization(
    org_data: OrganizationDelete,
    current_admin: TokenData = Depends(get_current_admin)
):
    """Delete organization (requires JWT authentication)"""
    # Get organization
    organization = db_manager.master_db.organizations.find_one(
        {"organization_name": org_data.organization_name}
    )
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization '{org_data.organization_name}' not found"
        )
    
    # Verify that current admin owns this organization
    if str(organization["_id"]) != current_admin.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this organization"
        )
    
    # Delete organization collection
    collection_name = organization["collection_name"]
    db_manager.delete_organization_collection(collection_name)
    
    # Delete admin user
    db_manager.master_db.admins.delete_one({"_id": ObjectId(current_admin.admin_id)})
    
    # Delete organization
    db_manager.master_db.organizations.delete_one({"_id": organization["_id"]})
    
    return {
        "message": "Organization deleted successfully",
        "organization_name": org_data.organization_name,
        "collection_deleted": collection_name
    }
