# app.support.clickhouse.router.py
# app/api/routes/beverages.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List

from app.support.clickhouse.dependencies import get_repository
from app.support.clickhouse.import_service.beverage_repository import BeverageRepository
# from app.support.clickhouse.repository import BeverageRepository
from app.support.clickhouse.import_service.schemas import BeverageCategory, BeverageCreate, BeverageUpdate

router = APIRouter(prefix="/beverages", tags=["beverages"])


@router.get("/", response_model=List[dict])
async def list_beverages(
    category: Optional[BeverageCategory] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    repo: BeverageRepository = Depends(get_repository)
):
    """Список напитков"""
    return await repo.list_all(category, limit, offset)


@router.get("/{beverage_id}")
async def get_beverage(
    beverage_id: str,
    repo: BeverageRepository = Depends(get_repository)
):
    """Получить напиток по ID"""
    result = await repo.get_by_id(beverage_id)
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    return result


@router.post("/")
async def create_beverage(
    data: BeverageCreate,
    repo: BeverageRepository = Depends(get_repository)
):
    """Создать напиток"""
    # TODO: сгенерировать эмбеддинг
    return {"message": "Created"}


@router.put("/{beverage_id}")
async def update_beverage(
    beverage_id: str,
    data: BeverageUpdate,
    repo: BeverageRepository = Depends(get_repository)
):
    """Обновить напиток"""
    updated = await repo.update(beverage_id, data.dict(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Not found")
    return {"message": "Updated"}


@router.delete("/{beverage_id}")
async def delete_beverage(
    beverage_id: str,
    repo: BeverageRepository = Depends(get_repository)
):
    """Удалить напиток"""
    await repo.delete(beverage_id)
    return {"message": "Deleted"}
