# app/core/config/project_config.py
from pathlib import Path
from typing import Dict, List
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
# from app.core.utils.path_utils import get_path_to_root, strtodict, strtolist


def get_path_to_root(name: str = '.env'):
    """
        get path to file or directory in root directory
    """
    try:
        for k in range(1, 10):
            env_path = Path(__file__).resolve().parents[k] / name
            if env_path.exists():
                break
        else:
            env_path = None
            raise Exception('environment file is not found')
        return env_path
    except Exception:
        return None


def strtolist(data: str, delim: str = ',') -> List[str]:
    """ строка с разделителями в список"""
    if isinstance(data, str):
        return [a.strip() for a in data.split(delim)]
    else:
        return []


def strtodict(data: str, delim1: str = ',', delim2: str = ':') -> Dict[str, str]:
    tmp = strtolist(data, delim1)
    result: dict = {}
    for item in tmp:
        key, val = item.split(delim2)
        result[key.strip()] = val.strip()
    return result


class Settings(BaseSettings):
    """ Project Settings """
    # внешний адрес и порт
    BASE_URL: str = "http://83.167.126.4/"
    PORT: int = 18091

    DEV: int = 1

    API_PREFIX: str = "api"
    # === PREACT ===
    PREACT_PORT: int = 5555
    PREACT_PREFIX: str = "preact"
    # ПОЛЯ ДЛЯ ВЫВОДА В ВИДАХ DETAIL & LIST
    IDETAIL_VIEW: str = "name, description"
    ILIST_VIEW: str = "name"
    # языки
    LANGS: str = "en, ru, fr"
    # язык по умолчанию
    DEFAULT_LANG: str = "en"
    # локализованные поля
    LOCALIZED_FIELDS: str = 'name,title,subtitle,decription'
    MACHINE_TRANSLATION_MARK: str = 'ai'
    #  справочники
    HANDBOOKS_PREFIX: str = "handbooks"

    # === POSTGRES ===
    POSTGRES_DB: str = "wine_db"
    POSTGRES_USER: str = "wine"
    POSTGRES_PASSWORD: str = "wine1"
    POSTGRES_PORT: int = 5432
    POSTGRES_HOST: str = "wine_host"
    DB_ECHO_LOG: int = 0

    # === ADMINER === ДЛЯ ОТЛАДКИ - УДАЛИТЬ В PRODUCTION
    ADMINER_PORTS: str = "8092:8080"

    # === APP ===
    API_HOST: str = "0.0.0.0"
    # ВНУТРЕННИЙ ПОРТ
    API_PORT: int = 8091
    DB_ECHO: int = 1
    DEBUG: int = 1
    PROJECT_NAME: str = "Wine Project"
    VERSION: str = "0.0.1"
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000"
    LAZY: str = "selectin"
    CASCADE: str = "all, delete-orphan"
    # === ROUTERS ===
    AUTH_PREFIX: str = "auth"
    USER_PREFIX: str = "users"
    IMAGES_PREFIX: str = "images"
    FILES_PREFIX: str = "files"
    MONGODB_PREFIX: str = "mongodb"
    # два ниже удалить ? дублируются с разделом ROUTERS выше
    MONGO_IMAGES: str = "images"
    MONGO_DOCUMENTS: str = "documents"

    # ==== TOKENS ====
    ACCESS_TOKEN_LIFETIME: int = 30000
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30000
    REFRESH_TOKEN_EXPIRE_DAYS: int = 90
    REFRESH_TOKEN_LIFETIME: int = 86400
    REFRESH_TOKEN_ROTATE_MIN_LIFETIME: int = 720000
    SECRET_KEY: str = "gV64m9aIzFG4qpgVphvQbPQrtAO0nM-7YwwOvu0XPt5KJOjAy4AfgLkqJXYEt"
    ALGORITHM: str = "HS256"
    # В продакшене SECRET_KEY генерируется через openssl rand -hex 32

    # ==== PAGING SETTINGS ====
    # кол-во записей на странице
    PAGE_DEFAULT: int = 20
    # минимальное кол-во страниц
    PAGE_MIN: int = 0
    # максимальное кол-во страниц
    PAGE_MAX: int = 1000

    # === настройки для импорта изображений ====
    # директория куда складывать файлы с картинками и откуда они подтягиваются в mongo
    UPLOAD_DIR: str = "upload_volume"
    # максимальная величина файла МБ
    MAX_FILE_SIZE: int = 10
    ALLOWED_EXTENSIONS: str = "png, jpg, jpeg, gif, webp"
    JSON_FILENAME: str = "data.json"

    # MongoDB
    MONGODB_CONTAINER_NAME: str = "mongo"
    ME_CONFIG_MONGODB_ADMINUSERNAME: str = "admin"
    ME_CONFIG_MONGODB_ADMINPASSWORD: str = "admin"
    ME_CONFIG_MONGODB_SERVER: str = "mongo"
    ME_CONFIG_BASICAUTH_USERNAME: str = "admin"
    ME_CONFIG_BASICAUTH_PASSWORD: str = "admin"
    MONGO_HOSTNAME: str = "mongodb"
    MONGO_INITDB_ROOT_USERNAME: str = "admin"
    MONGO_INITDB_ROOT_PASSWORD: str = "admin"
    MONGO_INITDB_DATABASE: str = "admin"
    MONGO_DATABASE: str = "wine_database"

    MONGO_OUT_PORT: int = 27017
    MONGO_INN_PORT: int = 27017

    # mongo-express УДАЛИТЬ В PRODUCTION
    MONGO_EXPRESS_CONTAINER_NAME: str = "mongo-express"
    MONGO_EXPRESS_PORT: int = 8081
    # Application
    API_V1_STR: str = "/api/v1"
    ME_CONFIG_MONGODB_ADMINUSERNAME: str = "admin"
    ME_CONFIG_MONGODB_ADMINPASSWORD: str = "admin"
    ME_CONFIG_MONGODB_SERVER: str = "mongo"
    ME_CONFIG_BASICAUTH_USERNAME: str = "admin"
    ME_CONFIG_BASICAUTH_PASSWORD: str = "admin"
    ME_OUT_PORT: int = "8081"
    ME_INN_PORT: int = "8081"
    # IMAGE SIZING в пикселях
    IMAGE_WIDTH: int = 2000
    IMAGE_HEIGH: int = 5000
    # для jpg только
    IMAGE_QUALITY: int = 85
    # ДЛИНА РАНДОМНОГО ИМЕНИ ФАЙЛА. чем короче, тем быстрее поиск по имени файла / чем по _id
    LENGTH_RANDOM_NAME: int = 12

    # === настройки импорта json в базу данных
    IGNORED_FLDS: str = 'index, isHidden, uid, imageTimestamp'
    INTL_FLDS: str = 'vol, alc, count'
    CASTED_FLDS: str = 'vol: float, count: int, alc: float'
    FIRST_LEVEL_FLDS: str = 'vol, count, image_path, image_id'
    API_ROOT_FIELDS: str = 'vol, count, image_path, image_id, uid, country, category'
    COMPLEX_FLDS: str = 'country, category, region, pairing, varietal'
    LANGUAGE_KEY: str = 'english: en, russian: ru'
    RE_DELIMITER: str = '.,;:'
    EXT_DELIMITER: str = 'and, or, или, и'
    WINE_CATEGORY: str = 'red, white, rose, sparkling'
    REDUNDANT_FIELDS: str = 'uid, imageTimestamp, index, isHidden'
    # === настройки парсинга
    BATCH_SIZE: int = 20
    # === ARQ+REDIS
    # === настройки redis/arq
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    ARQ_TASK_TIMEOUT: int = 300  # 5 минут на задачу по умолчанию
    ARQ_MAX_TRIES: int = 3  # максимум 3 попытки
    ARQ_MIN_DELAY: int = 3
    ARQ_MAX_DELAY: int = 10

    # === EMAIL SETTINGS ===
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    EMAIL_ADMIN: str = "akochnev66@gmail.com"  # Email address to send error notifications to
    EMAIL_USE_TLS: bool = True
    EMAIL_USE_SSL: bool = False

    # === MYMEMORY TRANSLATION SERVICE ===
    MYMEMORY_API_EMAIL: str = "akochnev66@gmail.com"
    MYMEMORY_API_BASE_URL: str = "https://api.mymemory.translated.net/get"
    MYMEMORY_REQUESTS_PER_MINUTE: int = 10  # Rate limit for MyMemory API
    MYMEMORY_REQUESTS_PER_DAY: int = 1000   # Daily limit for MyMemory API

    # === HUGGINGFACE TRANSLATION SERVICE ===
    HF_API_TOKEN: str = "test token"  # Default token
    HF_MODEL_NAME: str = "google/translategemma-4b-it"
    HF_REQUESTS_PER_MINUTE: int = 5  # Rate limit for HuggingFace API
    HF_REQUESTS_PER_DAY: int = 100   # Daily limit for HuggingFace API

    model_config = SettingsConfigDict(env_file=get_path_to_root(),
                                      env_file_encoding='utf-8',
                                      extra='ignore')

    @property
    def redundant(self) -> list:
        return strtolist(self.REDUNDANT_FIELDS)

    @property
    def language_key(self) -> dict:
        return strtodict(self.LANGUAGE_KEY)

    @property
    def ext_delimiter(self) -> list:
        return strtolist(self.EXT_DELIMITER)

    @property
    def first_level_fields(self) -> list:
        return strtolist(self.FIRST_LEVEL_FLDS)

    @property
    def api_root_fields(self) -> list:
        return strtolist(self.API_ROOT_FIELDS)

    @property
    def wine_category(self) -> list:
        return strtolist(self.WINE_CATEGORY)

    @property
    def complex_fields(self) -> list:
        return strtolist(self.COMPLEX_FLDS)

    @property
    def ignored_fields(self) -> list:
        return strtolist(self.IGNORED_FLDS)

    @property
    def international_fields(self) -> list:
        return strtolist(self.INTL_FLDS)

    @property
    def casted_fields(self) -> dict:
        return strtodict(self.CASTED_FLDS)

    @property
    def DETAIL_VIEW(self) -> list:
        return strtolist(self.IDETAIL_VIEW)

    @property
    def LIST_VIEW(self) -> list:
        return strtolist(self.ILIST_VIEW)

    @property
    def LANGUAGES(self):
        """
        return list of languages codes ['en', 'ru, 'fr' ...]
        """
        return strtolist(self.LANGS)

    @property
    def FIELDS_LOCALIZED(self):
        """
        return list of localized fileds (without suffix)
        """
        return strtolist(self.LOCALIZED_FIELDS)

    @property
    def max_file_size(self) -> int:
        return self.MAX_FILE_SIZE * 1024 * 1024

    @property
    def allowed_extensions(self) -> List[str]:
        return strtolist(self.ALLOWED_EXTENSIONS)

    @property
    def get_exclude_list(self) -> List[str]:
        return strtolist(self.EXCLUDE_LIST)

    @property
    def mongo_url(self) -> str:
        return (f"mongodb://{self.MONGO_INITDB_ROOT_USERNAME}:"
                f"{self.MONGO_INITDB_ROOT_PASSWORD}@{self.MONGO_HOSTNAME}:"
                f"{self.MONGO_INN_PORT}")  # {self.MONGO_INITDB_DATABASE}")


settings = Settings()


get_paging: dict = {'def': settings.PAGE_DEFAULT,
                    'min': settings.PAGE_MIN,
                    'max': settings.PAGE_MAX
                    }

# Создаем директорию для загрузок при запуске
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
