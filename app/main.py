# app/main.py
import httpx
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from loguru import logger
import sys
from time import perf_counter
from app.auth.routers import auth_router, user_router
# from app.core.config.project_config import settings
from app.core.config.database.db_async import DatabaseManager, init_db_extensions
from app.core.config.database.db_mongo import MongoDBManager, get_mongodb
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.mongodb.router import router as MongoRouter
from app.preact.create.router import CreateRouter
from app.preact.get.router import GetRouter
from app.preact.read.router import ReadRouter
from app.preact.delete.router import DeleteRouter
from app.preact.handbook.router import HandbookRouter
from app.preact.patch.router import PatchRouter
from app.support.api.router import ApiRouter
# -------ИМПОРТ РОУТЕРОВ----------
from app.support.category.router import CategoryRouter
from app.support.country.router import CountryRouter
# from app.support.customer.router import CustomerRouter
from app.support.drink.router import DrinkRouter
from app.support.food.router import FoodRouter
from app.support.item.router import ItemRouter
from app.support.item.router_item_view import ItemViewRouter
from app.support.region.router import RegionRouter
from app.support.subcategory.router import SubcategoryRouter
from app.support.subregion.router import SubregionRouter
from app.support.superfood.router import SuperfoodRouter
# from app.support.color.router import ColorRouter
from app.support.sweetness.router import SweetnessRouter
from app.support.varietal.router import VarietalRouter
from app.support.parser.router import (StatusRouter, CodeRouter, NameRouter, OrchestratorRouter,
                                       ImageRouter, RawdataRouter, RegistryRouter)
# from app.arq_worker_routes import router as ArqWorkerRouter
# from app.support.warehouse.router import WarehouseRouter
from app.core.config.database.meili_async import MeiliManager
# Import background tasks
from app.core.utils.background_tasks import init_background_tasks, stop_background_tasks
from app.core.services.meili_service import ItemMeiliService
from app.core.config.database.db_async import get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
    timeout = httpx.Timeout(10.0, connect=5.0)
    app.state.http_client = httpx.AsyncClient(
        http2=True, limits=limits, timeout=timeout, trust_env=False
        # Ускоряет работу, если не нужны системные прокси
    )
    DatabaseManager.init()
    await MeiliManager.get_client()
    # Можно сразу проверить соединение (healthcheck)
    await (await MeiliManager.get_client()).health()

    await MongoDBManager.connect()  # Подключаем Mongo
    # await init_db_extensions()  # подключение расщирений Postgresql

    # Initialize Meilisearch indexes
    async for db_session in get_db():
        item_meili_service = ItemMeiliService()
        meili_client = await MeiliManager.get_client()
        await item_meili_service.init_index(meili_client, db_session)
        break  # We just need one iteration to get the session

    # Initialize background tasks including MeiliSearch sync
    await init_background_tasks()

    yield

    # --- SHUTDOWN ---
    await stop_background_tasks()
    await app.state.http_client.aclose()
    await DatabaseManager.close()
    await MeiliManager.disconnect()
    await MongoDBManager.disconnect()


app = FastAPI(title="Hybrid PostgreSQL-MongoDB API",
              lifespan=lifespan,
              swagger_ui_parameters={
                  "docExpansion": "none",  # Сворачивает всё: и теги, и операции
                  "deepLinking": True,  # Позволяет копировать ссылки на конкретные методы
                  "filter": True  # Полезный бонус: добавляет строку поиска в Swagger
              }
              )

logger.remove()  # Удаляем стандартный обработчик
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    enqueue=True  # ВАЖНО: делает логирование неблокирующим (использует очередь)
)
logger.add("logs/app.log", rotation="500 MB", retention="10 days", compression="zip", enqueue=True)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = perf_counter()

    # Логируем начало запроса {потом убрать из prod - bootleneck}
    logger.info(f"Начало запроса: {request.method} {request.url.path}")

    response = await call_next(request)

    process_time = (perf_counter() - start_time) * 1000
    formatted_process_time = "{0:.2f}".format(process_time)

    # Логируем завершение и время выполнения
    logger.info(
        f"Завершено: {request.method} {request.url.path} | Статус: {response.status_code} | "
        f"Время: {formatted_process_time}мс"
    )

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "http://abc8888.ru",
        "https://abc8888.ru",
        "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)  # минимальный размер для сжатия

app.include_router(ApiRouter().router)
app.include_router(MongoRouter)
app.include_router(HandbookRouter().router)
app.include_router(CreateRouter().router)
app.include_router(GetRouter().router)
app.include_router(ReadRouter().router)
app.include_router(DeleteRouter().router)
app.include_router(PatchRouter().router)
app.include_router(ItemViewRouter().router)
app.include_router(ItemRouter().router)
app.include_router(DrinkRouter().router)

app.include_router(CategoryRouter().router)
app.include_router(SubcategoryRouter().router)
app.include_router(CountryRouter().router)
app.include_router(RegionRouter().router)
app.include_router(SubregionRouter().router)
app.include_router(SweetnessRouter().router)
app.include_router(FoodRouter().router)
app.include_router(SuperfoodRouter().router)
app.include_router(VarietalRouter().router)
app.include_router(StatusRouter().router)
app.include_router(CodeRouter().router)
app.include_router(NameRouter().router)
app.include_router(ImageRouter().router)
app.include_router(RawdataRouter().router)
app.include_router(RegistryRouter().router)
app.include_router(OrchestratorRouter().router)
# app.include_router(CustomerRouter().router)
# app.include_router(WarehouseRouter().router)

# app.include_router(ArqWorkerRouter)
app.include_router(auth_router)
app.include_router(user_router)


@app.get("/")
async def read_root():
    return {"message": "Hybrid PostgreSQL (auth) + MongoDB (files) API"}


@app.get("/health")
async def health_check(mongo_db: AsyncIOMotorDatabase = Depends(get_mongodb)):
    status_info = {"status": "healthy",
                   "mongo_connected": mongo_db is not None,
                   "mongo_operational": False}

    if mongo_db is not None:
        try:
            await mongo_db.command('ping')
            status_info["mongo_operational"] = True
        except Exception:
            status_info["status"] = "degraded"

    return status_info
