# app.support.gemma.repository.py
import httpx
from fastapi import HTTPException


class OllamaRepository:
    def __init__(self, base_url: str = "http://ollama:11434"):
        self.base_url = base_url

    async def call_api(self, endpoint: str, payload: dict):
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                resp = await client.post(f"{self.base_url}/api/{endpoint}", json=payload)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                # Прокидываем ошибку наверх в эндпоинт
                detail = e.response.text if hasattr(e, 'response') else str(e)
                raise HTTPException(status_code=500, detail=f"Ollama Error: {detail}")
