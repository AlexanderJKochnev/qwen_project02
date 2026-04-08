# app/core/embeddings/hybrid_manager.py
import asyncio
import torch
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from model2vec import StaticModel
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class HybridEmbeddingManager:
    """
    Гибридный менеджер эмбеддингов:
    - GPU модель (mE5-small) для импорта CSV (высокое качество, 20-40 мс)
    - Static модель (distilled) для запросов (быстро, 2-5 мс, 0 VRAM)
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            # Static модель для запросов (всегда в памяти, CPU)
            self.query_model = None
            self.query_model_loaded = False

            # GPU модель для импорта (загружается по требованию)
            self.import_model = None
            self.import_model_loaded = False

            # Настройки
            self.executor = ThreadPoolExecutor(max_workers=2)
            self.device = self._get_device()

            self._initialized = True
            logger.info("HybridEmbeddingManager initialized")

    def _get_device(self) -> str:
        """Определяем устройство"""
        if torch.cuda.is_available():
            return 'cuda'
        elif torch.backends.mps.is_available():
            return 'mps'
        return 'cpu'

    def _load_query_model(self):
        """Загружаем лёгкую Static модель для запросов (CPU)"""
        if not self.query_model_loaded:
            logger.info("Loading Static query model (CPU, 50MB)...")
            self.query_model = StaticModel.from_pretrained(
                "multilingual-e5-small-distill256"
            )
            self.query_model_loaded = True
            logger.info("✅ Static query model loaded")

    def _load_import_model(self):
        """Загружаем GPU модель для импорта (тяжёлая, высокое качество)"""
        if not self.import_model_loaded:
            logger.info(f"Loading GPU import model (mE5-small) on {self.device}...")

            # Проверяем свободную VRAM
            if self.device == 'cuda':
                free_vram = torch.cuda.mem_get_info()[0] / 1024 ** 3
                logger.info(f"Free VRAM before import model: {free_vram:.1f}GB")

                if free_vram < 2.5:  # Нужно ~1.5GB + запас
                    logger.warning("Low VRAM, import model may fail")

            self.import_model = SentenceTransformer(
                "intfloat/multilingual-e5-small", device=self.device
            )

            # Опционально: FP16 для экономии VRAM
            if self.device == 'cuda':
                self.import_model.half()
                logger.info("Enabled FP16 mode for import model")

            self.import_model_loaded = True
            logger.info("✅ GPU import model loaded")

    # ============= Методы для запросов (используют Static модель) =============

    async def encode_query(self, text: str) -> List[float]:
        """
        Для пользовательских запросов.
        Использует Static модель (CPU, 2-5 мс, 0 VRAM)
        """
        self._load_query_model()

        loop = asyncio.get_event_loop()

        def _encode():
            embedding = self.query_model.encode([text])
            return embedding[0].tolist()

        return await loop.run_in_executor(self.executor, _encode)

    async def encode_queries_batch(self, texts: List[str]) -> List[List[float]]:
        """Базовая обработка нескольких запросов"""
        self._load_query_model()

        loop = asyncio.get_event_loop()

        def _encode():
            embeddings = self.query_model.encode(texts)
            return [emb.tolist() for emb in embeddings]

        return await loop.run_in_executor(self.executor, _encode)

    # ============= Методы для импорта (используют GPU модель) =============

    async def encode_for_import(self, texts: List[str], batch_size: int = 256) -> List[List[float]]:
        """
        Для импорта CSV.
        Использует GPU модель mE5-small (высокое качество, быстрый batch)
        """
        self._load_import_model()

        loop = asyncio.get_event_loop()

        def _encode():
            return self.import_model.encode(
                texts, normalize_embeddings=True, show_progress_bar=False, batch_size=batch_size
            ).tolist()

        return await loop.run_in_executor(self.executor, _encode)

    async def encode_for_import_streaming(
            self, texts: List[str], callback=None
    ) -> List[List[float]]:
        """
        Потоковая обработка для больших батчей с прогрессом
        """
        self._load_import_model()

        results = []
        batch_size = 256

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            loop = asyncio.get_event_loop()

            def _encode_batch():
                return self.import_model.encode(
                    batch, normalize_embeddings=True, show_progress_bar=False
                ).tolist()

            batch_results = await loop.run_in_executor(self.executor, _encode_batch)
            results.extend(batch_results)

            if callback:
                await callback(i + len(batch), len(texts))

            # Даём дыхание системе
            await asyncio.sleep(0.01)

        return results

    # ============= Управление памятью =============

    def unload_import_model(self):
        """Выгружаем GPU модель после импорта, освобождаем VRAM"""
        if self.import_model_loaded:
            logger.info("Unloading GPU import model...")
            del self.import_model
            self.import_model = None
            self.import_model_loaded = False

            if self.device == 'cuda':
                torch.cuda.empty_cache()
                free_vram = torch.cuda.mem_get_info()[0] / 1024 ** 3
                logger.info(f"VRAM freed. Free: {free_vram:.1f}GB")

            logger.info("✅ GPU import model unloaded")

    def get_status(self) -> dict:
        """Статус моделей и памяти"""
        status = {"query_model_loaded": self.query_model_loaded, "import_model_loaded": self.import_model_loaded,
                  "device": self.device, }

        if self.device == 'cuda' and torch.cuda.is_available():
            free, total = torch.cuda.mem_get_info()
            status["vram_free_gb"] = round(free / 1024 ** 3, 2)
            status["vram_used_gb"] = round((total - free) / 1024 ** 3, 2)
            status["vram_total_gb"] = round(total / 1024 ** 3, 2)

        return status

    async def warmup(self):
        """Прогрев моделей (опционально)"""
        self._load_query_model()
        # Для теста: делаем один запрос
        await self.encode_query("warmup")
        logger.info("Query model warmed up")


# Глобальный экземпляр
hybrid_embeddings = HybridEmbeddingManager()
