# app/core/routers/image_router.py
# удалить
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.core.config.project_config import settings
import os


prefix = settings.IMAGES_PREFIX
router = APIRouter(prefix=f"/{prefix}", tags=[f"{prefix}"])


@router.get("/{filename}", openapi_extra={'x-request-schema': None})
async def get_image(filename: str):
    """Получить изображение по имени файла"""
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")

    # Проверяем, что файл находится в разрешенной директории
    if not os.path.abspath(file_path).startswith(os.path.abspath(settings.UPLOAD_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(file_path)
