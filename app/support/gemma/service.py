# app.support.gemma.service.py
from app.support.gemma.schemas import TranslationRequest


class TranslationService:
    def __init__(self, repository):
        self.repository = repository
        self.model_map = {1: "gemma2:2b", 2: "gemma2:9b", 3: "gemma2:27b"}

    async def translate(self, req: TranslationRequest):
        model_name = self.model_map.get(req.model_level, "gemma2:2b")

        # Общие опции для обоих типов API
        ollama_options = {"temperature": req.temperature, "num_predict": req.num_predict, "top_p": req.top_p,
                          "stop": req.stop}

        if req.interaction_type == "chat":
            payload = {"model": model_name, "messages": [
                {"role": "system", "content": f"You are a translator to {req.target_lang}. Output only text."},
                {"role": "user", "content": req.text}], "stream": False, "options": ollama_options,
                "keep_alive": req.keep_alive}
            result = await self.repository.call_api("chat", payload)
            return result.get("message", {}).get("content", "").strip()

        else:
            payload = {"model": model_name, "prompt": f"Translate to {req.target_lang}: {req.text}", "stream": False,
                       "options": ollama_options, "keep_alive": req.keep_alive}
            result = await self.repository.call_api("generate", payload)
            return result.get("response", "").strip()
