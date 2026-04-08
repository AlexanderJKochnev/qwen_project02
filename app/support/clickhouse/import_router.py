# app.support.clickhouse.import_router.py
# app/api/routes/import_.py
from fastapi import APIRouter, Depends, BackgroundTasks

from app.support.clickhouse.dependencies import get_import_service
from app.support.clickhouse.import_service import ImportService
from app.support.clickhouse.parsers import PARSERS

router = APIRouter(prefix="/import", tags=["import"])

# Список файлов для импорта
CSV_FILES = [('data/beer_data.csv', PARSERS['beer_data.csv']), ('data/scotch_review.csv', PARSERS['scotch_review.csv']),
             ('data/spirits_data.csv', PARSERS['spirits_data.csv']), ('data/wine.csv', PARSERS['wine.csv']),
             ('data/wine_data.csv', PARSERS['wine_data.csv']),
             ('data/winemag-data-130k-v2.csv', PARSERS['winemag-data-130k-v2.csv']),
             ('data/winemag-data_first150k.csv', PARSERS['winemag-data_first150k.csv']), ]


@router.post("/csv")
async def import_csv(
        background_tasks: BackgroundTasks, import_service: ImportService = Depends(get_import_service)
):
    """Фоновый импорт всех CSV файлов"""

    async def _import():
        # Для каждого файла своя сессия (тяжёлые запросы)
        for file_path, parser in CSV_FILES:
            # Получаем свежий клиент для каждого файла
            from app.core.config.database.click_async import get_ch_session
            async with get_ch_session() as client:
                await import_service.import_file(file_path, parser, client)

        # После импорта выгружаем GPU модель
        from app.support.clickhouse.dependencies import get_embedding_service
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
