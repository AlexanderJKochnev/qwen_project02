# app/core/utils/translation_utils.py
import asyncio  # noqa: F401
import httpx
import time
import csv
from datetime import datetime
from fastapi import HTTPException
# from loguru import logger
from typing import Dict, Optional, Any, List
from app.core.config.project_config import settings
import re
from rapidfuzz import fuzz
import httpx
from rapidfuzz import fuzz
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()

# 1. КОНСТАНТЫ (Прямо здесь, чтобы не было импортов)
INDUSTRY_PROMPTS = {
    "wine": "You are a professional sommelier. Use professional terminology (terroir, bouquet, tannins).",
    "trade": "You are an e-commerce expert. Focus on product specs and marketing appeal.",
    "general": "You are a precise translator. Output ONLY the translated text without explanations."}


class TranslationService:
    def __init__(self, repository):
        self.repository = repository
        self.model_map = {1: "translategemma", 2: "gemma2:9b", 3: "gemma2:27b", 4: "qwen2.5:7b"}

    # --- МЕТОДЫ ЛОГИКИ (Внутренние) ---

    def _clean(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'<.*?>', '', text)
        text = re.sub(r'[^\w\s]', '', text)
        return " ".join(text.lower().split())

    def get_similarity(self, t1: str, t2: str) -> float:
        s1, s2 = self._clean(t1), self._clean(t2)
        return round(fuzz.token_sort_ratio(s1, s2), 1) if s1 and s2 else 0.0

    def _build_payload(self, p: dict, model_name: str) -> dict:
        sys_content = INDUSTRY_PROMPTS.get(p.get('industry', 'general'), INDUSTRY_PROMPTS["general"])
        return {"model": model_name,
                "messages": [{"role": "system", "content": f"{sys_content} Target language: {p['target_lang']}."},
                             {"role": "user", "content": p['text']}, {"role": "assistant", "content": ""}], "stream": False,
                "options": {"temperature": p.get('temperature', 0.1), "num_predict": p.get('num_predict', 1000),
                            "top_p": p.get('top_p', 0.9), "stop": ["\nNote:", "\nExplanation:", "<end_of_turn>", "###"]},
                "keep_alive": p.get('keep_alive', '5m')}

    # --- РАБОЧИЙ МЕТОД (Для FastAPI и Теста) ---

    async def translate(self, p: dict):
        start = time.perf_counter()
        model_name = self.model_map.get(p.get('model_level', 1), "translategemma")

        payload = self._build_payload(p, model_name)
        result = await self.repository.call_api("chat", payload)

        content = result.get("message", {}).get("content", "").strip()

        # Расчет TPS
        eval_count = result.get("eval_count", 0)
        eval_duration = result.get("eval_duration", 1) / 1e9
        tps = round(eval_count / eval_duration, 1) if eval_count > 0 else 0

        return {"result": content, "tps": tps, "time": round(time.perf_counter() - start, 2)}

    # --- ТЕСТОВЫЙ МЕТОД (Бенчмарк) ---

    async def run_benchmark(self, text: str, levels: List[int], langs: List[str], temps: List[float], industry: str):
        results = []
        total = len(levels) * len(langs) * len(temps)

        with Progress(
                SpinnerColumn(), TextColumn("[cyan]{task.description}"), BarColumn(), TaskProgressColumn(),
                console=console
        ) as pr:
            task = pr.add_task("Тестирование параметров...", total=total)

            for lvl in levels:
                for ln in langs:
                    for tp in temps:
                        pr.update(task, description=f"Модель: {self.model_map[lvl]} | Lang: {ln} | T: {tp}")
                        try:
                            # Прямой прогон
                            res_f = await self.translate(
                                {"text": text, "target_lang": ln, "model_level": lvl, "industry": industry,
                                 "temperature": tp}
                            )
                            # Обратный прогон
                            res_b = await self.translate(
                                {"text": res_f['result'], "target_lang": "english", "model_level": lvl,
                                 "industry": industry, "temperature": tp}
                            )

                            sim = self.get_similarity(text, res_b['result'])
                            results.append(
                                {"Model": self.model_map[lvl], "Lang": ln, "Temp": tp, "Time": res_f['time'],
                                 "TPS": round((res_f['tps'] + res_b['tps']) / 2, 1), "Sim": sim}
                            )
                        except Exception as e:
                            results.append(
                                {"Model": self.model_map[lvl], "Lang": ln, "Temp": tp, "Time": f"ERR {e}", "TPS": 0,
                                 "Sim": 0}
                            )
                        pr.advance(task)

        self._save_and_show(results, text, industry)

    def _save_and_show(self, data, text, ind):
        table = Table(title=f"Бенчмарк: {ind.upper()}")
        table.add_column("Model")
        table.add_column("Lang")
        table.add_column("T°")
        table.add_column("Time")
        table.add_column("TPS")
        table.add_column("Similarity")
        for r in data:
            color = "green" if r['Sim'] > 90 else "yellow" if r['Sim'] > 70 else "red"
            table.add_row(
                r['Model'], r['Lang'], str(r['Temp']), f"{r['Time']}s", str(r['TPS']), f"[{color}]{r['Sim']}%[/]"
            )
        console.print(table)

        fname = f"bench_{datetime.now().strftime('%H%M%S')}.csv"
        with open(fname, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())
            writer.writeheader()
            writer.writerows(data)


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


