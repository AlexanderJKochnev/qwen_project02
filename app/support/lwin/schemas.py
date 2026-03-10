# app.support.lwin.schemas.py
from datetime import datetime
from typing import Optional
# from pydantic import model_validator, ConfigDict, Field, field_validator, computed_field
from app.core.schemas.base import BaseModel


class LwinCommon:
    STATUS: Optional[str] = None
    DISPLAY_NAME: Optional[str] = None
    PRODUCER_TITLE: Optional[str] = None
    PRODUCER_NAME: Optional[str] = None
    WINE: Optional[str] = None
    COUNTRY: Optional[str] = None
    REGION: Optional[str] = None
    SUB_REGION: Optional[str] = None
    SITE: Optional[str] = None
    PARCEL: Optional[str] = None
    COLOUR: Optional[str] = None
    TYPE: Optional[str] = None
    SUB_TYPE: Optional[str] = None
    DESIGNATION: Optional[str] = None
    CLASSIFICATION: Optional[str] = None
    VINTAGE_CONFIG: Optional[str] = None
    FIRST_VINTAGE: Optional[str] = None
    FINAL_VINTAGE: Optional[str] = None
    DATE_ADDED: Optional[datetime] = None
    DATE_UPDATED: Optional[datetime] = None
    REFERENCE: Optional[str] = None


class LwinCreate(BaseModel, LwinCommon):
    LWIN: str


class LwinUpdate(BaseModel, LwinCommon):
    LWIN: Optional[str] = None


class LwinRead(LwinCreate):
    id: int
