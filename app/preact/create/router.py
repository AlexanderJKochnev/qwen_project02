# app/preact/create/router.py
from typing import Any, Dict, Type
from app.core.models.base_model import DeclarativeBase
from fastapi import Body, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.utils.pydantic_utils import sqlalchemy_to_pydantic_post, get_pyschema
from app.core.config.database.db_async import get_db
from app.preact.core.router import PreactRouter


class CreateRouter(PreactRouter):
    def __init__(self):
        super().__init__(prefix='create', method='POST', tier=3)

    def __set_schema__(self, model: Type[DeclarativeBase]):
        """ по имени модели находит для response_model соотвествующую Create схему,
            а если ее нет то создает
        """
        schema = get_pyschema(model, 'Create') or sqlalchemy_to_pydantic_post(model)
        setattr(self, f'{model.__name__}Create', schema)
        schema_response = get_pyschema(model, 'CreateResponse') or sqlalchemy_to_pydantic_post(model)
        setattr(self, f'{model.__name__}CreateResponse', schema_response)

    def __get_schemas__(self, model: Type[DeclarativeBase], typo: str = 'Create'):
        """ получает ранее созданную Create схему """
        return getattr(self, f'{model.__name__}{typo}', )

    def schemas_generator(self, source: dict):
        """ генератор pydantic схем """
        for model in self.source.values():
            self.__set_schema__(model)

    def __source_generator__(self, source: dict):
        return ((f'/{key}',
                 get_pyschema(val, 'CreateResponse'),
                 get_pyschema(val, 'Create'),) for key, val in source.items())
        # return ((f'/{key}', self.__get_schemas__(val)) for key, val in source.items())
        # get_pyschema(val, 'DetailView'),

    async def endpoint(self, request: Request, data: Dict[str, Any] = Body(...),
                       session: AsyncSession = Depends(get_db)):
        try:
            current_path = request.url.path
            #  print(f'{current_path=}')
            _, tmp = self.__path_decoder__(current_path)
            model = self.source.get(tmp)
            schema = self.__get_schemas__(model)
            repo = self.get_repo(model)
            service = self.get_service(model)
            model_data = schema(**data)
            obj, result = await service.get_or_create(model_data, repo, model, session)
            # print(f'{result=}')
            return obj
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f'Create Fault, {e}'
            )
