# app/preact/handbook/router.py
"""
    роутер для справочников
    выводит только словари  id: name
    по языкам
"""
from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.preact.core.router import PreactRouter
from app.core.config.database.db_async import get_db
from typing import List
from app.core.utils.pydantic_utils import get_pyschema


class HandbookRouter(PreactRouter):
    def __init__(self):
        super().__init__(prefix='handbooks', method='GET', tier=2)

    def __source_generator__(self, source: dict):
        """
        генератор для создания роутов
        """
        return ((f'/{key}' + '/{lang}',
                 List[get_pyschema(val, 'ListView')],
                 None) for key, val in source.items())

    async def endpoint(self, request: Request, lang: str, session: AsyncSession = Depends(get_db)):
        current_path = request.url.path
        pref, lang = self.__path_decoder__(current_path)
        model = self.source.get(pref)
        # lang = self.get_lang_prefix(lang)  # convert lang to lang pref 'en' -> '', 'ru' -> '_ru' ...
        repo = self.get_repo(model)
        service = self.get_service(model)
        # print(f'{route.response_model=}, {repo=}')
        rows = await service.get_list_view(lang, repo, model, session)
        return rows
