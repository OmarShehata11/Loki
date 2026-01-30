"""
Signature management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import yaml

from ..models.database import get_db
from ..models.schemas import (
    SignatureResponse, SignatureCreate, SignatureUpdate
)
from ..models import crud

router = APIRouter(prefix="/signatures", tags=["signatures"])


@router.get("")
async def get_signatures(
    enabled_only: bool = False,
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    action: str = None,
    enabled: bool = None,
    db: AsyncSession = Depends(get_db)
):
    """Get signatures with filtering and pagination."""
    skip = (page - 1) * page_size
    
    signatures, total = await crud.get_signatures(
        db, 
        enabled_only=enabled_only,
        skip=skip,
        limit=page_size,
        search=search,
        action=action,
        enabled=enabled
    )
    
    return {
        "signatures": [
            SignatureResponse(
                id=sig.id,
                name=sig.name,
                pattern=sig.pattern,
                action=sig.action,
                description=sig.description,
                enabled=sig.enabled,
                created_at=sig.created_at,
                updated_at=sig.updated_at
            )
            for sig in signatures
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{sig_id}", response_model=SignatureResponse)
async def get_signature(
    sig_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a signature by ID."""
    signature = await crud.get_signature_by_id(db, sig_id)
    if not signature:
        raise HTTPException(status_code=404, detail="Signature not found")
    
    return SignatureResponse(
        id=signature.id,
        name=signature.name,
        pattern=signature.pattern,
        action=signature.action,
        description=signature.description,
        enabled=signature.enabled,
        created_at=signature.created_at,
        updated_at=signature.updated_at
    )


@router.post("", response_model=SignatureResponse, status_code=201)
async def create_signature(
    signature: SignatureCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new signature."""
    # Check if name already exists
    existing = await crud.get_signature_by_name(db, signature.name)
    if existing:
        raise HTTPException(status_code=400, detail="Signature name already exists")
    
    sig_data = signature.dict()
    new_sig = await crud.create_signature(db, sig_data)
    
    return SignatureResponse(
        id=new_sig.id,
        name=new_sig.name,
        pattern=new_sig.pattern,
        action=new_sig.action,
        description=new_sig.description,
        enabled=new_sig.enabled,
        created_at=new_sig.created_at,
        updated_at=new_sig.updated_at
    )


@router.put("/{sig_id}", response_model=SignatureResponse)
async def update_signature(
    sig_id: int,
    signature: SignatureUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a signature."""
    update_data = signature.dict(exclude_unset=True)
    
    # Force action to "alert" (drop removed)
    if "action" in update_data:
        update_data["action"] = "alert"
    
    # If name is being updated, check for conflicts
    if "name" in update_data:
        existing = await crud.get_signature_by_name(db, update_data["name"])
        if existing and existing.id != sig_id:
            raise HTTPException(status_code=400, detail="Signature name already exists")
    
    updated = await crud.update_signature(db, sig_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Signature not found")
    
    return SignatureResponse(
        id=updated.id,
        name=updated.name,
        pattern=updated.pattern,
        action=updated.action,
        description=updated.description,
        enabled=updated.enabled,
        created_at=updated.created_at,
        updated_at=updated.updated_at
    )


@router.delete("/{sig_id}")
async def delete_signature(
    sig_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a signature."""
    success = await crud.delete_signature(db, sig_id)
    if not success:
        raise HTTPException(status_code=404, detail="Signature not found")
    return {"message": "Signature deleted successfully"}


@router.post("/reload")
async def reload_signatures(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Reload signatures from uploaded YAML file to database.
    This syncs YAML file -> database.
    Requires a YAML file to be uploaded.
    """
    try:
        # Read uploaded file content
        content = await file.read()
        yaml_content = content.decode('utf-8')
        
        # Parse YAML
        all_rules = yaml.safe_load(yaml_content)
        signatures = all_rules.get('signatures', [])
        
        # Import signatures directly to database
        loaded_count = 0
        for sig_data in signatures:
            existing = await crud.get_signature_by_name(db, sig_data['name'])
            if existing:
                # Update existing
                await crud.update_signature(db, existing.id, {
                    'pattern': sig_data['pattern'],
                    'action': 'alert',  # Only alert now
                    'description': sig_data.get('description', ''),
                    'enabled': 1
                })
            else:
                # Create new
                await crud.create_signature(db, {
                    'name': sig_data['name'],
                    'pattern': sig_data['pattern'],
                    'action': 'alert',  # Only alert now
                    'description': sig_data.get('description', ''),
                    'enabled': 1
                })
            loaded_count += 1
        
        await db.commit()
        
        return {
            "message": f"Imported {loaded_count} signatures from uploaded YAML file",
            "count": loaded_count,
            "filename": file.filename
        }
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading signatures: {str(e)}")



