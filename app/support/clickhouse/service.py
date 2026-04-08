# app.support.clickhouse.service.py


import asyncio
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from model2vec import StaticModel
import torch
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Гибридный сервис эмбеддингов"""

    def __init__(self):
        self._query_model: Optional[StaticModel] = None
        self._import_model: Optional[SentenceTransformer] = None
        self._device = self._get_device()

    def _get_device(self) -> str:
        if torch.cuda.is_available():
            return 'cuda'
        elif torch.backends.mps.is_available():
            return 'mps'
        return 'cpu'

    def _ensure_query_model(self):
        """Ленивая загрузка Static модели (CPU)"""
        if self._query_model is None:
            logger.info("Loading Static query model (CPU)...")
            self._query_model = StaticModel.from_pretrained("multilingual-e5-small-distill256")
            logger.info("✅ Query model ready")

    def _ensure_import_model(self):
        """Ленивая загрузка GPU модели"""
        if self._import_model is None:
            logger.info(f"Loading GPU import model on {self._device}...")
            self._import_model = SentenceTransformer(
                "intfloat/multilingual-e5-small", device=self._device
            )
            if self._device == 'cuda':
                self._import_model.half()
            logger.info("✅ Import model ready")

    async def encode_query(self, text: str) -> List[float]:
        """Для поиска (Static, CPU, быстро)"""
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
                embeddings = self._import_model.encode(texts, normalize_embeddings=True, batch_size=256).tolist()
                return [emb[:256].tolist() for emb in embeddings]
                # return self._import_model.encode(texts, normalize_embeddings=True, batch_size=256).tolist()
        else:
            self._ensure_query_model()

            def _encode():
                return self._query_model.encode(texts).tolist()

        return await loop.run_in_executor(None, _encode)

    def unload_import_model(self):
        """Выгрузка GPU модели"""
        if self._import_model:
            del self._import_model
            self._import_model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("GPU model unloaded")

    def get_status(self) -> dict:
        return {"query_model_loaded": self._query_model is not None,
                "import_model_loaded": self._import_model is not None, "device": self._device}
