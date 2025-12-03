# app/rawdata_arq_worker.py
# Separate worker for processing Rawdata records - parsing HTML and updating field keys

import asyncio

import json
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import uuid
from app.core.config.database.db_config import settings_db
from app.core.config.project_config import settings
from app.support.parser.model import Rawdata, Status
from app.support.parser.utils.html_parser import parse_html_to_dict
from app.support.field_keys.service import FieldKeyService
from app.core.utils.email_sender import EmailSender, send_notification, NotificationType
from app.support.parser.repository import StatusRepository


# Настройка БД
engine = create_async_engine(settings_db.database_url, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
metrics = {
    'completed_tasks': 0
}
status_completed_id = None  # Cache the completed status ID


async def parse_all_rawdata_task(ctx, rawdata_id: int, status_completed_id: int):
    """
    Parse one Rawdata record, extract key-value pairs, store in parsed_data field,
    update field keys in the field_keys table, and set status to completed.
    """

    try:
        job_id = ctx.get("job_id")
        if not job_id:
            job_id = str(uuid.uuid4())

        async with asyncio.timeout(settings.ARQ_TASK_TIMEOUT):
            async with AsyncSessionLocal() as session:
                # Get one Rawdata record that has body_html (not processed yet)
                rawdata_record = await session.get(Rawdata, rawdata_id)
                if not rawdata_record:
                    print("No Rawdata records to process")
                    return {"status": "no_records"}
                print(f"Processing record with id {rawdata_record.id}")

                # Parse the HTML content
                parsed_dict, field_mapping = parse_html_to_dict(rawdata_record.body_html)

                # Store the parsed data as JSON in the parsed_data field
                if parsed_dict:
                    rawdata_record.parsed_data = json.dumps(parsed_dict, ensure_ascii=False, indent=2)

                # Process field keys and update the field_keys table
                for short_name, full_name in field_mapping.items():
                    # Truncate short_name to 25 characters if needed
                    if len(short_name) > 25:
                        short_name = short_name[:25]

                    # Create or update field key
                    field_key_service = FieldKeyService(session)
                    await field_key_service.get_or_create_field_key(
                        short_name=short_name,
                        full_name=full_name
                    )

                # Update status to completed
                rawdata_record.status_id = status_completed_id

                # Commit changes for this record
                await session.commit()

                print(f"Successfully processed Rawdata record with id {rawdata_record.id}")

                return {"status": "success", "record_id": rawdata_record.id}

    except Exception as e:
        print(f"Error processing Rawdata record: {str(e)}")
        # Don't commit the changes if there was an error
        # The record status will remain unchanged
        await send_notification(
            f"Rawdata processing воркер (№2) остановлен с ошибкой",
            notification_type=NotificationType.ERROR,
            additional_info=f'Error processing Rawdata record: {str(e)}, job_id: {job_id}',
            worker_name="Rawdata Processing Worker"
        )
        raise  # Re-raise the exception so ARQ can handle retries


async def on_startup_handle(ctx):
    global status_completed_id
    ctx['metrics'] = metrics

    # Initialize the completed status ID at startup
    async with AsyncSessionLocal() as session:
        status_completed = await StatusRepository.get_by_fields({"status": "completed"}, Status, session)
        if status_completed:
            status_completed_id = status_completed.id
        else:
            print("Warning: 'completed' status not found in database")

    print(
        f"Rawdata processing воркер запущен. Начальное количество задач:"
        f" {ctx['metrics']['completed_tasks']}, status_completed_id: {status_completed_id}")


async def on_job_post_run_handle(ctx):
    # Увеличиваем счетчик
    ctx['metrics']['completed_tasks'] += 1
    # Выводим текущее значение счетчика в консоль
    count = ctx['metrics']['completed_tasks']
    print(f"[{ctx['job_id']}] Задача завершена. Всего выполнено задач воркером Rawdata processing"
          f" : {count}")


# Хук вызывается при остановке процесса воркера
async def on_shutdown_handle(ctx):
    count = ctx['metrics']['completed_tasks']
    print(f"Rawdata processing воркер остановлен. Всего выполнено задач: {count}")
    await send_notification(
        f"Rawdata processing воркер (№2) успешно завершил работу",
        notification_type=NotificationType.SHUTDOWN,
        additional_info=f"Rawdata processing воркер остановлен. Всего выполнено задач: {count}",
        worker_name="Rawdata Processing Worker"
    )




# Класс настроек (согласно документации arq) для Rawdata processing worker


class RawdataWorkerSettings:
    functions = [parse_all_rawdata_task]
    queue_name = 'parse_all_rawdata_queue'  # Separate queue for this worker
    host = settings.REDIS_HOST
    port = settings.REDIS_PORT
    redis_settings = RedisSettings(host=host, port=port)
    conn_timeout = 10,  # таймаут подключения
    conn_retries = 5,  # попытки переподключения
    conn_retry_delay = 1,  # задержка между попытками
    on_startup = on_startup_handle
    on_shutdown = on_shutdown_handle
    on_job_end = on_job_post_run_handle
    max_tries = settings.ARQ_MAX_TRIES  # 3 попытки, потом — не повторять
    burst = True  # Stop worker when queue is empty
