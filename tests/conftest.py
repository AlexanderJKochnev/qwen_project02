# tests/conftest.py
import asyncio
import sys
from psycopg.errors import ForeignKeyViolation
from pydantic import BaseModel
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Any, Optional, Dict, Type
import pytest
from dateutil.relativedelta import relativedelta
from fastapi.routing import APIRoute
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger
import logging
from app.auth.models import User
from app.auth.utils import create_access_token, get_password_hash
from app.core.models.base_model import Base
from app.core.utils.common_utils import jprint
from app.main import app, get_db
from app.depends import get_translator_func
from app.mongodb.config import get_database, get_mongodb, MongoDB
# from app.mongodb.router import get_mongodb
from tests.config import settings_db
from tests.data_factory.fake_generator import generate_test_data
from tests.data_factory.reader_json import JsonConverter
from tests.utility.assertion import assertions
from tests.utility.data_generators import FakeData
from tests.utility.find_models import discover_models, discover_schemas2

# from tests.data_factory.fake_generator import generate_test_data

scope = 'session'
scope2 = 'session'
example_count = 5      # количество тестовых записей - рекомедуется >20 для paging test


@pytest.fixture(autouse=True)
def setup_test_logger():
    # 1. Удаляем все обработчики, настроенные в приложении (включая INFO из middleware)
    logger.remove()

    # 2. Добавляем новый обработчик только для уровня ERROR
    logger.add(sys.stderr, level="ERROR")

    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("httpcore").setLevel(logging.ERROR)

    yield  # После завершения теста можно ничего не делать или вернуть настройки


def get_model_by_name(name: str) -> Optional[Type[BaseModel]]:
    """
        получение pydantic модели по ее имени (для тестирования openapi_extra={'x-request-schema': ModelName)
    """
    def get_all_subclasses(cls):
        all_subclasses = []
        for subclass in cls.__subclasses__():
            all_subclasses.append(subclass)
            all_subclasses.extend(get_all_subclasses(subclass))
        return all_subclasses

    for cls in get_all_subclasses(BaseModel):
        if cls.__name__ == name:
            return cls
    return None
# ----------REAL IMAGE FIXTURES-----------


@pytest.fixture
def test_images_dir():
    """Возвращает путь к директории с тестовыми изображениями"""
    return Path(__file__).parent / "test_images"


@pytest.fixture
def todayutc():
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def pastutc():
    return (datetime.now(timezone.utc) - relativedelta(years=2)).isoformat()


@pytest.fixture()
def futureutc():
    return (datetime.now(timezone.utc) + relativedelta(years=2)).isoformat()


