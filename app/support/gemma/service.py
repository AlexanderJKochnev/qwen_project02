# app.support.gemma.service.py
from app.support.gemma.schemas import TranslationRequest

import time


class TranslationService:
    def __init__(self, repository):
        self.repository = repository
        self.model_map = {1: "gemma2:2b", 2: "gemma2:9b", 3: "gemma2:27b"}

    async def translate(self, p: dict):
        start_time = time.perf_counter()  # Начинаем отсчет

        model_name = self.model_map.get(p['model_level'], "gemma2:2b")

        ollama_options = {"temperature": p['temperature'], "num_predict": p['num_predict'], "top_p": p['top_p'],
                          "stop": p['stop']}

        if p['interaction_type'] == "chat":
            payload = {"model": model_name,
                       "messages": [{"role": "system", "content": f"Translate to {p['target_lang']}. Only text."},
                                    {"role": "user", "content": p['text']}], "stream": False, "options": ollama_options,
                       "keep_alive": p['keep_alive']}
            result = await self.repository.call_api("chat", payload)
            content = result.get("message", {}).get("content", "").strip()
        else:
            payload = {"model": model_name, "prompt": f"Translate to {p['target_lang']}: {p['text']}", "stream": False,
                       "options": ollama_options, "keep_alive": p['keep_alive']}
            result = await self.repository.call_api("generate", payload)
            content = result.get("response", "").strip()

        execution_time = time.perf_counter() - start_time
        return content, round(execution_time, 3)