async def translate_text(text: str,
                         target_lang: str = "ru",
                         mark: str = "ai",
                         source_lang: str = "en",
                         test: bool = False) -> Optional[str]:
    """
    Translate text using MyMemory translation service

    Args:
        text: Text to translate
        source_lang: Source language code (default: "en")
        target_lang: Target language code (default: "ru")
        mark:  отметка о машинном переводе
        test: used for test purpose only
    Returns:
        Translated text or None if translation failed
    """
    if not text or not text.strip():
        return text

    try:
        params = {
            "q": text,
            "langpair": f"{source_lang}|{target_lang}",
            "de": settings.MYMEMORY_API_EMAIL
        }
        if test:
            print(f"translate_text.{params=}")
            return f"{text} <{mark}>"
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.MYMEMORY_API_BASE_URL, params=params)
            response.raise_for_status()

            data = response.json()

            if data.get("responseStatus") == 200 and data.get("responseData"):
                translated_text = data["responseData"]["translatedText"]
                return f"{translated_text} <{mark}>"

            return None
    except Exception as e:
        print(f"Translation error: {e}")
        return None


async def gemma_translate(text: str,
                          target_lang: str = "ru",
                          source_lang: str = "en",
                          mark: str = "gm", **kwargs) -> Optional[str]:
    """
    Translate text with gemma
    """
    languages: dict = {'ru': 'russian',
                       'en': 'english',
                       'it': 'italian',
                       'zh': 'chinese',
                       'de': 'germany',
                       'es': 'spanish',
                       'fr': 'french'}
    ollama = settings.OLLAMA_HOST
    prompt = f"Translate the following text to {languages.get(target_lang, target_lang)}: {text}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(f"{ollama}/api/generate",
                                         json={"model": "translategemma",
                                               "prompt": prompt,
                                               "stream": False})
            response.raise_for_status()
            data = response.json()
            return data.get("response").strip()
        except Exception as e:
            raise Exception(f'gemma_translate.error: {e}')


async def llm_translate(text: str,
                        target_lang: str = "ru",
                        source_lang: str = "en",
                        mark: str = "gm",

                        **kwargs) -> Optional[str]:
    repo = OllamaRepository()
    service = TranslationService(repo)
    params = {"text": text, "target_lang": target_lang,
              "model_level": settings.OLLAMA_MODEL_LEVEL,
              "interaction_type": settings.OLLAMA_INTERACTION_TYPE,
              "temperature": settings.OLLAMA_TEMPERATURE,
              "num_predict": settings.OLLAMA_NUM_PREDICT,
              "top_p": settings.OLLAMA_TOP_P,
              "keep_alive": settings.OLLAMA_KEEP_ALIVE,
              "stop": None,
              "industry": "wine"
              }
    translated_text, time_taken = await service.translate(params)
    return translated_text