@pytest.fixture
def sample_image_paths(test_images_dir):
    """Возвращает пути ко всем тестовым изображениям"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    image_paths = []

    for file_path in test_images_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            image_paths.append(file_path)

    return image_paths


@pytest.fixture
def sample_image_jpg(test_images_dir):
    """Возвращает путь к конкретному JPG изображению"""
    jpg_path = test_images_dir / "sample.jpg"
    if jpg_path.exists():
        return jpg_path
    # Если файла нет, ищем любой JPG
    for file_path in test_images_dir.iterdir():
        if file_path.suffix.lower() in {'.jpg', '.jpeg'}:
            return file_path
    raise FileNotFoundError("No JPG images found in test directory")


# ----------MONGODB FIXTURES--------------
@pytest.fixture(scope="session")
async def test_mongodb(clean_database):
    """Создает тестовый экземпляр MongoDB"""
    test_mongo = MongoDB()
    test_url = f'{settings_db.mongo_url}'
    await test_mongo.connect(test_url, settings_db.MONGO_DATABASE)
    yield test_mongo
    await test_mongo.disconnect()


@pytest.fixture(scope="session")  # , autouse=True)
async def clean_database():
    """Очищает базу данных перед каждой сессией"""
    test_mongo = MongoDB()
    test_url = f'{settings_db.mongo_url}'
    await test_mongo.connect(test_url, settings_db.MONGO_DATABASE)
    if hasattr(test_mongo, 'database'):
        await test_mongo.client.drop_database(settings_db.MONGO_DATABASE)
        test_mongo.database = test_mongo.client[settings_db.MONGO_DATABASE]
    await test_mongo.disconnect()


@pytest.fixture(scope="function")
async def test_mongo_connection():
    """Фикстура для проверки прямого подключения к MongoDB"""
    try:
        client = AsyncIOMotorClient(settings_db.mongo_url, serverSelectionTimeoutMS=5000)
        await client.admin.command('ping')
        client.close()
        return True
    except Exception as e:
        pytest.fail(f"MongoDB connection failed: {e}")


@pytest.fixture(scope="function")
async def mongo_health_check(test_mongodb):
    """Проверка здоровья MongoDB подключения из приложения"""
    try:
        # Проверяем что можем выполнять команды
        await test_mongodb.client.admin.command('ping')
        return True
    except Exception as e:
        pytest.fail(f"MongoDB health check failed: {e}")


@pytest.fixture
async def test_client_with_mongo(test_mongodb):
    """Создает тестового клиента с переопределенными MongoDB зависимостями"""
    from app.main import app
    from app.mongodb.config import get_mongodb, get_database

    # Переопределяем зависимости для тестов
    async def override_get_mongodb():
        return test_mongodb

    async def override_get_database():
        return test_mongodb.database

    app.dependency_overrides[get_mongodb] = override_get_mongodb
    app.dependency_overrides[get_database] = override_get_database

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

# ---------------mongo db end ----------


def pytest_configure(config):
    config.option.log_cli_level = "CRITICAL"
    config.option.log_cli_format = "%(levelname)s - %(message)s"


@pytest.fixture(scope=scope)
def import_data() -> List[Dict]:
    """ конвертация архива """
    data = JsonConverter()()
    return list(data.values())


def get_routers(method: str = 'GET') -> List[APIRoute]:
    """  список роутеров, содержащих указанный метод """
    # prefix содердится в a.path
    exc_route = ('/', '/auth/token', '/wait')
    return [a for a in app.routes
            if all((isinstance(a, APIRoute), a.path not in exc_route)) and all((hasattr(a, 'methods'),
                                                                                method in a.methods))]


@pytest.fixture(scope=scope)
def exclude_routers() -> List[str]:
    """ список path prefixes of routes what shall be excluded from tests"""
    return ('/health', '/openapi', '/users', '/parser', '/rawdatas', '/auth/token',
            '/registry', "/codes", "/status", "/names", "/images",
            # "/items/hierarchy",
            # "/drinks/hierarchy",
            "/items/direct", "/api/mongo")


def sort_routes(routes: list[APIRoute], path_prefixes: list[str]) -> list[APIRoute]:
    def get_sort_key(route: APIRoute):
        path = route.path

        # Ищем индекс префикса в предоставленном кортеже/списке
        for index, prefix in enumerate(path_prefixes):
            # Важно: проверяем startswith
            if path.startswith(prefix):
                # Возвращаем (индекс_префикса, сам_путь)
                # Индекс гарантирует порядок из path_prefixes
                # Сам путь нужен для алфавитной сортировки внутри одного префикса
                return (index, path)

        # Если префикс не найден, возвращаем индекс за пределами списка
        return (len(path_prefixes), path)

    # Сортируем и возвращаем новый список
    return sorted(routes, key=get_sort_key)


@pytest.fixture(scope=scope)
def presort_routers() -> List[str]:
    """ список path prefixes router what shall be sorted
        для тестирования POST, UPDATE, DELETE
    """
    result = ('/items', '/drink',
              '/subregion', '/create/subregions', '/delete/subregions',
              '/region', '/create/regions', '/delete/regions',
              '/country', '/delete/country',
              '/subcategory', '/create/subcategory', '/delete/subcategory',
              '/category',
              '/foods', '/create/foods', '/delete/foods'
              '/superfoods')
    return result


def get_xxx_routes(method: str, exc_routers: List[str], pre_routers: List[str]) -> List[APIRoute]:
    """
        список роутеров, содержащих указанный метод
        отсортированный для групповой обработки
    """
    exc_route = ('/',)  # исключаем корень
    tmp = sort_routes([a for a in app.routes
                       if isinstance(a, APIRoute) and a.path not in exc_route and
                       method in a.methods and not any((a.path.startswith(x) for x in exc_routers))],
                      pre_routers)
    # if method in ['POST', 'PATCH']:
    #     return tmp[::-1]
    return tmp


@pytest.fixture(scope=scope)
def get_get_routes(exclude_routers, presort_routers) -> List[APIRoute]:
    return get_xxx_routes('GET', exclude_routers, presort_routers)


@pytest.fixture(scope=scope)
def get_post_routes(exclude_routers, presort_routers) -> List[APIRoute]:
    return get_xxx_routes('POST', exclude_routers, presort_routers)


@pytest.fixture(scope=scope)
def get_patch_routes(exclude_routers, presort_routers) -> List[APIRoute]:
    return get_xxx_routes('PATCH', exclude_routers, presort_routers)


@pytest.fixture(scope=scope)
def get_del_routes(exclude_routers, presort_routers) -> List[APIRoute]:
    return get_xxx_routes('DELETE', exclude_routers, presort_routers)


@pytest.fixture(scope=scope)
def get_all_routes(exclude_routers) -> List[APIRoute]:
    """  список роутеров, содержащих указанный метод """
    # prefix содерится в a.path
    # APIRoute(path='/registry/hierarchy', name='create_relation', methods=['POST'])
    exc_route = ('/',)
    return [a for a in app.routes
            if isinstance(a, APIRoute) and a.path not in exc_route and
            not any((a.path.startswith(x) for x in exclude_routers))]


@pytest.fixture(scope=scope)
def simple_router_list():
    """генератор тестовых данных 1
    """

    from app.support.category.router import CategoryRouter
    # from app.support.color.router import ColorRouter
    from app.support.country.router import CountryRouter
    # from app.support.customer.router import CustomerRouter
    from app.support.sweetness.router import SweetnessRouter
    from app.support.varietal.router import VarietalRouter
    from app.support.superfood.router import SuperfoodRouter   # noqa: F401
    from app.support.food.router import FoodRouter

    # generator = TestDataGenerator()
    # template = remove_id(json_reader())
    # return generator.generate(template, count=7)
    source = (CategoryRouter,
              CountryRouter,
              SuperfoodRouter,
              SweetnessRouter,
              VarietalRouter,
              FoodRouter,
              # StatusRouter,
              # RegistryRouter,
              # CodeRouter,
              # NameRouter,
              # RawdataRouter,
              # ImageRouter
              )
    return source


@pytest.fixture(scope=scope)
def complex_router_list():
    """ генератор тестовых данных 2"""
    from app.support.food.router import FoodRouter  # NOQA: F401
    from app.support.subcategory.router import SubcategoryRouter
    from app.support.region.router import RegionRouter
    from app.support.subregion.router import SubregionRouter
    # from app.support.warehouse.router import WarehouseRouter
    from app.support.drink.router import DrinkRouter
    from app.support.item.router import ItemRouter
    return (SubcategoryRouter,
            RegionRouter,
            SubregionRouter,
            # WarehouseRouter,
            DrinkRouter,
            ItemRouter,
            # ItemViewRouter
            )


@pytest.fixture(scope=scope)
def event_loop(request):
    """
    Создаём отдельный event loop для всей сессии тестов.
    Это предотвращает ошибку "Event loop is closed".
    """
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    try:
        yield loop
    finally:
        if not loop.is_closed():
            loop.close()
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_models():
    """Автоматически обнаруживает все модели для тестирования"""
    return discover_models()


@pytest.fixture(scope=scope)
def get_schemas(discovery_schemas):
    """only read schemas and paginated / delete responses
        получает словарь {schema_name: obj} и преобрузет в словарь
        {model_name:{'create': obj,
                     'update': obj,
                     'read': obj
                     }
        }
    """
    tmp = discover_schemas2(app)
    schemas = {}
    for name, obj in tmp.items():
        if name.endswith('Create'):
            model_name = name[:-6]
            if model_name not in schemas:
                schemas[model_name] = {}
            schemas[model_name]['create'] = obj
        elif name.endswith('Update'):
            model_name = name[:-6]
            if model_name not in schemas:
                schemas[model_name] = {}
            schemas[model_name]['update'] = obj
        elif name.endswith('Read'):
            model_name = name[:-4]
            if model_name not in schemas:
                schemas[model_name] = {}
            schemas[model_name]['read'] = obj
    return schemas


@pytest.fixture(scope=scope)
def discovery_schemas():
    return discover_schemas2(app)


@pytest.fixture(scope="session")
async def test_schemas(authenticated_client_with_db, test_db_session):
    client = authenticated_client_with_db
    schemas = {}
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    openapi = response.json()
    # Все компоненты (включая схемы)
    tmp = openapi["components"]["schemas"]
    for name, obj in tmp.items():
        if name.endswith('Create'):
            model_name = name[:-6]
            if model_name not in schemas:
                schemas[model_name] = {}
            schemas[model_name]['create'] = obj
        elif name.endswith('Update'):
            model_name = name[:-6]
            if model_name not in schemas:
                schemas[model_name] = {}
            schemas[model_name]['update'] = obj
        elif name.endswith('Read'):
            model_name = name[:-4]
            if model_name not in schemas:
                schemas[model_name] = {}
            schemas[model_name]['read'] = obj
    return schemas


@pytest.fixture(scope=scope)
def base_url():
    """ базовый url """
    return "http://testserver"


@pytest.fixture(scope=scope)
def get_fields_type() -> Dict[str, Any]:
    """
        Подготавливает спиcок имен полей и генераторов их значений для всех POST/PATCH
        маршрутов, отсортированных по очередности заполнения
        {
        route: /example,
        method: 'POST' | 'PATCH'
        model_name: 'DrinkCreate' (schema name)
        test_data {required_only: {field: generator ...},
                   all_fields: {field: generator ...}
        }
    """
    x = FakeData(app, 1)
    return x()


@pytest.fixture(scope=scope)
async def fakedata_generator(authenticated_client_with_db, test_db_session,
                             simple_router_list, complex_router_list):
    """ генератор тестовых данных """
    failed_cases = []
    source = simple_router_list + complex_router_list
    test_number = 5
    client = authenticated_client_with_db
    for n, item in enumerate(source):
        router = item()
        schema = router.create_schema_relation
        prefix = router.prefix
        test_data = generate_test_data(
            schema, test_number, {'int_range': (1, test_number), 'decimal_range': (0.5, 1), 'float_range': (0.1, 1.0),
                                  'faker_seed': 42}
        )
        for m, data in enumerate(test_data):
            try:
                _ = schema(**data)
            except Exception as e:
                if assertions(False, failed_cases, item, prefix, f'ошибка валидации: {e}'):
                    continue  # Продолжаем со следующим роутером
            try:
                response = await client.post(f'{prefix}/hierarchy', json=data)
                # if response.status_code not in [200, 201]:
                if assertions(response.status_code not in [200, 201],
                              failed_cases, item,
                              prefix, f'status_code {response.status_code}'):
                    jprint(data)
                    print('-------------------------------')
                    # assert response.status_code in [200, 201],
                    # f'{prefix}, {response.text}'
            except Exception as e:
                jprint(data)
                assert False, f'{e} {response.status_code} {prefix=}, {response.text}'
    if failed_cases:
        pytest.fail("Failed routers:\n" + "\n".join(failed_cases))


@pytest.fixture(scope=scope)
def routers_get() -> List[str]:
    """ список роутеров GET """
    return [x for x in get_routers('GET')]


@pytest.fixture(scope=scope)
def routers_get_one() -> List[str]:
    """ список роутеров GET get_by_id"""
    return [x.path for x in get_routers('GET')]


@pytest.fixture(scope=scope)
def routers_get_all() -> List[str]:
    """ список роутеров GET get_all"""
    return [x.path for x in get_routers('GET') if x.name == 'get']


@pytest.fixture(scope=scope)
def real_routers_get_all() -> List[APIRoute]:
    """ список роутеров GET get_all"""
    return [x for x in ('GET') if x.name == 'get']


@pytest.fixture(scope=scope)
def routers_post() -> List[str]:
    return [x for x in get_routers('POST')]


@pytest.fixture(scope=scope)
def routers_patch() -> List[str]:
    return [x.path for x in get_routers('PATCH')]


@pytest.fixture(scope=scope)
def routers_delete() -> List[str]:
    return [x.path for x in get_routers('DELETE')]


@pytest.fixture(scope=scope)
def test_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123"
    }


@pytest.fixture(scope=scope)
def super_user_data():
    return {"username": 'admin',
            "email": 'admin@example.com',
            "password": 'admin',
            "is_active": True,
            "is_superuser": True}


# ---- DATABASE MOCK ----
@pytest.fixture(scope=scope)
def mock_db_url():
    """URL для тестовой базы данных POPSTGRESQL"""
    # return "sqlite+aiosqlite:///:memory:"
    # return "postgresql+asyncpg://test_user:test@localhost:2345/test_db" этот драйвер не походит для тестирования
    st = settings_db
    se = (f"postgresql+psycopg_async://{st.POSTGRES_USER}:"
          f"{st.POSTGRES_PASSWORD}@{st.POSTGRES_HOST}:{st.PG_PORT}/{st.POSTGRES_DB}")
    print(se)
    return (se)


@pytest.fixture(scope=scope)
async def mock_engine(mock_db_url):
    """Создает асинхронный движок для тестовой базы данных"""
    engine = create_async_engine(
        mock_db_url,
        echo=False,
        # pool_pre_ping=True
        pool_pre_ping=False,  # ❗️ Отключите для async
        pool_recycle=3600,  # Вместо этого используйте pool_recycle
        pool_size=20, max_overflow=0  # !
    )
    # Создает все таблицы в базе данных
    async with engine.begin() as conn:
        # сбрасывает базу данных перед тестированием
        # await conn.run_sync(Base.metadata.drop_all, checkfirst=False, cascade=True)
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope=scope2)
async def test_db_session(mock_engine):
    """Создает сессию для тестовой базы данных"""
    AsyncSessionLocal = sessionmaker(
        bind=mock_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )
    # async with mock_engine.connect() as session:
    async with AsyncSessionLocal() as session:
        try:  # !
            yield session
            await session.commit()   # !
            # await session.close()
        except ForeignKeyViolation:
            pass
        except Exception:
            await session.rollback()  # Откат при ошибках
            raise


@pytest.fixture(scope=scope2)
async def create_test_user(test_db_session, test_user_data):
    """Создает тестового пользователя в базе данных"""
    # Создаем пользователя напрямую в БД
    hashed_password = get_password_hash(test_user_data["password"])
    db_user = User(
        username=test_user_data["username"],
        email=test_user_data["email"],
        hashed_password=hashed_password
    )
    test_db_session.add(db_user)
    # await test_db_session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
    await test_db_session.commit()
    await test_db_session.refresh(db_user)
    return db_user


@pytest.fixture(scope=scope2)
async def create_super_user(test_db_session, super_user_data):
    """Создает суперпользователя в базе данных"""
    hashed_password = get_password_hash(super_user_data["password"])
    db_user = User(
        username=super_user_data["username"],
        email=super_user_data["email"],
        is_superuser=super_user_data["is_superuser"],
        hashed_password=hashed_password
    )
    test_db_session.add(db_user)
    await test_db_session.commit()
    await test_db_session.refresh(db_user)
    return db_user
# --------FAST API ----------------------------


@pytest.fixture(scope=scope)
async def override_app_dependencies():
    """Фикстура для переопределения зависимостей приложения"""
    original_overrides = app.dependency_overrides.copy()
    yield app.dependency_overrides
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)


@pytest.fixture(scope=scope2)
async def get_test_db(test_db_session, create_test_user, create_super_user):
    """Dependency override для получения тестовой сессии БД"""
    yield test_db_session


@pytest.fixture(scope=scope2)
async def client(test_db_session, override_app_dependencies, get_test_db, base_url):
    """Базовый клиент без авторизации"""
    # Переопределяем зависимость get_db
    async def get_test_db():
        yield test_db_session
    app.dependency_overrides[get_db] = get_test_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=base_url
    ) as ac:
        yield ac


@pytest.fixture(scope=scope2)
async def authenticated_client_with_db(test_db_session, super_user_data,
                                       override_app_dependencies, base_url, get_test_db, test_mongodb):
    """ Аутентифицированный клиент с тестовой базой данных """
    # from app.main import app
    # from app.mongodb.config import get_mongodb, get_database
    async def get_test_db():
        yield test_db_session

    async def override_get_mongodb():
        return test_mongodb

    async def override_get_database():
        return test_mongodb.database

    async def override_get_translator_func(data: Dict[str, Any], flag: Optional[bool] = None):
        result: dict = {}
        for key, val in data.items():
            if isinstance(result, str):
                result[key] = f'{val} translated'
            else:
                result[key] = val
        return result

    # override_app_dependencies[app.dependency_overrides] = get_test_db
    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[get_mongodb] = override_get_mongodb
    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_translator_func] = lambda: override_get_translator_func

    # Создаем JWT токен для тестового пользователя
    token_data = {"sub": super_user_data["username"]}
    access_token = create_access_token(data=token_data)

    # Создаем клиент с токеном в заголовках
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=base_url,
        headers={"Authorization": f"Bearer {access_token}"}
    ) as ac:
        ac._test_user = super_user_data
        ac._test_user_db = create_super_user
        ac._access_token = access_token
        yield ac

# -----------data generator------------------
