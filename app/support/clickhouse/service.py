# app.support.clickhouse.service.py


import asyncio
from pathlib import Path
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from model2vec import StaticModel
import torch
from loguru import logger


class EmbeddingService:
    """
    Гибридный сервис эмбеддингов:
    - Для поиска: статическая модель (distilled, CPU, 256 dims) из /app/models/distilled_e5_256d
    - Для импорта: полная модель (intfloat/multilingual-e5-small) из кэша /app/cache
    """

    def __init__(self):
        # Пути внутри контейнера (проброшены через volumes)
        self.models_dir = Path("/app/models")
        self.cache_dir = Path("/app/cache")
        self.distilled_path = self.models_dir / "distilled_e5_256d"

        self._query_model: Optional[StaticModel] = None
        self._import_model: Optional[SentenceTransformer] = None
        self._device = self._get_device()

        # Проверяем наличие дистиллированной модели
        if not self.distilled_path.exists():
            logger.error(f"Distilled model not found at {self.distilled_path}. "
                         "Please run setup_models.py first and mount the models volume.")
            raise RuntimeError("Distilled model missing")

    def _get_device(self) -> str:
        if torch.cuda.is_available():
            return 'cuda'
        elif torch.backends.mps.is_available():
            return 'mps'
        return 'cpu'

    def _ensure_query_model(self):
        """Загружает статическую модель для поиска (локально, CPU)"""
        if self._query_model is None:
            logger.info(f"Loading distilled model from {self.distilled_path}...")
            self._query_model = StaticModel.from_pretrained(str(self.distilled_path))
            logger.info("Query model ready (static, 256 dims)")

    def _ensure_import_model(self):
        """Загружает полную модель для импорта из кэша (GPU если доступен)"""
        if self._import_model is None:
            logger.info(f"Loading full model from cache {self.cache_dir} on {self._device}...")
            self._import_model = SentenceTransformer(
                "intfloat/multilingual-e5-small",
                cache_folder=str(self.cache_dir),   # ключ: используем кэш
                device=self._device
            )
            if self._device == 'cuda':
                self._import_model.half()
            logger.info("Import model ready (full, 384 dims)")

    async def encode_query(self, text: str) -> List[float]:
        """Для поиска (статическая модель, CPU)"""
        loop = asyncio.get_event_loop()
        self._ensure_query_model()

        def _encode():
            return self._query_model.encode([text])[0].tolist()

        return await loop.run_in_executor(None, _encode)

    async def encode_batch(self, texts: List[str], for_import: bool = False) -> List[List[float]]:
        """Batch эмбеддингов"""
        loop = asyncio.get_event_loop()

        if for_import:
            self._ensure_import_model()
            def _encode():
                return self._import_model.encode(
                    texts,
                    normalize_embeddings=True,
                    batch_size=256
                ).tolist()
        else:
            self._ensure_query_model()
            def _encode():
                return self._query_model.encode(texts).tolist()

        return await loop.run_in_executor(None, _encode)

    def unload_import_model(self):
        """Выгружает GPU модель после импорта (освобождает VRAM)"""
        if self._import_model:
            del self._import_model
            self._import_model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("Import model unloaded, VRAM freed")

    def get_status(self) -> dict:
        return {
            "query_model_loaded": self._query_model is not None,
            "import_model_loaded": self._import_model is not None,
            "distilled_model_exists": self.distilled_path.exists(),
            "cache_dir_exists": self.cache_dir.exists(),
            "device": self._device
        }