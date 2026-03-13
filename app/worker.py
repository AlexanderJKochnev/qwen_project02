# app/support/worker.py

# from arq import create_pool
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config.database.db_config import settings_db
from app.support.parser.orchestrator import ParserOrchestrator
from app.support.parser.model import Name
from app.core.config.project_config import settings

# Глобальные настройки
engine = create_async_engine(settings_db.database_url, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def parse_rawdata_task(ctx, name_id: int):
    async with AsyncSessionLocal() as session:
        name = await session.get(Name, name_id)
        if not name:
            return {"status": "error", "reason": "Name not found"}
        orchestrator = ParserOrchestrator(session)
        success = await orchestrator._fill_rawdata_for_name(name)
        if success:
            await session.commit()
            return {"status": "success", "name_id": name_id}
        else:
            await session.rollback()
            return {"status": "failed", "name_id": name_id}


# Обязательные для arq переменные
functions = [parse_rawdata_task]


def redis_settings():
    return RedisSettings(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


# Queue name for this worker's tasks
queue_name = 'parse_rawdata_queue'
