# app/core/routers/base.py
import orjson
from typing import Any, List, Type, TypeVar, Callable
# from dateutil.relativedelta import relativedelta
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, BackgroundTasks, Response
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.auth.dependencies import get_active_user_or_internal
from app.core.config.database.db_async import get_db
from app.core.config.project_config import get_paging, settings
from app.core.utils.common_utils import back_to_the_future, delta_data
from app.core.services.service import Service
from app.core.schemas.base import (DeleteResponse, PaginatedResponse, ReadSchema,
                                   CreateResponse, UpdateSchema, CreateSchema)
from app.core.exceptions import exception_to_http
from app.core.utils.pydantic_utils import get_repo, get_service, get_pyschema


paging = get_paging
TCreateSchema = TypeVar("TCreateSchema", bound=CreateSchema)
TUpdateSchema = TypeVar("TUpdateSchema", bound=UpdateSchema)
TReadSchema = TypeVar("TReadSchema", bound=ReadSchema)
TCreateResponse = TypeVar("TCreateResponse", bound=CreateResponse)
TUpdateSchema = TypeVar("TUpdateSchema", bound=UpdateSchema)
TService = TypeVar("TService", bound=Service)

# dev = settings.DEV
delta = delta_data(settings.DATA_DELTA)    # (datetime.now(timezone.utc) - relativedelta(years=2)).isoformat()


def type_checking(result, func_name):
    logger.info(f'{type(result)}, {func_name}')
    if isinstance(result, dict):
        if items := result.get('items'):
            logger.info(f'    {type(items[0])}, {func_name}')
    elif isinstance(result, list):
        logger.info(f'    {type(result[0])}, {func_name}')


