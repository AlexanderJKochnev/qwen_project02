# app/support/websearch/schemas.py
from pydantic import BaseModel
from typing import Optional, List


class SearchRequest(BaseModel):
    query: str


class SearchResponse(BaseModel):
    found_in_db: bool
    description: Optional[str] = None
    location: Optional[str] = None
    confidence: Optional[float] = None
    result: Optional[List] = None