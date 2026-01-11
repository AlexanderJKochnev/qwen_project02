# app/support/read/router.py
"""
    роутер для UpdateView (заполнение) для всех кроме Drink & Items
    Items_Drinks заполняются из ItemViewRouter.get_one
    сюда же внедряем перевод
"""
from typing import Callable, Annotated
from fastapi import Request, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from app.depends import get_translator_func
from app.preact.core.router import PreactRouter
from app.core.config.database.db_async import get_db
from app.core.utils.pydantic_utils import get_pyschema
from app.core.utils.exception_handler import ValidationError_handler


class ReadRouter(PreactRouter):
    translation: Annotated[Callable, Depends(get_translator_func)]

    def __init__(self):
        super().__init__(prefix='read', method='GET', tier=2)

    def __source_generator__(self, source: dict):
        """
        генератор для создания роутов
        """
        return ((f'/{key}' + '/{id}',
                 get_pyschema(val, 'Create'),
                 None) for key, val in source.items())

    async def endpoint(self, request: Request, id: int,
                       translation: Annotated[Callable, Depends(get_translator_func)],
                       session: AsyncSession = Depends(get_db)):
        try:
            current_path = request.url.path
            # route = request.scope["route"]
            # response_model = route.response_model
            pref, _ = self.__path_decoder__(current_path, 2)
            model = self.source.get(pref)
            repo = self.get_repo(model)
            service = self.get_service(model)
            obj = await service.get_by_id(id, repo, model, session)
            result_dict = obj.to_dict()
            translated_dict = await translation(result_dict)
            return translated_dict
        except ValidationError as exc:
            ValidationError_handler(exc)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f'ReadRouter, {pref}: {exc}')
