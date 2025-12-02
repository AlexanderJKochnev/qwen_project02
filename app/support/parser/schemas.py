# app/support/parser/schemas.py
from typing import Optional, Any
import json

from pydantic import field_serializer
from app.core.schemas.base import (CreateResponse, DateSchema,
                                   BaseModel, PkSchema)
# from app.core.schemas.image_mixin import ImageUrlMixin


class StatusCreate(BaseModel):
    status: str


class StatusCreateRelation(StatusCreate):
    pass


class StatusCreateResponseSchema(StatusCreate, CreateResponse):
    pass


class StatusUpdate(BaseModel):
    status: Optional[str] = None


class StatusRead(StatusCreate, PkSchema, DateSchema):
    pass


class StatusReadRelation(StatusRead):
    pass


class RegistryCreate(BaseModel):
    shortname: str
    url: str
    base_path: Optional[str] = None
    # HTML-тег и атрибут для извлечения ссылок
    link_tag: Optional[str] = None
    link_attr: Optional[str] = None
    parent_selector: Optional[str] = None
    timeout: Optional[int] = None
    status_id: Optional[int] = 1


class RegistryCreateRelation(BaseModel):
    shortname: str
    url: str
    base_path: Optional[str] = None
    # HTML-тег и атрибут для извлечения ссылок
    link_tag: Optional[str] = None
    link_attr: Optional[str] = None
    parent_selector: Optional[str] = None
    timeout: Optional[int] = None
    status: StatusCreateRelation


class RegistryCreateResponseSchema(RegistryCreate, CreateResponse):
    pass


class RegistryUpdate(BaseModel):
    shortname: Optional[str] = None
    url: Optional[str] = None
    base_path: Optional[str] = None
    # HTML-тег и атрибут для извлечения ссылок
    link_tag: Optional[str] = None
    link_attr: Optional[str] = None
    parent_selector: Optional[str] = None
    timeout: Optional[int] = None

    status_id: Optional[int] = 1


class RegistryRead(RegistryCreate, PkSchema, DateSchema):
    pass


class RegistryReadRelation(PkSchema, DateSchema):
    shortname: str
    url: str
    base_path: Optional[str] = None
    # HTML-тег и атрибут для извлечения ссылок
    link_tag: Optional[str] = None
    link_attr: Optional[str] = None
    parent_selector: Optional[str] = None
    timeout: Optional[int] = None
    status: StatusRead


# ------------------
class CodeCreate(BaseModel):
    code: str
    url: str
    status_id: Optional[int] = 1


class CodeCreateRelation(BaseModel):
    code: str
    url: str
    status: StatusCreateRelation
    registry: RegistryCreateRelation


class CodeCreateResponseSchema(CodeCreate, CreateResponse):
    pass


class CodeUpdate(BaseModel):
    code: Optional[str] = None
    url: Optional[str] = None
    status_id: Optional[int] = 1


class CodeRead(CodeCreate, PkSchema, DateSchema):
    pass


class CodeReadRelation(PkSchema, DateSchema):
    code: str
    url: Optional[str] = None
    status: StatusRead
    registry: RegistryRead


class NameCreate(BaseModel):
    name: str
    url: str
    code_id: int
    status_id: Optional[int] = 1


class NameCreateRelation(BaseModel):
    name: str
    url: str
    code: CodeCreateRelation
    status: StatusCreateRelation


class NameCreateResponseSchema(NameCreate, CreateResponse):
    pass


class NameUpdate(BaseModel):
    name: Optional[str] = None
    code_id: Optional[int] = None
    url: Optional[str] = None
    status_id: Optional[int] = 1


class NameRead(NameCreate, PkSchema, DateSchema):
    pass


class NameReadRelation(PkSchema, DateSchema):
    name: str
    url: str
    code: CodeRead
    status: StatusRead


class RawdataCreate(BaseModel):
    body_html: str
    name_id: int
    status_id: Optional[int] = 1


class RawdataCreateRelation(BaseModel):
    body_html: str
    name: NameCreateRelation
    status: StatusCreateRelation


class RawdataCreateResponseSchema(RawdataCreate, CreateResponse):
    pass


class RawdataUpdate(BaseModel):
    body_html: Optional[str] = None
    name_id: Optional[int] = None
    status_id: Optional[int] = 1
    parsed_data: Optional[str] = None


class RawdataRead(RawdataCreate, PkSchema, DateSchema):
    parsed_data: Optional[str] = None  # Store as string in schema since it's stored as string in DB
    
    @field_serializer('parsed_data')
    def serialize_parsed_data(self, value: Optional[str]) -> Optional[dict[str, Any]]:
        """Convert parsed_data from JSON string to dict during serialization."""
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # If parsing fails, return the original value
            return value


class RawdataReadRelation(PkSchema, DateSchema):
    body_html: Optional[str]
    name: NameRead
    status: StatusRead
    parsed_data: Optional[str] = None  # Store as string in schema since it's stored as string in DB
    
    @field_serializer('parsed_data')
    def serialize_parsed_data(self, value: Optional[str]) -> Optional[dict[str, Any]]:
        """Convert parsed_data from JSON string to dict during serialization."""
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # If parsing fails, return the original value
            return value


class ImageCreate(BaseModel):
    name_id: int
    image_path: Optional[str] = None
    image_id: Optional[str] = None


class ImageCreateRelation(BaseModel):
    image_path: Optional[str] = None
    image_id: Optional[str] = None
    name: NameCreateRelation


class ImageCreateResponseSchema(ImageCreate, CreateResponse):
    pass


class ImageUpdate(BaseModel):
    image_path: Optional[str] = None
    image_id: Optional[str] = None
    name_id: Optional[int] = None


class ImageRead(ImageCreate, PkSchema, DateSchema):
    pass


class ImageReadRelation(PkSchema, DateSchema):
    image_path: Optional[str] = None
    image_id: Optional[str] = None
    name: NameRead
