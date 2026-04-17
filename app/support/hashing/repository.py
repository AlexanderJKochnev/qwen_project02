# app/support/hashing/repository.py
from sqlalchemy.ext.asyncio import AsyncSession
import math
from typing import List, Optional, Tuple, Any
from sqlalchemy import select, func, desc, text, and_, or_
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT
from loguru import logger
from app.core.repositories.sqlalchemy_repository import Repository
from app.support.hashing.model import WordHash


class WordHashRepository(Repository):
    model = WordHash
