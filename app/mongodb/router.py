# app/mongodb/router.py
import io
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, status, UploadFile
from fastapi.responses import StreamingResponse, Response
from app.auth.dependencies import get_active_user_or_internal
from app.core.config.project_config import settings
from app.core.utils.common_utils import back_to_the_future, delta_data
from app.mongodb.models import FileListResponse, ImageCreateResponse, DirectUploadResponse
from app.mongodb.service import ThumbnailImageService
# from app.core.cache import cache_key_builder, invalidate_cache  #  потом может быть закэшируем

prefix = settings.MONGODB_PREFIX
subprefix = f"{settings.IMAGES_PREFIX}"
fileprefix = f"{settings.FILES_PREFIX}"
directprefix = f"{subprefix}/direct"
thumbprefix = "thumbnails"
upload_dir = settings.UPLOAD_DIR
delta = delta_data(settings.DATA_DELTA)
router = APIRouter(prefix=f"/{prefix}", tags=[f"{prefix}"], dependencies=[Depends(get_active_user_or_internal)])


# === Списки изображений (метаданные) ===
@router.get(f'/{subprefix}', response_model=FileListResponse, openapi_extra={'x-request-schema': None})
# @cache_key_builder(prefix = 'mongodb_images', expire = 300, key_params = ["after_date", "page", "per_page"])
async def get_images_after_date(
    after_date: datetime = Query(delta, description="Дата в формате ISO 8601 (например, 2024-01-01T00:00:00Z)"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(10, ge=1, le=1000, description="Количество элементов на страницу"),
    image_service: ThumbnailImageService = Depends()
):
    """
    Получение постраничного списка id изображений, созданных после заданной даты.
    """
    try:
        after_date = back_to_the_future(after_date)
        return await image_service.get_images_after_date(after_date, page, per_page)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(f'/{subprefix}list', response_model=dict, openapi_extra={'x-request-schema': None})
# @cache_key_builder(prefix = 'mongodb_images_list', expire = 300, key_params = ["after_date"])
async def get_images_list_after_date(
    after_date: datetime = Query(delta, description="Дата в формате ISO 8601 (например, 2024-01-01T00:00:00Z)"),
    image_service: ThumbnailImageService = Depends()  # ← Используем новый сервис
) -> dict:
    """
    список всех изображений в базе данных без страниц
    """
    try:
        after_date = back_to_the_future(after_date)
        result = await image_service.get_images_list_after_date(after_date)
        return {a: b for b, a in result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# === THUMBNAIL endpoint'ы (для списков) ===
@router.get(f'/{thumbprefix}/' + "{file_id}", openapi_extra={'x-request-schema': None})
async def download_thumbnail(
    file_id: str, image_service: ThumbnailImageService = Depends()
):
    """
    Получить THUMBNAIL изображения по ID (для списков)
    """
    # print(f"📱 THUMBNAIL request for ID: {file_id}")
    image_data = await image_service.get_thumbnail(file_id)

    headers = {"Content-Disposition": f"inline; filename={image_data['filename']}", "X-Image-Type": "thumbnail",
               "X-File-Size": str(len(image_data["content"]))}
    if image_data.get("from_cache"):
        headers["X-Cache"] = "HIT"
    else:
        headers["X-Cache"] = "MISS"

    # print(f"📱 Returning THUMBNAIL: {len(image_data['content'])} bytes")

    return Response(
        io.BytesIO(image_data["content"]), media_type=image_data['content_type'], headers=headers
    )


@router.get(f'/{thumbprefix}/name/' + "{filename}", openapi_extra={'x-request-schema': None})
async def download_thumbnail_by_filename(
    filename: str, image_service: ThumbnailImageService = Depends()
):
    """
    Получить THUMBNAIL по имени файла
    """
    # print(f"📱 THUMBNAIL request for filename: {filename}")
    image_data = await image_service.get_thumbnail_by_filename(filename)

    headers = {"Content-Disposition": f"inline; filename={image_data['filename']}", "X-Image-Type": "thumbnail",
               "X-File-Size": str(len(image_data["content"]))}
    if image_data.get("from_cache"):
        headers["X-Cache"] = "HIT"
    else:
        headers["X-Cache"] = "MISS"

    # print(f"📱 Returning THUMBNAIL: {len(image_data['content'])} bytes")

    return Response(
        io.BytesIO(image_data["content"]), media_type=image_data['content_type'], headers=headers
    )


# === FULL IMAGE endpoint'ы (для детального просмотра) ===
@router.get(f'/{subprefix}/' + "{file_id}", openapi_extra={'x-request-schema': None})
async def download_full_image(
    file_id: str, image_service: ThumbnailImageService = Depends()
):
    """
    Получить ПОЛНОРАЗМЕРНОЕ изображение по ID (для детального просмотра)
    """
    # print(f"🖼️  FULL IMAGE request for ID: {file_id}")
    image_data = await image_service.get_full_image(file_id)

    headers = {"Content-Disposition": f"attachment; filename={image_data['filename']}", "X-Image-Type": "full",
               "X-File-Size": str(len(image_data["content"]))}
    if image_data.get("from_cache"):
        headers["X-Cache"] = "HIT"
    else:
        headers["X-Cache"] = "MISS"

    # print(f"🖼️  Returning FULL IMAGE: {len(image_data['content'])} bytes")

    return Response(
        io.BytesIO(image_data["content"]), media_type=image_data['content_type'], headers=headers
    )


@router.get(f'/{fileprefix}/' + "{filename}", openapi_extra={'x-request-schema': None})
async def download_full_image_by_filename(
    filename: str, image_service: ThumbnailImageService = Depends()
):
    """
    Получить ПОЛНОРАЗМЕРНОЕ изображение по имени файла
    """
    # print(f"🖼️  FULL IMAGE request for filename: {filename}")
    try:
        image_data = await image_service.get_full_image_by_filename(filename)

        headers = {"Content-Disposition": f"attachment; filename={image_data['filename']}", "X-Image-Type": "full",
                   "X-File-Size": str(len(image_data["content"]))}
        if image_data.get("from_cache"):
            headers["X-Cache"] = "HIT"
        else:
            headers["X-Cache"] = "MISS"

        # print(f"🖼️  Returning FULL IMAGE: {len(image_data['content'])} bytes")

        return Response(
            io.BytesIO(image_data["content"]), media_type=image_data['content_type'], headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(f'/{subprefix}', response_model=ImageCreateResponse, openapi_extra={'x-request-schema': None})
# @invalidate_cache(patterns = ["mongodb_images:*", "mongodb_images_list:*"])
async def upload_image(
    file: UploadFile = File(...), description: Optional[str] = Form(None),
    image_service: ThumbnailImageService = Depends()
):
    """
    загрузка одного изображения в базу данных
    """
    result = await image_service.upload_image(file, description)
    if result.get('file_id'):
        result['mesage'] = "Image uploaded successfully"
    else:
        result['message'] = "Image upload fail"
    return result


@router.post(f'/{directprefix}', response_model=DirectUploadResponse, openapi_extra={'x-request-schema': None})
# @invalidate_cache(patterns = ["mongodb_images:*", "mongodb_images_list:*"])
async def direct_upload(image_service: ThumbnailImageService = Depends()) -> dict:
    """
    импортирование рисунков из директории UPLOAD_DIR
    """
    images = await image_service.direct_upload_image()
    return images


@router.delete(f'/{subprefix}/' + "{file_id}", response_model=dict, openapi_extra={'x-request-schema': None})
# @invalidate_cache(patterns = ["mongodb_images:*", "mongodb_images_list:*"])
async def delete_image(
    file_id: str, image_service: ThumbnailImageService = Depends()  # ← Используем новый сервис
):
    """
    удаление одного изображения по _id
    """
    success = await image_service.delete_image(file_id)
    if success:
        return {"message": "Image deleted successfully"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
