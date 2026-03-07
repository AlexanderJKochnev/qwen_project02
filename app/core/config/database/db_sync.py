# app/core/congig/database/db_sync.py
# синхронный драйвер
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config.database.db_config import settings_db

# 0. url для подключения
sync_database_url = settings_db.database_url.replace("postgresql+asyncpg://", "postgresql://")

#  1. Синхронный двигатель
engine_sync = create_engine(
    sync_database_url,
    echo=settings_db.DB_ECHO_LOG,
    pool_pre_ping=True,
)

# 2. Синхронная фабрика сессий
SessionLocalSync = sessionmaker(autocommit=False, autoflush=False, bind=engine_sync)
