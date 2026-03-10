# app.support.lwin.schemas.py
from datetime import datetime
from typing import Optional
# from pydantic import model_validator, ConfigDict, Field, field_validator, computed_field
from app.core.schemas.base import BaseModel


class LwinCommon:
    status: Optional[str] = None
    display_name: Optional[str] = None
    producer_title: Optional[str] = None
    producer_name: Optional[str] = None
    wine: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    sub_region: Optional[str] = None
    site: Optional[str] = None
    parcel: Optional[str] = None
    colour: Optional[str] = None
    type: Optional[str] = None
    sub_type: Optional[str] = None
    designation: Optional[str] = None
    classification: Optional[str] = None
    vintage_config: Optional[str] = None
    first_vintage: Optional[str] = None
    final_vintage: Optional[str] = None
    date_added: Optional[datetime] = None
    date_updated: Optional[datetime] = None


class LwinCreate(BaseModel, LwinCommon):
    lwin: str


class LwinUpdate(BaseModel, LwinCommon):
    lwin: Optional[str] = None


class LwinRead(LwinCreate):
    id: int
