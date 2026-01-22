# app/core/schemas/api_mixin.py
""" нигде не используется """

from pydantic import computed_field

from app.core.schemas.base import BaseModel


class LangMixin(BaseModel):
    """
        языковая схема - добавлять 'name_<lang>'
        нужно для конвертации вложенных моделей в плоские
        если в модели поле возвращают другую модель,
        создает в корне  вычисляемые поля языковые поля и подставляет в них значения
        из полей вложенных  моделей  определенных в __get_lang__
    """

    def __get_schema__(self):
        schema = None
        field_name = None
        return schema, field_name

    def __get_lang__(self, lang: str = '_ru', ) -> str:
        schema, field_name = self.__get_schema__()
        if schema:
            prefix = getattr(schema, f'{field_name}{lang}') or getattr(schema, f'{field_name}')
            return prefix
        return None

    @computed_field
    @property
    def name_ru(self) -> str:
        return self.__get_lang__('_ru')

    @computed_field
    @property
    def name_fr(self) -> str:
        return self.__get_lang__('_fr')

    @computed_field
    @property
    def name(self) -> str:
        return self.__get_lang__('')
