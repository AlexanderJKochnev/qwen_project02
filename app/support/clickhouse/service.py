# app.support.clickhouse.service.py
from pathlib import Path
from typing import List

from model2vec import StaticModel
import asyncio


class EmbeddingService:
    def __init__(self, models_dir: str = "/app/models"):
        self.model_path = Path(models_dir) / "distilled_e5_256d"
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            self._model = StaticModel.from_pretrained(str(self.model_path))

    async def encode_query(self, text: str) -> List[float]:
        loop = asyncio.get_event_loop()
        self._ensure_model()

        def _encode():
            return self._model.encode([text])[0].tolist()

        return await loop.run_in_executor(None, _encode)
