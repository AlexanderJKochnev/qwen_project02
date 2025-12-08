# app/main.py
# from sqlalchemy.exc import SQLAlchemyError
import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from app.auth.routers import auth_router, user_router
from app.core.config.database.db_async import engine, get_db, init_db_extensions  # noqa: F401
from app.mongodb.config import get_mongodb, MongoDB  # close_mongo_connection, connect_to_mongo
from app.mongodb.router import router as MongoRouter
from app.preact.create.router import CreateRouter
from app.preact.get.router import GetRouter
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
from app.arq_worker_routes import router as ArqWorkerRouter
# from app.support.warehouse.router import WarehouseRouter

# from sqladmin import Admin
# from app.middleware.auth_middleware import AuthMiddleware
# from app.admin import sqladm

# from app.core.routers.image_router import router as image_router
# from app.core.security import get_current_active_user

# from app.admin.auth import authentication_backend

logging.basicConfig(level=logging.WARNING)  # в начале main.py или conftest.py

app = FastAPI(title="Hybrid PostgreSQL-MongoDB API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

app.include_router(ArqWorkerRouter)
app.include_router(auth_router)
app.include_router(user_router)


@app.get("/")
async def read_root():
    return {"message": "Hybrid PostgreSQL (auth) + MongoDB (files) API"}


@app.get("/health")
async def health_check(mongodb_instance: MongoDB = Depends(get_mongodb)):
    status_info = {"status": "healthy",
                   "mongo_connected": mongodb_instance.client is not None,
                   "mongo_operational": False}

    if mongodb_instance.client:
        try:
            await mongodb_instance.client.admin.command('ping')
            status_info["mongo_operational"] = True
        except Exception:
            status_info["status"] = "degraded"

    return status_info


@app.on_event("startup")
async def startup_event():
    await init_db_extensions()


@app.on_event("shutdown")
async def shutdown_event():
    mongodb_instance = await get_mongodb()
    await mongodb_instance.disconnect()
    await engine.dispose()
