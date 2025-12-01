# app/arq_worker.py

import asyncio
import os
from requests.exceptions import HTTPError
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import uuid
from app.core.config.database.db_config import settings_db
from app.core.config.project_config import settings
from app.support.parser.orchestrator import ParserOrchestrator
from app.support.parser.model import Name
from app.support.parser.service import TaskLogService
from app.core.utils.loggers import smooth_delay
from app.core.utils.email_sender import EmailSender


# Настройка БД
engine = create_async_engine(settings_db.database_url, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
min_delay = settings.ARQ_MIN_DELAY
max_delay = settings.ARQ_MIN_DELAY
Y = 2


async def parse_rawdata_task(ctx, name_id: int):
    job_id = ctx.get("job_id")
    if not job_id:
        job_id = str(uuid.uuid4())

    # Initialize task_log_id to None to ensure it's always defined
    task_log_id = None
    
    # Create session for logging the task start
    try:
        async with AsyncSessionLocal() as session:
            # Создаём запись о старте в TaskLog
            task_log_id = await TaskLogService.add_with_session(
                task_name="parse_rawdata_task",
                job_id=job_id,
                name_id=name_id,
                session=session
            )
            await session.commit()
    except Exception as e:
        # If we can't create the initial task log, we still need to report the error
        print(f"Failed to create initial task log: {e}")
        # Continue with task execution even if logging failed
        pass
    
    await smooth_delay()

    try:
        async with asyncio.timeout(settings.ARQ_TASK_TIMEOUT):
            async with AsyncSessionLocal() as session:
                name = await session.get(Name, name_id)
                if not name:
                    raise ValueError("Name not found")
                orchestrator = ParserOrchestrator(session)
                success = await orchestrator._fill_rawdata_for_name(name)
                if success:
                    await session.commit()
                else:
                    await session.rollback()
                    raise RuntimeError("Failed to fill rawdata")

                # Update task log on success if task_log_id is available
                if task_log_id:
                    async with AsyncSessionLocal() as log_session:
                        await TaskLogService.update_with_session(
                            task_log_id, 'success', None, session=log_session
                        )
                        await log_session.commit()

    except HTTPError as e:
        # Update task log on failure if task_log_id is available
        if task_log_id:
            async with AsyncSessionLocal() as log_session:
                await TaskLogService.update_with_session(
                    task_log_id, 'failed', str(e.response.status_code), session=log_session
                )
                await log_session.commit()
        await send_error_notification(str(e.response.status_code))
        os._exit(1)
    except RuntimeError as e:
        # Update task log on failure if task_log_id is available
        if task_log_id:
            async with AsyncSessionLocal() as log_session:
                await TaskLogService.update_with_session(
                    task_log_id, 'failed', str(e), session=log_session
                )
                await log_session.commit()
        await send_error_notification(str(e))
        os._exit(1)
    except Exception as e:
        # Update task log on failure if task_log_id is available
        if task_log_id:
            async with AsyncSessionLocal() as log_session:
                await TaskLogService.update_with_session(
                    task_log_id, 'failed', str(e), session=log_session
                )
                await log_session.commit()
        await send_error_notification(str(e))
        os._exit(1)


# Класс настроек (согласно документации arq)
class WorkerSettings:
    functions = [parse_rawdata_task]
    host = settings.REDIS_HOST
    port = settings.REDIS_PORT
    redis_settings = RedisSettings(host=host, port=port)
    conn_timeout = 10,  # таймаут подключения
    conn_retries = 5,  # попытки переподключения
    conn_retry_delay = 1,  # задержка между попытками
    on_startup = None
    on_shutdown = None
    max_tries = settings.ARQ_MAX_TRIES  # 3 попытки, потом — не повторять


async def send_error_notification(error_message: str):
    """
    Отправляет уведомление об ошибке на email
    """
    email_sender = EmailSender()
    to_email = settings.EMAIL_ADMIN  # Email address to send error notifications to
    subject = "Ошибка воркера ARQ"
    body = f"Произошла ошибка при выполнении задачи воркера ARQ:\n\n{error_message}"

    await email_sender.send_email(to_email, subject, body)
