# app/support/websearch/service.py
import httpx
import zlib
import string
from fastapi import HTTPException
import asyncio
from typing import List, Dict
import json
from loguru import logger
from redis.asyncio import Redis
from app.core.config.project_config import settings
from app.core.config.database.redis_async import redis_manager
from app.support.websearch.schemas import SearchResponse


class WebSearchService:
    PUNCT_TABLE = str.maketrans(string.punctuation, ' ' * len(string.punctuation))

    def __init__(self):
        # В Docker сети SearXNG доступен по имени searxng:8080
        self.searxng_url: str = f"http://searxng:{settings.SEARXNG_PORT}"
        self._redis = None
        self.cache_ttl = 86400  # 24 часа в секундах
        # ollama_url: str = "http://ollama:11434"
        # ollama_url: str = "http://localhost:11434"

    @property
    def redis(self):
        """Создает клиент только при первом обращении, когда пул уже готов"""
        if self._redis is None:
            # Пул гарантированно инициализирован в lifespan к моменту вызова API
            self._redis = Redis(connection_pool=redis_manager.pool)
        return self._redis

    def _normalize_query(self, query: str) -> str:
        """ Самый быстрый способ нормализации через translate """
        if not query:
            return ""

        # 1. Приводим к нижнему регистру
        # 2. Удаляем пунктуацию через быструю таблицу перевода
        # 3. split() без параметров удалит любые пробельные символы (включая \n, \t)
        words = query.lower().translate(self.PUNCT_TABLE).split()

        # 4. Сортируем слова по алфавиту для идентичности ключей
        words.sort()

        return " ".join(words)

    async def search_tune(self, query: str, category: str, language: str, max_results: int):
        """ настраиваемый поиск через SearXNG """
        normalised_query = self._normalize_query(query)
        cache_key = f"search:{category}:{language}:{normalised_query}"
        # 1. Чтение и распаковка
        try:
            compressed = await self.redis.get(cache_key)
            if compressed:
                return SearchResponse(result=json.loads(zlib.decompress(compressed).decode('utf-8')),
                                      found_in_db=False,
                                      found_in_cash=True)
        except Exception as e:
            logger.error(f"Cache read error: {e}")
        # 2. Поиск (логика получения data из SearXNG)
        search = f"{query} -wikipedia"
        try:
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
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=response.text)
                data = response.json()
                from app.core.utils.common_utils import jprint
                print(data.keys())
                # jprint(data)
                search_results: str = []
                for result in data.get("results", [])[:max_results]:
                    search_results.append(
                        {"title": result.get("title", ""), "url": result.get("url", ""),
                         "content": result.get("content", ""), "score": result.get("score", 0)}
                    )
                # 3. Сжатие и запись
                if search_results:
                    try:
                        # Сжимаем строку в байты
                        data_to_cache = zlib.compress(json.dumps(search_results).encode('utf-8'))
                        await self.redis.setex(cache_key, self.cache_ttl, data_to_cache)
                    except Exception as e:
                        logger.error(f"Cache write error: {e}")
                jprint(search_results)
                return SearchResponse(result=search_results, found_in_db=False, found_in_cash=True)
        except HTTPException as e:
            logger.error(str(e))

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


_web_search_instance = WebSearchService()


def get_web_search_service() -> WebSearchService:
    """Провайдер для Depends"""
    return _web_search_instance
