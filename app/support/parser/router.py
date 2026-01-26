# app/support/parser/router.py
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError
from sqlalchemy import select, and_
import asyncio
from fastapi import Depends, Query, HTTPException
from typing import Optional
from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter, LightRouter
from app.core.schemas.base import PaginatedResponse
from app.support.parser.model import Code, Name, Image, Rawdata, Status, Registry
from app.support.parser import schemas
from app.support.parser.service import RawdataService
from app.support.parser.orchestrator import ParserOrchestrator
from app.support.parser.repository import StatusRepository, RawdataRepository
from app.core.config.database.db_async import DatabaseManager
from app.core.utils.exception_handler import ValidationError_handler

background_tasks = set()  # чтобы ссылка не удалилась


class OrchestratorRouter(LightRouter):
    def __init__(self):
        super().__init__(prefix='/parser', include_in_schema=False)

    def setup_routes(self):
        self.router.add_api_route(
            "", self.endpoints, methods=["POST"])  # , response_model=self.create_schema)
        self.router.add_api_route("/name", self.parse_names_endpoint, methods=["POST"])
        self.router.add_api_route("/raw", self.parse_raw_endpoint, methods=["POST"])
        # self.router.add_api_route("/raw/backgound", self.start_background_parsing, methods=["POST"])
        # self.router.add_api_route("/raw/enqueue", self.enqueue_raw_parsing, methods=['POST'])
        self.router.add_api_route("/raw/frap-parse", self.enqueue_all_raw_parsing, methods=['POST'])
        self.router.add_api_route("/raw/frap-encoding", self.enqueue_single_rawdata_parsing, methods=['POST'])

    async def endpoints(self, shortname: str = None, url: str = None,
                        session: AsyncSession = Depends(get_db)):
        """
            получение кодов ФРАП
        """
        orchestrator = ParserOrchestrator(session)
        result = await orchestrator.run(shortname=shortname, url=url)
        if result["status"] == "alreadycompleted":
            # Тут можно вернуть 409 Conflict или предложить "force"
            return {"detail": result["message"], "action": "Повторить обработку? Используйте ?force=true"}
        return result

    async def parse_names_endpoint(
        self,
        max_pages: Optional[int] = Query(None,
                                         description="Макс. кол-во страниц для обработки (для тестов)"),
        code_id: Optional[int] = None, session: AsyncSession = Depends(get_db)
    ):
        """
            получение наименований продукции зарегистрированной в ФРАП
        """
        # Если code_id не задан — берем первую запись со статусом != 'completed'
        if code_id is None:
            status_completed = await StatusRepository.get_by_fields({"status": "completed"}, Status, session)
            stmt = select(Code)
            if status_completed:
                stmt = stmt.where(Code.status_id != status_completed.id)
            stmt = stmt.order_by(Code.id).limit(1)
            result = await session.execute(stmt)
            code = result.scalar_one_or_none()
            if not code:
                return {"error": "Нет необработанных записей в Code"}
        else:
            code = await session.get(Code, code_id)
            if not code:
                return {"error": "Code not found"}

        registry = await session.get(Registry, code.registry_id)
        if not registry:
            return {"error": "Registry not found"}

        orchestrator = ParserOrchestrator(session)
        result = await orchestrator.parse_names_from_code(code, registry, max_pages=max_pages)

        return {"code_id": code.id, "result": result}

    async def parse_raw_endpoint(self,
                                 name_id: Optional[int] = Query(
                                     None, description="ID записи Name. "
                                                       "Если не указан — обрабатывается первая "
                                                       "незавершённая."
                                 ), session: AsyncSession = Depends(get_db)
                                 ):
        """
        получение инфорации о продукции по id (не используется)
        """
        if name_id is not None:
            name = await session.get(Name, name_id)
            if not name:
                return {"error": "Name not found"}
        else:
            # Берём первую запись Name со статусом != completed
            status_completed = await StatusRepository.get_by_fields(
                {"status": "completed"}, Status, session
            )
            stmt = select(Name)
            if status_completed:
                stmt = stmt.where(Name.status_id != status_completed.id)
            stmt = stmt.order_by(Name.id).limit(1)
            result = await session.execute(stmt)
            name = result.scalar_one_or_none()
            if not name:
                return {"error": "No unprocessed Name records found"}

        orchestrator = ParserOrchestrator(session)
        result = await orchestrator.parse_rawdata_from_name(name)
        return result

    async def start_background_parsing(self, session: AsyncSession = Depends(get_db)):

        orchestrator = ParserOrchestrator(session)
        """
            Это не production-ready для долгих задач (при рестарте приложения задача прервётся).
            Для продакшена — использовать Celery + Redis/RabbitMQ или arq.
        """
        async def run():
            result = await orchestrator.process_all_names_in_background()
            print("Background parsing finished:", result)

        task = asyncio.create_task(run())
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

        return {"message": "Background parsing started"}

    async def enqueue_raw_parsing(self, name_id: int):
        from arq import create_pool
        from arq.connections import RedisSettings
        from app.core.config.project_config import settings
        redis = await create_pool(RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT))
        job = await redis.enqueue_job('parse_rawdata_task', name_id, _queue_name='parse_rawdata_queue')
        return {"job_id": job.job_id}

    async def enqueue_all_raw_parsing(self):
        """
            парсинг данных ФРАП
        """
        from arq import create_pool
        from arq.connections import RedisSettings
        from app.core.config.project_config import settings
        redis = await create_pool(RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT))
        async with DatabaseManager.session_maker() as session:
            status_completed = await session.execute(select(Status).where(Status.status == "completed"))
            status_completed = status_completed.scalar_one_or_none()
            query = select(Name.id)
            if status_completed:
                query = query.where(Name.status_id != status_completed.id)
            names = await session.execute(query)
            for (name_id,) in names:
                await redis.enqueue_job('parse_rawdata_task', name_id, _queue_name='parse_rawdata_queue')
        return {"message": "All raw parsing jobs enqueued"}

    async def enqueue_single_rawdata_parsing(self):
        """
            декдирование даннных ФРАП
        """
        from arq import create_pool
        from arq.connections import RedisSettings
        from app.core.config.project_config import settings
        redis = await create_pool(RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT))
        async with DatabaseManager.session_maker() as session:
            # Get the completed status ID properly
            status_completed = await session.execute(select(Status).where(Status.status == "completed"))
            status_completed = status_completed.scalar_one_or_none()
            if status_completed:
                status_completed_id = status_completed.id
            else:
                # If completed status doesn't exist, we can't proceed
                return {"error": "Completed status not found in database"}

            query = select(Rawdata.id)
            query = query.where(and_(Rawdata.status_id != status_completed_id,
                                     Rawdata.body_html.isnot(None)))
            rawdata = await session.execute(query)
            for (rawdata_id,) in rawdata:
                await redis.enqueue_job('parse_all_rawdata_task',
                                        rawdata_id, status_completed_id, _queue_name='parse_all_rawdata_queue')
        return {"message": "All raw decoding jobs enqueued"}


class RegistryRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=Registry,
            prefix="/registry", include_in_schema=False
        )

    async def create(self, data: schemas.RegistryCreate,
                     session: AsyncSession = Depends(get_db)) -> schemas.RegistryCreateResponseSchema:
        return await super().create(data, session)

    async def patch(self, id: int,
                    data: schemas.CodeUpdate,
                    session: AsyncSession = Depends(get_db)) -> schemas.CodeCreateResponseSchema:
        return await super().patch(id, data, session)

    async def create_relation(self, data: schemas.RegistryCreateRelation,
                              session: AsyncSession = Depends(get_db)):  # -> schemas.RegistryCreateResponseSchema:
        # result = await super().create_relation(data, session)
        result = await self.create(data, session)
        return result


class CodeRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=Code,
            prefix="/codes", include_in_schema=False
        )

    async def create(self, data: schemas.CodeCreate,
                     session: AsyncSession = Depends(get_db)) -> schemas.CodeCreateResponseSchema:
        return await super().create(data, session)

    async def patch(self, id: int,
                    data: schemas.CodeUpdate,
                    session: AsyncSession = Depends(get_db)) -> schemas.CodeCreateResponseSchema:
        return await super().patch(id, data, session)

    async def create_relation(self, data: schemas.CodeCreateRelation,
                              session: AsyncSession = Depends(get_db)) -> schemas.CodeRead:
        result = await super().create_relation(data, session)
        return result


class StatusRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=Status,
            prefix="/status", include_in_schema=False
        )

    async def create(self, data: schemas.StatusCreate,
                     session: AsyncSession = Depends(get_db)) -> schemas.StatusCreateResponseSchema:
        return await super().create(data, session)

    async def patch(self, id: int,
                    data: schemas.StatusUpdate,
                    session: AsyncSession = Depends(get_db)) -> schemas.StatusCreateResponseSchema:
        return await super().patch(id, data, session)

    async def create_relation(self, data: schemas.StatusCreateRelation,
                              session: AsyncSession = Depends(get_db)) -> schemas.StatusRead:
        result = await super().create_relation(data, session)
        return result


class NameRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=Name,
            prefix="/names", include_in_schema=False
        )

    async def create(self, data: schemas.NameCreate,
                     session: AsyncSession = Depends(get_db)) -> schemas.NameCreateResponseSchema:
        return await super().create(data, session)

    async def patch(self, id: int,
                    data: schemas.NameUpdate,
                    session: AsyncSession = Depends(get_db)) -> schemas.NameCreateResponseSchema:
        return await super().patch(id, data, session)

    async def create_relation(self, data: schemas.NameCreateRelation,
                              session: AsyncSession = Depends(get_db)) -> schemas.NameRead:
        result = await super().create_relation(data, session)
        return result


class RawdataRouter(BaseRouter):

    def __init__(self):
        super().__init__(
            model=Rawdata,
            prefix="/rawdatas", include_in_schema=False
        )

    def setup_routes(self):
        self.router.add_api_route(
            "/searchtfs",
            self.search_fts, methods=["GET"],
            response_model=PaginatedResponse[schemas.RawdataRead]
        )
        super().setup_routes()

    async def create(self, data: schemas.RawdataCreate,
                     session: AsyncSession = Depends(get_db)) -> schemas.RawdataCreateResponseSchema:
        return await super().create(data, session)

    async def patch(self, id: int,
                    data: schemas.RawdataUpdate,
                    session: AsyncSession = Depends(get_db)) -> schemas.RawdataCreateResponseSchema:
        return await super().patch(id, data, session)

    async def create_relation(self, data: schemas.RawdataCreateRelation,
                              session: AsyncSession = Depends(get_db)) -> schemas.RawdataRead:
        result = await super().create_relation(data, session)
        return result

    async def search_fts(self,
                         search_str: str = Query(
                             None, description="Поисковый запрос "
                             "(при отсутствии значения - выдает все записи)"),
                         page: int = Query(1, ge=1, description="Номер страницы"),
                         page_size: int = Query(15, ge=1, le=100, description="Размер страницы"),
                         session: AsyncSession = Depends(get_db)) -> PaginatedResponse[schemas.RawdataRead]:
        """Поиск элементов с использованием триграммного индекса в связанной модели Drink"""
        try:
            result = await RawdataService.search_fts(search_str,
                                                     RawdataRepository,
                                                     self.model, session, page, page_size)
            return result
        except ValidationError as exc:
            err = ValidationError_handler(exc)
            raise HTTPException(status_code=422, detail=err)


class ImageRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=Image,
            prefix="/images", include_in_schema=False
        )

    async def create(self, data: schemas.ImageCreate,
                     session: AsyncSession = Depends(get_db)) -> schemas.ImageCreateResponseSchema:
        return await super().create(data, session)

    async def patch(self, id: int,
                    data: schemas.ImageUpdate,
                    session: AsyncSession = Depends(get_db)) -> schemas.ImageCreateResponseSchema:
        return await super().patch(id, data, session)

    async def create_relation(self, data: schemas.ImageCreateRelation,
                              session: AsyncSession = Depends(get_db)) -> schemas.ImageRead:
        result = await super().create_relation(data, session)
        return result
