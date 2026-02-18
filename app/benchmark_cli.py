# тест моделей для перевода
# docker exec -it app python app/benchmark_cli.py

import asyncio
import time
from difflib import SequenceMatcher
from typing import List, Dict, Tuple

import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# Конфигурация
OLLAMA_HOST = "http://ollama:11434/api/chat"
console = Console()

# Твои отраслевые промпты
INDUSTRY_PROMPTS = {
    "wine": "You are a professional sommelier and wine critic. Use professional terminology (terroir, bouquet, tannins). Translate accurately and elegantly.",
    "trade": "You are an e-commerce and retail expert. Focus on product specs, marketing appeal, and clear trade terms.",
    "general": "You are a precise translator. Output ONLY the translated text without any explanations."
}


class BenchmarkingCLI:
    def __init__(self):
        # Маппинг уровней на реальные модели в Ollama
        self.model_map = {1: "gemma2:2b", 2: "qwen2.5:7b", 3: "gemma2:9b"}

    def calculate_similarity(self, text1: str, text2: str) -> float:
        return round(SequenceMatcher(None, text1.lower(), text2.lower()).ratio() * 100, 1)

    async def translate_step(self, client: httpx.AsyncClient, text: str, model: str, lang: str, temp: float, industry: str):
        # Выбираем системный промпт
        sys_content = INDUSTRY_PROMPTS.get(industry, INDUSTRY_PROMPTS["general"])

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": f"{sys_content} Target language: {lang}."},
                {"role": "user", "content": text}
            ],
            "stream": False,
            "options": {"temperature": temp}
        }

        start = time.perf_counter()
        resp = await client.post(OLLAMA_HOST, json=payload, timeout=120.0)
        resp.raise_for_status()
        end = time.perf_counter()

        data = resp.json()
        content = data["message"]["content"].strip()

        # Считаем TPS (Tokens Per Second)
        eval_count = data.get("eval_count", 0)
        eval_duration = data.get("eval_duration", 1) / 1e9
        tps = round(eval_count / eval_duration, 1) if eval_count > 0 else 0

        return content, end - start, tps

    async def run(self, text: str, levels: List[int], langs: List[str], temps: List[float], industry: str):
        sys_prompt = INDUSTRY_PROMPTS.get(industry, INDUSTRY_PROMPTS["general"])
        results = []
        total_steps = len(levels) * len(langs) * len(temps)

        console.print(f"[bold blue]Запуск бенчмарка для отрасли:[/] [bold yellow]{industry.upper()}[/]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            main_task = progress.add_task("[cyan]Прогресс...", total=total_steps)

            async with httpx.AsyncClient() as client:
                for lvl in levels:
                    model = self.model_map.get(lvl, "gemma2:2b")
                    for lang in langs:
                        for temp in temps:
                            progress.update(main_task, description=f"[yellow]Тест {model} -> {lang} (T={temp})")
                            try:
                                # Прямой перевод
                                f_text, t1, tps1 = await self.translate_step(client, text, model, lang, temp, industry)
                                # Обратный перевод (на английский для сравнения)
                                b_text, t2, tps2 = await self.translate_step(client, f_text, model, "English", temp, industry)

                                sim = self.calculate_similarity(text, b_text)
                                avg_tps = round((tps1 + tps2) / 2, 1)
                                avg_time = round((t1 + t2) / 2, 2)

                                results.append({
                                    "model": model, "lang": lang, "temp": str(temp),
                                    "time": f"{avg_time}s", "tps": avg_tps, "sim": sim
                                })
                            except Exception as e:
                                results.append({
                                    "model": model, "lang": lang, "temp": str(temp),
                                    "time": f"ERR {e}", "tps": 0, "sim": 0
                                })
                            progress.advance(main_task)

        self.display_table(results, text, industry)

    def display_table(self, data, original_text, industry):
        table = Table(
            title=f"\n[bold white]Бенчмарк: {industry.upper()}[/]\n[grey62]Текст: {original_text[:60]}...",
            show_header=True,
            header_style="bold magenta",
            border_style="bright_black"
        )
        table.add_column("Модель", style="cyan")
        table.add_column("Язык", style="green")
        table.add_column("T°", justify="center")
        table.add_column("Время (с)", justify="right")
        table.add_column("Ток/сек", justify="right", style="bold blue")
        table.add_column("Схожесть", justify="right")

        for r in data:
            sim_style = "bold green" if r['sim'] >= 90 else "yellow" if r['sim'] >= 75 else "bold red"
            sim_str = f"[{sim_style}]{r['sim']}%[/]"

            table.add_row(r['model'], r['lang'], r['temp'], r['time'], str(r['tps']), sim_str)

        console.print(table)


# Параметры теста
if __name__ == "__main__":
    # Настраиваемые параметры теста
    TEST_TEXT = "Full-bodied Cabernet Sauvignon with firm tannins and notes of blackcurrant and cedar."
    TEST_LEVELS = [1, 2]  # 2b и 7b
    TEST_LANGS = ["russian", "spanish", "chinese", "french"]
    TEST_TEMPS = [0.0, 0.3]
    TEST_INDUSTRY = "wine"  # "wine", "trade", "general"

    cli = BenchmarkingCLI()
    asyncio.run(cli.run(TEST_TEXT, TEST_LEVELS, TEST_LANGS, TEST_TEMPS, TEST_INDUSTRY))
