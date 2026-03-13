# app/support/producer/model.py
from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.config.project_config import settings
from app.core.models.base_model import BaseFull, plural, BaseFullFree
from app.service_registry import registers_search_update


# @registers_search_update("pruducer.drink.item")
class ProducerTitle(BaseFullFree):
    lazy = settings.LAZY
    single_name = 'producertitle'
    plural_name = plural(single_name)
    cascade = settings.CASCADE
    # Обратная связь: один ко многим
    producers = relationship(
        "Producer", back_populates=single_name, cascade=cascade, lazy=lazy
    )


class Producer(BaseFull):
    lazy = settings.LAZY
    single_name = 'producer'
    plural_name = plural(single_name)
    cascade = settings.CASCADE
    # Обратная связь: many to one
    producertitle_id: Mapped[int] = mapped_column(ForeignKey("producertitles.id"), nullable=True, index=True)
    producertitle: Mapped["ProducerTitle"] = relationship(back_populates=plural_name, lazy=lazy)
    # drinks = relationship(
    #     "Drink", back_populates=single_name, cascade=cascade, lazy=lazy
    #     )
