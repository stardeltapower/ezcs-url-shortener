from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import generate_api_key, get_current_api_key, hash_api_key, verify_admin_token
from app.database import get_db
from app.models import ApiKey
from app.schemas import ApiKeyCreate, ApiKeyInfo, ApiKeyListResponse, ApiKeyResponse

router = APIRouter(prefix="/api/admin/keys", tags=["Admin - API Keys"])


@router.post("/", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    api_key_data: ApiKeyCreate, db: Session = Depends(get_db), _: bool = Depends(verify_admin_token)
):
    """Create a new API key (Admin only)"""
    # Generate new API key
    new_key = generate_api_key()
    key_hash = hash_api_key(new_key)

    # Create database record
    db_api_key = ApiKey(key_hash=key_hash, name=api_key_data.name)

    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)

    # Return response with the plain key (only time it's shown)
    return ApiKeyResponse(
        id=db_api_key.id,
        name=db_api_key.name,
        key=new_key,  # Plain key returned only on creation
        is_active=db_api_key.is_active,
        created_at=db_api_key.created_at,
    )


@router.get("/", response_model=ApiKeyListResponse)
def list_api_keys(db: Session = Depends(get_db), _: bool = Depends(verify_admin_token)):
    """List all API keys (Admin only)"""
    api_keys = db.query(ApiKey).all()

    key_info_list = [
        ApiKeyInfo(id=key.id, name=key.name, is_active=key.is_active, created_at=key.created_at)
        for key in api_keys
    ]

    return ApiKeyListResponse(keys=key_info_list, total=len(key_info_list))


@router.get("/{key_id}", response_model=ApiKeyInfo)
def get_api_key(key_id: int, db: Session = Depends(get_db), _: bool = Depends(verify_admin_token)):
    """Get API key details by ID (Admin only)"""
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()

    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    return ApiKeyInfo(
        id=api_key.id, name=api_key.name, is_active=api_key.is_active, created_at=api_key.created_at
    )


@router.patch("/{key_id}/revoke", response_model=ApiKeyInfo)
def revoke_api_key(
    key_id: int, db: Session = Depends(get_db), _: bool = Depends(verify_admin_token)
):
    """Revoke (deactivate) an API key (Admin only)"""
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()

    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    api_key.is_active = False
    db.commit()
    db.refresh(api_key)

    return ApiKeyInfo(
        id=api_key.id, name=api_key.name, is_active=api_key.is_active, created_at=api_key.created_at
    )


@router.patch("/{key_id}/activate", response_model=ApiKeyInfo)
def activate_api_key(
    key_id: int, db: Session = Depends(get_db), _: bool = Depends(verify_admin_token)
):
    """Reactivate a revoked API key (Admin only)"""
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()

    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    api_key.is_active = True
    db.commit()
    db.refresh(api_key)

    return ApiKeyInfo(
        id=api_key.id, name=api_key.name, is_active=api_key.is_active, created_at=api_key.created_at
    )


@router.delete("/{key_id}")
def delete_api_key(
    key_id: int, db: Session = Depends(get_db), _: bool = Depends(verify_admin_token)
):
    """Permanently delete an API key (Admin only)"""
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()

    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    db.delete(api_key)
    db.commit()

    return {"message": "API key deleted successfully"}


# Public endpoint to check if an API key is valid
public_router = APIRouter(prefix="/api/keys", tags=["API Keys - Public"])


@public_router.get("/validate")
def validate_api_key(current_key: ApiKey = Depends(get_current_api_key)):
    """Validate current API key"""
    return {"valid": True, "name": current_key.name, "created_at": current_key.created_at}