class BaseRouter:
    """
    Базовый роутер с общими CRUD-методами.
    Наследуйте и переопределяйте get_query() для добавления selectinload.
    """

    def __init__(
        self,
        model: Type[Any],
        prefix: str,
        auth_dependency: Callable = get_active_user_or_internal,
        **kwargs
    ):
        self.model = model
        self.repo = get_repo(model)
        self.service: TService = get_service(model)

        self.auth_dependency = auth_dependency
        # input py schema for simple create without relation
        self.create_schema = get_pyschema(model, 'Create')
        self.create_response_schema = get_pyschema(model, 'CreateResponseSchema') or self.create_schema
        # input py schema for create with relation
        self.create_schema_relation = get_pyschema(model, 'CreateRelation') or self.create_schema
        # input update schema
        self.update_schema = get_pyschema(model, 'Update')

        # response schemas:
        self.read_schema = get_pyschema(model, 'Read')
        self.read_schema_relation = get_pyschema(model, 'ReadRelation') or self.read_schema
        self.paginated_response = PaginatedResponse[self.read_schema_relation]
        self.nonpaginated_response = List[self.read_schema_relation]
        self.delete_response = DeleteResponse

        self.prefix = prefix
        self.tags = [prefix.replace('/', '')]
        include_in_schema = kwargs.get('include_in_schema', True)
        self.router = APIRouter(prefix=prefix,
                                tags=self.tags,
                                dependencies=[Depends(self.auth_dependency)],
                                include_in_schema=include_in_schema)
        self.setup_routes()
        # self.read_response = py.read_response(read_schema)
        # self.path_schema = path_schema

    def setup_routes(self):
        """Настраивает маршруты"""
        self.router.add_api_route("", self.create, methods=["POST"],
                                  response_model=self.create_response_schema,
                                  openapi_extra={'x-request-schema': self.create_schema.__name__})

        self.router.add_api_route("/hierarchy",
                                  self.create_relation,
                                  status_code=status.HTTP_200_OK,
                                  methods=["POST"],
                                  response_model=self.read_schema_relation,
                                  openapi_extra={'x-request-schema': self.create_schema_relation.__name__})
        """
        self.router.add_api_route("/batch",
                                  self.batch_create,
                                  status_code=status.HTTP_200_OK,
                                  methods=['POST'],
                                  response_model=List[self.read_schema_relation],
                                  openapi_extra={'x-request-schema':
                                                 f"List_{self.create_schema_relation.__name__}"})
        """
        # get all без паггинации
        self.router.add_api_route("", self.get, methods=["GET"],
                                  # response_model=self.paginated_response,
                                  openapi_extra={'x-request-schema': None})
        # search с пагинацией
        self.router.add_api_route("/search", self.search, methods=["GET"],
                                  response_model=self.paginated_response,
                                  openapi_extra={'x-request-schema': None})
        # search без пагинации
        self.router.add_api_route("/search_all",
                                  self.search_all, methods=["GET"],
                                  response_model=self.nonpaginated_response,
                                  openapi_extra={'x-request-schema': None})
        self.router.add_api_route("/search_geans",
                                  self.search_geans, methods=["GET"],
                                  response_model=self.paginated_response,
                                  openapi_extra={'x-request-schema': None}
                                  )
        self.router.add_api_route("/search_geans_all",
                                  self.search_geans_all, methods=["GET"],
                                  # response_model=self.nonpaginated_response,
                                  openapi_extra={'x-request-schema': None}
                                  )
        # get without pagination
        self.router.add_api_route("/all",
                                  self.get_all, methods=["GET"],
                                  # response_model=self.nonpaginated_response,  # List[self.read_response])
                                  openapi_extra={'x-request-schema': None})
        # get full
        self.router.add_api_route("/full",
                                  self.get_full,
                                  methods=["GET"],
                                  # response_model=self.nonpaginated_response,
                                  openapi_extra={'x-request-schema': None})
        # get full
        self.router.add_api_route("/full_page",
                                  self.get_full_with_pagination,
                                  methods=["GET"],
                                  openapi_extra={'x-request-schema': None})
        # get one buy id
        self.router.add_api_route("/{id}",
                                  self.get_one, methods=["GET"],
                                  # response_model=self.read_schema,
                                  openapi_extra={'x-request-schema': None})

        self.router.add_api_route("",
                                  self.update_or_create, methods=["PATCH"],
                                  response_model=self.read_schema,
                                  openapi_extra={'x-request-schema': self.update_schema.__name__})
        self.router.add_api_route("/{id}",
                                  self.patch, methods=["PATCH"],
                                  # response_model=self.read_schema,
                                  openapi_extra={'x-request-schema': self.update_schema.__name__})

        self.router.add_api_route("/{id}",
                                  self.delete, methods=["DELETE"],
                                  response_model=self.delete_response,
                                  openapi_extra={'x-request-schema': None})

    async def create(self, data: TCreateSchema,
                     session: AsyncSession = Depends(get_db)) -> TReadSchema:
        """
        Создание одной записи без зависимостей
        input_valudation_chema <>CreateRelation
        response_model <>CreateResponseSchema
        """
        try:
            # obj = await self.service.create(data, self.repo, self.model, session)
            obj, created = await self.service.get_or_create(data, self.repo, self.model, session)
            return obj
        except Exception as e:
            detail = (f'ошибка создания записи {e}, model = {self.model}, '
                      f'create_schema = {self.create_schema}, '
                      f'service = {self.service} ,'
                      f'repository = {self.repo}')
            print(detail)
            raise HTTPException(status_code=500, detail=detail)

    async def batch_create(self, data: List[TCreateSchema],
                           session: AsyncSession = Depends(get_db)) -> List[TReadSchema]:
        """
         Создание нескольких записей без зависимостей
        """
        try:
            obj = await self.service.batch_get_or_create(data, self.repo, self.model, session)
            return obj
        except Exception as e:
            detail = (f'ошибка создания записи {e}, model = {self.model}, '
                      f'create_schema = {self.create_schema}, '
                      f'service = {self.service} ,'
                      f'repository = {self.repo}')
            print(detail)
            raise HTTPException(status_code=500, detail=detail)

    async def create_relation(self, data: TCreateSchema, session: AsyncSession = Depends(get_db)) -> TReadSchema:
        """
        Создание одной записи с зависимостями - если в таблице есть зависимости
        они будут рекурсивно найдены в связанных таблицах (или добавлены при отсутсвии)
        переписать если есть зависимости
        input_valudation_chema <>CreateRelation
        response_model <>ReadRelation
        """
        try:
            obj = await self.service.create_relation(data, self.repo, self.model, session)
            if isinstance(obj, tuple):
                obj, _ = obj
            # return obj
            return await self.service.get_by_id(obj.id, self.repo, self.model, session)
        except Exception as e:
            raise exception_to_http(e)

    async def update_or_create(self, data: TUpdateSchema, background_tasks: BackgroundTasks,
                               session: AsyncSession = Depends(get_db)) -> TReadSchema:
        """
            обновление / добавление одной записи ? пока нигде не используется
            input_valudation_chema <>CreateRelation
            response_model <>ReadRelation
        """
        try:
            obj, created = await self.service.update_or_create(data, self.repo, self.model, background_tasks, session)
            return obj
        except Exception as e:
            detail = (f'ошибка обновления записи {e}, model = {self.model}, '
                      f'create_schema = {self.create_schema}, '
                      f'service = {self.service} ,'
                      f'repository = {self.repo}')
            print(detail)
            raise HTTPException(status_code=405, detail=detail)

    async def patch(self, id: int,
                    data: TUpdateSchema, background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)) -> TReadSchema:
        """
            Изменение одной записи по id
            input_valudation_chema <>Update
            response_model <>Read
        """
        result = await self.service.patch(id, data, self.repo, self.model, background_tasks,
                                          session)
        return result

    # @logger.catch(reraise=True)
    async def delete(self, id: int, background_tasks: BackgroundTasks,
                     session: AsyncSession = Depends(get_db)) -> DeleteResponse:
        """
            Удаление одной записи по id
            input_valudation_chema No
            response_model <>DeleteResponse
        """
        try:
            await self.service.delete(id, self.model, self.repo, background_tasks, session)
            return DeleteResponse(success=True, deleted_count=1, message=f'record with {id=}')
        except ValueError:
            raise HTTPException(status_code=404, detail=f"record with {id=} not found")
        except PermissionError as e:
            raise HTTPException(status_code=409, detail=f'{id=}, {str(e)}')
        except Exception as e:
            raise HTTPException(status_code=409, detail=f'{id=}, {str(e)}')

    async def get_one(self,
                      id: int,
                      session: AsyncSession = Depends(get_db)):
        """
            Получение одной записи по ID
            input_valudation_chema <>CreateRelation
            response_model <>ReadRelatio
        """
        obj = await self.service.get_by_id(id, self.repo, self.model, session)
        if obj is None:
            raise HTTPException(status_code=404, detail=f'Запрашиваемый файл {id} не найден на сервере')
        res = obj.to_dict_fast(skip_empty=True)
        content = orjson.dumps(res)
        return Response(content=content, media_type="application/json")
        # return res
        # return validated_res.model_dump(exclude_none=True, exclude_unset=True)

    async def get(self,
                  after_date: datetime = Query(delta,
                                               description="Дата в формате ISO 8601 (например, 2024-01-01T00:00:00Z)"),
                  page: int = Query(1, ge=1),
                  page_size: int = Query(paging.get('def', 20),
                                         ge=paging.get('min', 1),
                                         le=paging.get('max', 1000)),
                  session: AsyncSession = Depends(get_db)
                  ):
        """
            Получение постранично всех записей после заданной даты.
            По умолчанию задана дата - 2 года от сейчас
            input_valudation_chema None
            response_model PaginatedResponse[<>ReadRelation>]
        """
        after_date = back_to_the_future(after_date)
        response = await self.service.get(after_date, page, page_size, self.repo, self.model, session)
        content = orjson.dumps(response)
        return Response(content=content, media_type="application/json")
        # return response

    async def get_all(
            self,
            after_date: datetime = Query(delta,
                                         # (datetime.now(timezone.utc) - relativedelta(years=2)).isoformat(),
                                         description="Дата в формате ISO 8601 (например, 2024-01-01T00:00:00Z)"
                                         ), session: AsyncSession = Depends(get_db), limit: int = 20
    ):
        """
            Получение все записей одним списком после указанной даты.
            По умолчанию задана дата - 2 года от сейчас
            input_valudation_chema <>CreateRelation
            response_model <>ReadRelatio

        """
        try:
            after_date = back_to_the_future(after_date)
            response = await self.service.get_all(after_date, self.repo, self.model, session)
            content = orjson.dumps(response)
            return Response(content=content, media_type="application/json")
            # return response
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Internal server error. {e}")

    async def get_full(self, session: AsyncSession = Depends(get_db)) -> List[TReadSchema]:
        try:
            return await self.service.get_full(self.repo, self.model, session)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Internal server error. {e}")

    async def get_full_with_pagination(self,
                                       page: int = Query(1, ge=1),
                                       page_size: int = Query(paging.get('def', 20),
                                                              ge=paging.get('min', 1),
                                                              le=paging.get('max', 1000)),
                                       session: AsyncSession = Depends(get_db)
                                       ) -> PaginatedResponse:
        """
            Получение постранично всех записей
        """
        # print(f"📥 GET request for {self.model.__name__} from")
        response = await self.service.get_full_with_pagination(page, page_size, self.repo, self.model, session)
        # type_checking(response, 'get')
        result = self.paginated_response(**response)
        return result

    async def search(self, search: str = Query(None, description="Поисковый запрос. "
                                               "В случае пустого запроса будут "
                                               "выведены все данные "),
                     page: int = Query(1, ge=1),
                     page_size: int = Query(paging.get('def', 20),
                                            ge=paging.get('min', 1),
                                            le=paging.get('max', 1000)),
                     session: AsyncSession = Depends(get_db),
                     ) -> PaginatedResponse:
        """
            Поиск по всем текстовым полям основной таблицы
            с постраничным выводом результата
            input_valudation_chema None
            response_model PaginatedResponse[<>ReadRelation>]
        """
        result = await self.service.search(search, page, page_size, self.repo, self.model, session)
        return result

    async def search_all(self,
                         search: str = Query(None, description="Поисковый запрос. "
                                             "В случае пустого запроса будут "
                                             "выведены все данные "),
                         session: AsyncSession = Depends(get_db), limit: int = 20) -> List[TReadSchema]:
        """
            Поиск по всем текстовым полям основной таблицы БЕЗ пагинации
            input_valudation_chema <>CreateRelation
            response_model <>ReadRelatio
        """
        result = await self.service.search_all(search, self.repo, self.model, session, limit)
        return result

    async def search_geans(self, search: str = Query(None,
                                                     min_length=3, max_length=50,
                                                     description="Полнотекстовый поиск по слову или "
                                                                 " части слова (с начала), "
                                                                 " набору слов в любом порядке"),
                           similarity_threshold: float = Query(None, ge=0, le=1.0),
                           page: int = Query(1, ge=1),
                           page_size: int = Query(paging.get('def', 20),
                                                  ge=paging.get('min', 1),
                                                  le=paging.get('max', 1000)),
                           session: AsyncSession = Depends(get_db),
                           ) -> PaginatedResponse:
        """
            Поиск по всем текстовым полям основной таблицы
            с постраничным выводом результата
            input_valudation_chema None
            response_model PaginatedResponse[<>ReadRelation>]
        """
        try:
            result = await self.service.search_geans(search, similarity_threshold,
                                                     page, page_size, self.repo,
                                                     self.model, session)
            return result
        except Exception as e:
            logger.error(f'search_geans, {e}')
            raise HTTPException(status_code=501, detail=f'search_geans, {self.model.__name__}, {e}')

    async def search_geans_all(self,
                               search: str = Query(None, description="Поисковый запрос. "
                                                   "В случае пустого запроса будут "
                                                   "выведены все данные "),
                               similarity_threshold: float = Query(None, ge=0, le=1.0),
                               session: AsyncSession = Depends(get_db),
                               limit: int = 20  # ограничение что бы не подвесить сервер
                               ):
        """
            Поиск по всем текстовым полям основной таблицы БЕЗ пагинации
            input_valudation_chema <>CreateRelation
            response_model <>ReadRelation
        """
        try:
            result = await self.service.search_geans_all(search, similarity_threshold,
                                                         self.repo, self.model, session, limit)
            return result
            #  content = orjson.dumps(result)
            # return Response(content=content, media_type="application/json")
        except Exception as e:
            raise HTTPException(status_code=501, detail=f'search_geans_all, {self.model.__name__}, {e}')


class LightRouter:
    """
        минимальный роутер с зависимостями
    """

    def __init__(self, prefix: str, **kwargs):
        self.prefix = prefix
        self.tags = [prefix.replace('/', '')]
        include_in_schema = kwargs.get('include_in_schema', True)
        self.router = APIRouter(prefix=prefix,
                                tags=self.tags,
                                dependencies=[Depends(get_active_user_or_internal)],
                                include_in_schema=include_in_schema
                                )
        # self.session: AsyncSession = Depends(get_db)
        self.setup_routes()

    def setup_routes(self):
        """ override it as follows """
        self.router.add_api_route("", self.endpoints,
                                  methods=["POST"], response_model=self.create_schema)

    async def endpoint(self, request: Request):
        """ override it """
