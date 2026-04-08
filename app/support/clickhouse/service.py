# app.support.clickhouse.service.py


import asyncio
from pathlib import Path
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from model2vec import StaticModel
import torch
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, models_dir: str = "/app/models"):
        self.models_dir = Path(models_dir)
        self.distilled_path = self.models_dir / "distilled_e5_256d"

        # Модели загружаются лениво
        self._query_model: Optional[StaticModel] = None
        self._import_model: Optional[SentenceTransformer] = None
        self._device = self._get_device()

        # Проверяем существование локальной модели
        if not self.distilled_path.exists():
            logger.warning(f"Distilled model not found at {self.distilled_path}. Will fallback to original model for queries.")

    def _get_device(self) -> str:
        if torch.cuda.is_available():
            return 'cuda'
        elif torch.backends.mps.is_available():
            return 'mps'
        return 'cpu'

    def _ensure_query_model(self):
        """Загружает статическую модель для поиска (локально)"""
        if self._query_model is None:
            if self.distilled_path.exists():
                logger.info(f"Loading distilled model from {self.distilled_path}...")
                self._query_model = StaticModel.from_pretrained(str(self.distilled_path))
            else:
                logger.warning("Distilled model missing, falling back to original model (slower).")
                # fallback: загружаем обычную модель на CPU
                self._query_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
            logger.info("Query model ready")

    def _ensure_import_model(self):
        """Загружает оригинальную модель для импорта (GPU если доступен)"""
        if self._import_model is None:
            logger.info(f"Loading original model on {self._device}...")
            self._import_model = SentenceTransformer(
                "intfloat/multilingual-e5-small",
                device=self._device
            )
            if self._device == 'cuda':
                self._import_model.half()
            logger.info("Import model ready")

    async def encode_query(self, text: str) -> List[float]:
        """Для поиска: дистиллированная модель (256 dims, CPU)"""
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
                # Оригинальная модель возвращает 384 dims, мы сохраняем как есть
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
        """Выгружает GPU модель после импорта"""
        if self._import_model:
            del self._import_model
            self._import_model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("GPU import model unloaded")

    def get_status(self) -> dict:
        return {
            "query_model_loaded": self._query_model is not None,
            "import_model_loaded": self._import_model is not None,
            "distilled_model_exists": self.distilled_path.exists(),
            "device": self._device
        }