# app.support.clickhouse.import_router.py
# app/api/routes/import_.py
from fastapi import APIRouter, Depends, BackgroundTasks
from loguru import logger
from app.support.clickhouse.dependencies import get_import_service
from app.support.clickhouse.import_service import ImportService
from app.support.clickhouse.parsers import PARSERS

router = APIRouter(prefix="/import", tags=["import"])

# Список файлов, которые лежат в /app/data
CSV_FILES = [
    ('beer_data.csv', PARSERS['beer_data.csv']),
    ('scotch_review.csv', PARSERS['scotch_review.csv']),
    ('spirits_data.csv', PARSERS['spirits_data.csv']),
    ('wine.csv', PARSERS['wine.csv']),
    ('wine_data.csv', PARSERS['wine_data.csv']),
    ('winemag-data-130k-v2.csv', PARSERS['winemag-data-130k-v2.csv']),
    ('winemag-data_first150k.csv', PARSERS['winemag-data_first150k.csv']),
]


@router.post("/csv")
async def import_csv(
    background_tasks: BackgroundTasks,
    import_service: ImportService = Depends(get_import_service)
):
    """Фоновый импорт всех CSV файлов из /app/data"""
    async def _import():
        for file_name, parser in CSV_FILES:
            # Для каждого файла своя сессия (тяжёлые запросы)
            try:
                await import_service.import_file(file_name, parser)
            except Exception as e:
                logger.error(f"Failed to import {file_name}: {e}")
        # После импорта выгружаем GPU модель
        from app.api.dependencies import get_embedding_service
        embedding_service = await get_embedding_service()
        embedding_service.unload_import_model()

    background_tasks.add_task(_import)

    return {"message": "Import started in background", "files": [f[0] for f in CSV_FILES]}


@router.get("/status")
async def import_status(
        import_service: ImportService = Depends(get_import_service)
):
    """Статус (можно расширить с сохранением состояния)"""
    return {"status": "idle"}
