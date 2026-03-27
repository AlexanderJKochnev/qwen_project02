from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db # Ваша функция получения сессии

router = APIRouter()

@router.get("/search")
async def search(
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db)
):
    results = await search_service.global_search(query=q, pg_db=db)
    return results
