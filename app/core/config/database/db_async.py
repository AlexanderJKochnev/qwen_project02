# app/core/config/database/db_async.py
# асинхронный драйвер
from sqlalchemy.ext.asyncio import (create_async_engine,
                                    async_sessionmaker,
                                    # AsyncEngine,
                                    AsyncSession)
from sqlalchemy import text
from app.core.config.database.db_config import settings_db


class DatabaseManager:
    engine = None
    session_maker = None

    @classmethod
    def init(cls):
        # Создаем Engine (Singleton)
        cls.engine = create_async_engine(settings_db.database_url,
                                         echo=settings_db.DB_ECHO_LOG,
                                         pool_pre_ping=True,
                                         pool_size=settings_db.POOL_SIZE,
                                         max_overflow=settings_db.MAX_OVERFLOW,
                                         pool_recycle=settings_db.POOL_RECYCLE
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


async def get_db():
    async with DatabaseManager.session_maker() as session:
        try:
            yield session
            # await session.commit()  # Опционально: автокоммит при успехе
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
