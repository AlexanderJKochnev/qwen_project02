# tests/config.py

from typing import Optional
from pydantic import PostgresDsn
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.config.project_config import get_path_to_root

# from app.mongodb.config import Settings
# load_dotenv() - не использовать - путает

env_file = Path(__file__).resolve().parent.joinpath('.env.tests')


class ConfigDataBase(BaseSettings):
    """ Postgresql Database Setting """
    model_config = SettingsConfigDict(env_file=get_path_to_root(env_file),
                                      env_file_encoding='utf-8',
                                      extra='ignore')

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    PG_PORT: str
    POSTGRES_DB: str
    DB_ECHO_LOG: bool
    # probable secirity issue:
    SECRET_KEY: str
    ALGORITHM: str
    # -----------------
    MONGODB_CONTAINER_NAME: str
    MONGO_INITDB_ROOT_USERNAME: str
    MONGO_INITDB_ROOT_PASSWORD: str
    MONGO_INITDB_DATABASE: str
    MONGO_DATABASE: str
    MONGO_OUT_PORT: int
    MONGO_INN_PORT: int
    MONGO_HOSTNAME: str
    MONGO_EXPRESS_CONTAINER_NAME: str
    ME_CONFIG_MONGODB_ADMINUSERNAME: str
    ME_CONFIG_MONGODB_ADMINPASSWORD: str
    ME_CONFIG_MONGODB_SERVER: str
    ME_CONFIG_BASICAUTH_USERNAME: str
    ME_CONFIG_BASICAUTH_PASSWORD: str
    ME_OUT_PORT: int
    ME_INN_PORT: int
    MEILISEARCH_URL: str
    MEILISEARCH_MASTER_KEY: str = "your_strong_master_key_here"
    MEILISEARCH_MODELS: str = 'item,drink,rawdata'
    TOLERANCE_TIME: int = 2

    @property
    def database_url(self) -> Optional[PostgresDsn]:
        """
        выводит строку подключения
        :return:
        :rtype:
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def django_database_url(self) -> Optional[PostgresDsn]:
        """
        выводит строку подключения
        :return:
        :rtype:
        """
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def mongo_url(self) -> str:
        """
        выводит строку подключения
        :return:
        :rtype:
        """
        return (f"mongodb://{self.MONGO_INITDB_ROOT_USERNAME}:"
                f"{self.MONGO_INITDB_ROOT_PASSWORD}@{self.MONGO_HOSTNAME}:"
                f"{self.MONGO_OUT_PORT}")  # {self.MONGO_INITDB_DATABASE}")


settings_db = ConfigDataBase()

# внешний url
base_url_out: str = 'http://83.167.126.4:18091/'

# локальный url в docker
base_url_doc: str = 'http://localhost:8091/'
