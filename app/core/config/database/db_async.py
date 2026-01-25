# app/core/config/database/db_async.py
# асинхронный драйвер
from sqlalchemy.ext.asyncio import (create_async_engine,
                                    async_sessionmaker,
                                    AsyncEngine,
                                    AsyncSession)
from sqlalchemy import text
from app.core.config.database.db_config import settings_db

# 1.    Асинхронный двигатель
engine: AsyncEngine = create_async_engine(settings_db.database_url,
                                          echo=settings_db.DB_ECHO_LOG,
                                          pool_pre_ping=True,
                                          pool_size=settings_db.POOL_SIZE,
                                          max_overflow=settings_db.MAX_OVERFLOW,
                                          pool_recycle=settings_db.POOL_RECYCLE
                                          )


async def init_db_extensions():
    """Инициализация расширений PostgreSQL"""
    async with AsyncSessionLocal() as session:
        # Установка расширения pg_trgm, если оно еще не установлено
        await session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        await session.commit()


# 2. Фабрика асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# 3. Зависимость для внедроения в routes


async def get_db():
    async with AsyncSessionLocal() as session:
        # await session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        yield session
