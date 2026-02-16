# app/core/config/database/db_async.py
# асинхронный драйвер
from sqlalchemy.ext.asyncio import (create_async_engine,
                                    async_sessionmaker,
                                    # AsyncEngine,
                                    AsyncSession)
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from loguru import logger
from app.core.config.database.db_config import settings_db


class DatabaseManager:
    engine = None
    session_maker = None
    connection_string = None

    @classmethod
    def __init__(cls):
        cls.connection_string = settings_db.database_url
        # Создаем Engine (Singleton)
        cls.engine = create_async_engine(settings_db.database_url,
                                         echo=settings_db.DB_ECHO_LOG,
                                         poolclass=NullPool,
                                         # ВАЖНО: отключаем встроенный пул SQLAlchemy
                                         connect_args={"options": "-c statement_timeout=30000"}
                                         # Опционально: таймаут 30 сек
                                         # все что ниже только для прямого соединения
                                         # pool_pre_ping=True,
                                         # pool_size=settings_db.POOL_SIZE,
                                         # max_overflow=settings_db.MAX_OVERFLOW,
                                         # pool_recycle=settings_db.POOL_RECYCLE
                                         )

        # Создаем фабрику сессий
        cls.session_maker = async_sessionmaker(
            bind=cls.engine,
            expire_on_commit=False,
            class_=AsyncSession,
            autoflush=False
        )

    @classmethod
    async def close(cls):
        if cls.engine:
            await cls.engine.dispose()

    @classmethod
    async def check_connection(cls):
        """Проверка физического соединения с БД"""
        if cls.session_maker is None:
            raise RuntimeError("DatabaseManager не инициализирован! Вызовите init() сначала.")

        async with cls.session_maker() as session:
            try:
                # Выполняем простейший запрос
                await session.execute(text("SELECT 1"))
                return True
            except Exception as e:
                logger.error(f"PostgreSQL Connection Error: {e}")
                raise e


async def get_db():
    async with DatabaseManager.session_maker() as session:
        try:
            yield session
            await session.commit()  # Опционально: автокоммит при успехе
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db_extensions():
    """Инициализация расширений PostgreSQL"""
    async with DatabaseManager.session_maker() as session:
        # Установка расширения pg_trgm, если оно еще не установлено
        await session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        await session.commit()
