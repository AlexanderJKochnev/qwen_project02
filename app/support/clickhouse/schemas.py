# app.support.clickhouse.schemas.py
from typing import Any, Dict, Optional
from pydantic import Field
from datetime import datetime
from app.core.schemas.base import BaseModel


class BeverageBase(BaseModel):
    name: str
    description: str
    category: str
    country: Optional[str] = None
    brand: Optional[str] = None
    abv: Optional[float] = None
    price: Optional[float] = None
    rating: Optional[float] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class BeverageCreate(BeverageBase):
    pass


class BeverageUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    rating: Optional[float] = None
    attributes: Optional[Dict[str, Any]] = None


class BeverageInDB(BeverageBase):
    id: str
    file_hash: Optional[str] = None
    source_file: Optional[str] = None
    created_at: datetime


class SearchQuery(BaseModel):
    query: str
    category: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)


class SearchResult(BaseModel):
    name: str
    description: str
    category: str
    country: Optional[str]
    brand: Optional[str]
    price: Optional[float]
    rating: Optional[float]
    similarity: float


class RAGResponse(BaseModel):
    query: str
    found: int
    generated: str
    sources: list[SearchResult]
