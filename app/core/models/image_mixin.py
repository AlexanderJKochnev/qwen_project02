# app/core/models/image_mixin.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.models.base_model import Base  # noqa: F401


class ImageMixin:
    """Mixin для добавления функционала изображений к моделям"""
    # image file name (оставлено для обратной совместимости - потом удалить
    image_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # image id - ИМЯ НЕ МЕНЯТЬ
    image_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
