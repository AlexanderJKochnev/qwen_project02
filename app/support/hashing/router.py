# app/support/hashing/router.py
from fastapi import APIRouter
from app.support import Item
from app.support.hashing.model import WordHash
from sqlalchemy.ext.asyncio import AsyncSession
from app.fill_wordhash import seed_word_dictionary


router = APIRouter(prefix="/hashing", tags=["hashing"])


@router.get("/search")
async def goahead(self, session: AsyncSession):
    nmbr = await seed_word_dictionary(session, Item, WordHash)
    return {f'{nmbr} records shall be added'}
