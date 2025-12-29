# app/core/schemas/lang_schemas.py
from pydantic import computed_field
from app.core.schemas.base import ListView, DetailView
"""
    языковые pydantic модели для справочников
    добавлять по мере появления языков
"""


class ListViewEn(ListView):
    @computed_field(description='Name',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_name(self) -> str:
# /workspace/app/core/schemas/lang_schemas.py ru start 0015
        """Возвращает первое непустое значение из name, name_ru, name_fr"""
# /workspace/app/core/schemas/lang_schemas.py ru end 0015
# /workspace/app/core/schemas/lang_schemas.py ru start 0014
        return self.name or self.name_ru or self.name_fr or ""
# /workspace/app/core/schemas/lang_schemas.py ru end 0014


class DetailViewEn(DetailView):
    @computed_field(description='Name',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_name(self) -> str:
# /workspace/app/core/schemas/lang_schemas.py ru start 0013
        """Возвращает первое непустое значение из name, name_ru, name_fr"""
# /workspace/app/core/schemas/lang_schemas.py ru end 0013
# /workspace/app/core/schemas/lang_schemas.py ru start 0012
        return self.name or self.name_ru or self.name_fr or ""
# /workspace/app/core/schemas/lang_schemas.py ru end 0012

    @computed_field(description='Name',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_description(self) -> str:
# /workspace/app/core/schemas/lang_schemas.py ru start 0011
        return self.description or self.description_ru or self.description_fr or ""
# /workspace/app/core/schemas/lang_schemas.py ru end 0011


class ListViewRu(ListView):
    @computed_field(description='Наименование',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_name(self) -> str:
# /workspace/app/core/schemas/lang_schemas.py ru start 0010
        """Возвращает первое непустое значение из name, name_ru, name_fr"""
# /workspace/app/core/schemas/lang_schemas.py ru end 0010
# /workspace/app/core/schemas/lang_schemas.py ru start 0009
        return self.name_ru or self.name or self.name_fr or ""
# /workspace/app/core/schemas/lang_schemas.py ru end 0009


class DetailViewRu(DetailView):
    @computed_field(description='Наименование',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_name(self) -> str:
# /workspace/app/core/schemas/lang_schemas.py ru start 0008
        """Возвращает первое непустое значение из name, name_ru, name_fr"""
# /workspace/app/core/schemas/lang_schemas.py ru end 0008
# /workspace/app/core/schemas/lang_schemas.py ru start 0007
        return self.name_ru or self.name or self.name_fr or ""
# /workspace/app/core/schemas/lang_schemas.py ru end 0007

    @computed_field(description='Описание',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_description(self) -> str:
# /workspace/app/core/schemas/lang_schemas.py ru start 0006
        return self.description_ru or self.description or self.description_fr or ""
# /workspace/app/core/schemas/lang_schemas.py ru end 0006


class ListViewFr(ListView):
    @computed_field(description='Nom',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_name(self) -> str:
# /workspace/app/core/schemas/lang_schemas.py ru start 0005
        """Возвращает первое непустое значение из name, name_ru, name_fr"""
# /workspace/app/core/schemas/lang_schemas.py ru end 0005
# /workspace/app/core/schemas/lang_schemas.py ru start 0004
        return self.name_fr or self.name or self.name_ru or ""
# /workspace/app/core/schemas/lang_schemas.py ru end 0004


class DetailViewFr(DetailView):
    @computed_field(description='Nom',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_name(self) -> str:
# /workspace/app/core/schemas/lang_schemas.py ru start 0003
        """Возвращает первое непустое значение из name, name_ru, name_fr"""
# /workspace/app/core/schemas/lang_schemas.py ru end 0003
# /workspace/app/core/schemas/lang_schemas.py ru start 0002
        return self.name_ru or self.name or self.name_fr or ""
# /workspace/app/core/schemas/lang_schemas.py ru end 0002

    @computed_field(description='Description',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_description(self) -> str:
# /workspace/app/core/schemas/lang_schemas.py ru start 0001
        return self.description_fr or self.description or self.description_ru or ""
# /workspace/app/core/schemas/lang_schemas.py ru end 0001
