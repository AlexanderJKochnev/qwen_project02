# app.support.clickhouse.schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class BeverageCategory(str, Enum):
    WINE = "wine"
    WHISKY = "whisky"
    BEER = "beer"
    SPIRITS = "spirits"


class BeverageBase(BaseModel):
    name: str
    description: str
    category: BeverageCategory
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
    category: Optional[BeverageCategory] = None
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
