# app/core/schemas/image_mixin.py
from pydantic import BaseModel, computed_field, Field
from typing import Optional, List
from app.core.config.project_config import settings


class ImageUrlMixin(BaseModel):
    """ добавляет поле для image_id"""
    image_id: Optional[str] = Field(default=None)  # DEPRECATED
    image_path: Optional[str] = Field(default=None)  # DEPRECATED
    seaweed_fids: Optional[List[str]] = Field(default=[] )


class ImageUrlMixinPath(BaseModel):
    """Pydantic миксин для автоматической генерации image_url из image_path"""
    image_path: Optional[str] = Field(default=None, exclude=True)

    @computed_field
    @property
    def image_url(self) -> Optional[str]:
        """
        Генерирует полный URL изображения на основе image_path и BASE_URL из настроек.
        Если image_path пустой — возвращает None.
        http://83.167.126.4:18091/mongodb/images/68d6ead9da55b293d13a0f5d
        """
        try:
            if not self.image_path:
                return None
            base_url = settings.BASE_URL or 'http://localhost/'

            prefix = settings.MONGODB_PREFIX or 'mongodb'
            # если ссылка по image id
            # images = settings.IMAGES_PREFIX or 'images'
            # если ссылка по имени файла
            images = settings.FILES_PREFIX or 'images'
            url = f"{base_url.rstrip('/')}/{prefix.strip('/')}/{images.strip('/')}/{self.image_path.strip('/')}"
            return url
        except Exception as e:
            print(f'image_url.error: {e}')
            return None
