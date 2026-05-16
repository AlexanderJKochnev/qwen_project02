# app/core/models/image_mixin.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.models.base_model import Base  # noqa: F401


class ImageMixin:
    """Mixin для добавления функционала изображений к моделям"""
    # image file name (оставлено для обратной совместимости - потом удалить
    image_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # image id - ИМЯ НЕ МЕНЯТЬ
    image_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # ПРЕДЫДУЩИЕ ЗНАЧЕНИЯ DEPRECATED удалить после импорта данных в seaweeds
    seaweed_fids: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    # ДАННЫЕ В ЭТОМ ПОЛЕЯ ХРАНЯТСЯ СЛЕДУЮЩИМ СПОСОБОМ:
    # кол-во не огранично
    # каждый элемент это fid файла в seaweed
    # 0,2,4,6, ... полные изображения
    # 1,3,5,7, ... их thumbnail