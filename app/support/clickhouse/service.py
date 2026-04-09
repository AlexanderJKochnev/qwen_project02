# app.support.clickhouse.service.py
# это легкий CPU embedding
import asyncio
from model2vec import StaticModel
from pathlib import Path


class EmbeddingService:
    def __init__(self, models_dir: str = "/app/models"):
        self.model_path = Path(models_dir) / "distilled_e5_256d"
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            self._model = StaticModel.from_pretrained(str(self.model_path))

    async def encode_query(self, text: str) -> list[float]:
        self._ensure_model()
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._model.encode([text])[0].tolist()
        )
