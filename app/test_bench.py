import asyncio
import time
from difflib import SequenceMatcher
from typing import List, Dict
import httpx

# Настройки для теста
OLLAMA_HOST = "http://localhost:11434/api/chat"


class TranslationBench:
    def __init__(self, industry_prompt: str):
        self.industry_prompt = industry_prompt

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Вычисляет % схожести между оригиналом и обратным переводом"""
        return round(SequenceMatcher(None, text1.lower(), text2.lower()).ratio() * 100, 2)

    async def single_pass(self, client: httpx.AsyncClient, text: str, model: str, lang: str, options: dict):
        """Один шаг: Прямой или Обратный перевод"""
        payload = {"model": model,
                   "messages": [{"role": "system",
                                 "content": f"{self.industry_prompt} "
                                 f"Target language: {lang}. Output ONLY translation."},
                                {"role": "user", "content": text}], "stream": False, "options": options}
        start = time.perf_counter()
        resp = await client.post(OLLAMA_HOST, json=payload, timeout=60.0)
        end = time.perf_counter()

        result = resp.json().get("message", {}).get("content", "").strip()
        return result, end - start

    async def run_full_test(self, original_text: str, models: List[str], target_langs: List[str], configs: List[dict]):
        results = []

        async with httpx.AsyncClient() as client:
            for model in models:
                for lang in target_langs:
                    for cfg in configs:
                        try:
                            # 1. Прямой перевод (Original -> Target)
                            forward_text, time_f = await self.single_pass(client, original_text, model, lang, cfg)

                            # 2. Обратный перевод (Target -> Original)
                            # Для обратного перевода язык всегда English (или исходный)
                            back_text, time_b = await self.single_pass(client, forward_text, model, "English", cfg)

                            similarity = self.calculate_similarity(original_text, back_text)
                            avg_time = round((time_f + time_b) / 2, 3)

                            results.append(
                                {"Model": model, "Lang": lang, "Temp": cfg.get("temperature"), "Avg_Time": avg_time,
                                 "Similarity_%": similarity, "Back_Text": back_text[:50] + "..."
                                 # Для отладки
                                 }
                            )
                        except Exception as e:
                            print(f"Error testing {model} on {lang}: {e}")

        return results
