# это import & GPU embedding
from pathlib import Path
from sentence_transformers import SentenceTransformer
from loguru import logger
import torch


class ImportEmbedding:
    def __init__(self, cache_dir: str = "/app/cache"):
        self.cache_dir = Path(cache_dir)
        self._model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self._model_path = self._find_model()

    def _find_model(self) -> Path:
        for model_dir in self.cache_dir.glob("models--intfloat--multilingual-e5-small*/snapshots/*"):
            if (model_dir / "model.safetensors").exists():
                logger.info(f"Found local model at {model_dir}")
                return model_dir
        raise RuntimeError("Full model not found. Please run setup_models.py first and mount cache volume.")

    def _load(self):
        if self._model is None:
            logger.info(f"Loading full model from {self._model_path} on {self.device}...")
            self._model = SentenceTransformer(
                str(self._model_path),   # путь к локальной папке
                device=self.device
            )
            if self.device == 'cuda':
                self._model.half()

    def encode(self, texts: list[str]) -> list[list[float]]:
        self._load()
        return self._model.encode(texts, normalize_embeddings=True, batch_size=256).tolist()

    def unload(self):
        if self._model:
            del self._model
            self._model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("GPU model unloaded")