def get_group_localized_fields(langs: list, default_lang: str, localized_fields: list) -> Dict[str, List[str]]:
    """Get dict of localized field names that should be translated"""
    languages = [f'_{lang}' if lang != default_lang else '' for lang in langs]
    result: dict = {}
    for field in localized_fields:
        result[field] = [f'{field}{lang}' for lang in languages]
    return result


def get_field_language(field_name: str) -> Optional[str]:
    """Extract language code from field name"""
    if len(field_name) < 3 or field_name[-3] != '_':
        return settings.DEFAULT_LANG
    lang_code = field_name[-2:]
    # Check if the extracted code is in the configured languages
    if lang_code in settings.LANGUAGES:
        return lang_code
    return settings.DEFAULT_LANG


async def fill_missing_translations(data: Dict[str, Any], test: bool = False) -> Dict[str, Any]:
    """
    Fill missing translations in data dictionary using available translations

    Args:
        data: Dictionary containing fields that may need translation

    Returns:
        Updated dictionary with filled translations
    """
    if not data:
        return data

    updated_data = data.copy()

    # language
    langs = settings.LANGUAGES
    default_lang = settings.DEFAULT_LANG
    localized_fields = settings.FIELDS_LOCALIZED
    mark = settings.MACHINE_TRANSLATION_MARK
    # Group fields by their base name {'name': ['name', 'name_ru', 'name_fr', ...], ...}
    field_groups = get_group_localized_fields(langs, default_lang, localized_fields)
    # Process each group of related fields
    trans_func = gemma_translate
    for base_name, fields in field_groups.items():
        # Check which fields are filled
        # {'name': 'text', 'name_ru': 'текст', ...}
        filled_fields = {field: data.get(field) for field in fields if data.get(field)}

        # Skip if no source for translation
        if not filled_fields:
            continue

        # Determine source field priority: prefer First in language, then Second, then Next
        source_field = None
        source_value = None

        # Find source -- first non empty fields
        for lang in langs:
            for field_name, value in filled_fields.items():
                if get_field_language(field_name) == lang and value:
                    source_field = field_name
                    source_value = value
                    source_lang = lang
                    break
            if source_field:
                break

        if not source_value:    # no source found
            continue            # skip translation

        # Fill missing translations
        for field in fields:
            if field not in filled_fields:  # Field is missing
                target_lang = get_field_language(field)
                if target_lang and target_lang != source_lang:
                    # Translate from source to target
                    translated_text = await trans_func(
                        source_value,
                        target_lang=target_lang,
                        mark=mark,
                        source_lang=source_lang,
                    )

                    if translated_text:
                        updated_data[field] = translated_text
    return updated_data


# --- ТОЧКА ВХОДА ДЛЯ ЗАПУСКА ИЗ ТЕРМИНАЛА ---
if __name__ == "__main__":
    # Импортируем репозиторий здесь, чтобы избежать циклов в основном приложении

    async def main():
        repo = OllamaRepository()
        service = TranslationService(repo)

        # САМ ТЕСТ С ПЕРЕБОРОМ ПАРАМЕТРОВ
        await service.run_benchmark(
            text="Elegant Pinot Noir with silky tannins and aromas of forest floor.",
            levels=["translategemma", "gemma2:9b", "qwen2.5:7b"],
            # Проверяем всё от 2b до Qwen
            langs=["russian", "spanish", "english", "chinese"], temps=[0.0, 0.3, 0.9],  # Перебираем температуры
            industry="wine"
        )

    asyncio.run(main())
