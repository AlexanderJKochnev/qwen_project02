# api/schemas.py
from pydantic import BaseModel
from typing import Optional, Dict, Any


class BeverageCreate(BaseModel):
    name: str
    description: str
    category: str
    country: Optional[str] = None
    brand: Optional[str] = None
    abv: Optional[float] = None
    price: Optional[float] = None
    rating: Optional[float] = None
    attributes: Dict[str, Any] = {}


class BeverageUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    rating: Optional[float] = None
    attributes: Optional[Dict[str, Any]] = None


class SearchQuery(BaseModel):
    query: str
    category: Optional[str] = None
    limit: int = 10
