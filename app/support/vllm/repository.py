# app.support.vllm.repository.py
from app.core.config.project_config import settings
from app.core.config.database.ollama_async import get_ollama_manager
from app.core.repositories.sqlalchemy_repository import Repository
from app.support.ollama.model import Ollama, Prompt, ISOLanguage, Proption, WriterRule


class VllmRepository:
    pass