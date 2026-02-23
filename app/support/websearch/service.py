# app/support/websearch/service.py
# app/services/web_search.py
import httpx
import asyncio
from typing import List, Dict
import json
from loguru import logger
from app.core.config.project_config import settings

"""
categories_as_tabs:
  general:
  images:
  videos:
  news:
  map:
  music:
  it:
  science:
  files:
  social media:
"""


class WebSearchService:
    def __init__(self):
        # self.searxng_url = "https://api.abc8888.ru/searxng"
        # self.searxng_url = "https://api.test.abc8888.ru/searxng"
        self.searxng_url: str = "http://searxng:8080"
        ollama_url: str = "http://ollama:11434"
        # ollama_url: str = "http://localhost:11434"

    async def search_tune(self, search: str, category: str, language: str, max_results: int):
        """ настраиваемый поиск через SearXNG """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.searxng_url}/search",
                params={"q": search,
                        "format": "json",
                        "categories": category,
                        "language": language,
                        "safesearch": "0",
                        "pageno": 1,
                        "count": max_results
                        }
            )
            print(response.status_code, '===========================')
            data = response.json()
            from app.core.utils.common_utils import jprint
            print(data.keys())
            jprint(data)
            results = []
            for result in data.get("results", [])[:max_results]:
                results.append(
                    {"title": result.get("title", ""), "url": result.get("url", ""),
                     "content": result.get("content", ""), "score": result.get("score", 0)}
                )
            return results

    async def search_searxng(self, query: str, max_results: int = 5) -> List[Dict]:
        """Поиск через SearXNG"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.searxng_url}/search",
                params={"q": query,
                        "format": "json",
                        "categories": "general",
                        "language": "ru",
                        "safesearch": "0",
                        "pageno": 1,
                        "count": max_results
                        }
            )
            data = response.json()
            from app.core.utils.common_utils import jprint
            print(data.keys())
            jprint(data)

            # Возвращаем топ результатов
            results = []
            for result in data.get("results", [])[:max_results]:
                results.append(
                    {"title": result.get("title", ""), "url": result.get("url", ""),
                     "content": result.get("content", ""), "score": result.get("score", 0)}
                )
            return results

    async def fetch_full_content(self, url: str, max_length: int = 3000) -> str:
        """Загружаем полное содержание страницы для лучшего контекста"""
        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                response = await client.get(
                    url, headers={"User-Agent": "Mozilla/5.0 (compatible; YourBot/1.0)"}
                )
                # Простая очистка HTML (в реальности лучше использовать BeautifulSoup)
                import re
                text = re.sub(r'<[^>]+>', ' ', response.text)
                text = re.sub(r'\s+', ' ', text).strip()
                return text[:max_length]
        except Exception as e:
            return f"Не удалось загрузить содержимое: {e}"

    async def llm_evaluate_and_summarize(self, query: str, search_results: List[Dict]) -> Dict:
        """LLM оценивает результаты и генерирует резюме"""

        # Загружаем полный контент для топ-3 результатов
        content_tasks = []
        for result in search_results[:3]:
            if result.get("url"):
                content_tasks.append(self.fetch_full_content(result["url"]))

        full_contents = await asyncio.gather(*content_tasks)

        # Формируем контекст для LLM
        context = f"Запрос пользователя: {query}\n\n"
        context += "Найденная информация в интернете:\n"

        for i, (result, content) in enumerate(zip(search_results[:3], full_contents)):
            context += f"\n--- ИСТОЧНИК {i + 1} ---\n"
            context += f"Заголовок: {result['title']}\n"
            context += f"URL: {result['url']}\n"
            context += f"Содержание: {content[:1500]}\n"

        # Промпт для LLM
        prompt = f"""{context}

Твоя задача:
1. Оцени релевантность каждого источника (от 0 до 1)
2. Извлеки ключевую информацию: описание (2-5 предложений), местонахождение (если есть)
3. Верни ТОЛЬКО JSON в формате:
{{
  "description": "краткое описание на русском",
  "location": "местонахождение или null",
  "relevance_scores": [0.9, 0.5, 0.2],
  "confidence": 0.95
}}

Не добавляй никакого текста кроме JSON.
"""

        # Вызов Ollama
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.ollama_url}/api/generate", json={"model": "qwen2.5:7b",  # или gemma3:4b для скорости
                                                         "prompt": prompt, "stream": False,
                                                         "temperature": 0.1,  # Низкая температура для точности
                                                         "format": "json"}
            )
            result = response.json()

            # Парсим JSON из ответа
            try:
                return json.loads(result["response"])
            except Exception as e:
                logger.error(e)
                # Если LLM вернула невалидный JSON
                return {"description": "Не удалось обработать результаты", "location": None, "relevance_scores": [],
                        "confidence": 0}
