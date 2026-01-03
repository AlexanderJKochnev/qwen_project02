# app/support/field_keys/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.config.database.db_config import get_async_session
from app.support.field_keys.service import FieldKeyService
from app.support.field_keys.schemas import FieldKeyResponse, FieldKeyCreate, FieldKeyUpdate
from app.support.field_keys.repository import FieldKeyRepository


router = APIRouter(prefix="/field_keys", tags=["field_keys"])


@router.get("/", response_model=List[FieldKeyResponse])
async def get_field_keys(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session)
):
    repo = FieldKeyRepository(session)
    # For now, we'll just return all field keys without complex filtering
    # In a real implementation, you'd add proper query logic here
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{field_key_id}", response_model=FieldKeyResponse)
async def get_field_key(
    field_key_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    repo = FieldKeyRepository(session)
    # For now, we'll just return a single field key
    # In a real implementation, you'd add proper query logic here
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/", response_model=FieldKeyResponse)
async def create_field_key(
    field_key: FieldKeyCreate,
    session: AsyncSession = Depends(get_async_session)
):
    service = FieldKeyService(session)
    result = await service.get_or_create_field_key(
        short_name=field_key.short_name,
        full_name=field_key.full_name
    )
    # Convert result to FieldKeyResponse
    return FieldKeyResponse(
        id=result["id"],
        short_name=result["short_name"],
        full_name=result["full_name"],
        frequency=result["frequency"],
        created_at=None,  # This will be filled by Pydantic from the database
        updated_at=None   # This will be filled by Pydantic from the database
    )


@router.put("/{field_key_id}", response_model=FieldKeyResponse)
async def update_field_key(
    field_key_id: int,
    field_key_update: FieldKeyUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/{field_key_id}")
async def delete_field_key(
    field_key_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    raise HTTPException(status_code=501, detail="Not implemented yet")
