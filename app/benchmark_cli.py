import asyncio
import time
from difflib import SequenceMatcher
from typing import List, Dict

import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# Настройки
OLLAMA_HOST = "http://ollama:11434/api/chat"
console = Console()

# Промпты отраслей
INDUSTRY_PROMPTS = {"wine": "You are a professional sommelier. Use wine terminology (terroir, tannins, notes).",
                    "trade": "You are an e-commerce expert. Focus on product specs and marketing appeal.",
                    "general": "You are a precise translator. Output only the translated text."}


class BenchmarkingCLI:
    def __init__(self):
        self.model_map = {1: "gemma2:2b", 2: "qwen2.5:7b", 3: "gemma2:9b"}

    def calculate_similarity(self, text1: str, text2: str) -> float:
        return round(SequenceMatcher(None, text1.lower(), text2.lower()).ratio() * 100, 1)

    async def translate_step(
            self, client: httpx.AsyncClient, text: str, model: str, lang: str, temp: float, sys_prompt: str
    ):
        payload = {"model": model,
                   "messages": [{"role": "system", "content": f"{sys_prompt} Target language: {lang}. ONLY translation."},
                                {"role": "user", "content": text}], "stream": False, "options": {"temperature": temp}}
        start = time.perf_counter()
        resp = await client.post(OLLAMA_HOST, json=payload, timeout=120.0)
        resp.raise_for_status()
        end = time.perf_counter()
        return resp.json()["message"]["content"].strip(), end - start

    async def run(self, text: str, levels: List[int], langs: List[str], temps: List[float], industry: str):
        sys_prompt = INDUSTRY_PROMPTS.get(industry, INDUSTRY_PROMPTS["general"])
        results = []
        total_steps = len(levels) * len(langs) * len(temps)

        with Progress(
                SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(),
                TaskProgressColumn(), console=console
        ) as progress:
            main_task = progress.add_task("[cyan]Running Benchmarks...", total=total_steps)

            async with httpx.AsyncClient() as client:
                for lvl in levels:
                    model = self.model_map.get(lvl, "gemma2:2b")
                    for lang in langs:
                        for temp in temps:
                            progress.update(main_task, description=f"[yellow]Testing {model} -> {lang} (T={temp})")
                            try:
                                # Прямой
                                f_text, t1 = await self.translate_step(client, text, model, lang, temp, sys_prompt)
                                # Обратный
                                b_text, t2 = await self.translate_step(
                                    client, f_text, model, "English", temp, sys_prompt
                                )

                                sim = self.calculate_similarity(text, b_text)
                                avg_time = round((t1 + t2) / 2, 3)

                                results.append([model, lang, str(temp), f"{avg_time}s", f"{sim}%"])
                            except Exception as e:
                                results.append([model, lang, str(temp), f"ERROR {e}", "0%"])

                            progress.advance(main_task)

        self.display_table(results, text)

    def display_table(self, data, original_text):
        table = Table(
            title=f"\nTranslation Benchmark Results\n[grey62]Original: {original_text[:60]}...", show_header=True,
            header_style="bold magenta"
        )
        table.add_column("Model", style="cyan")
        table.add_column("Lang", style="green")
        table.add_column("Temp", justify="center")
        table.add_column("Avg Time", justify="right")
        table.add_column("Similarity", justify="right", style="bold yellow")

        for row in data:
            # Подсветка хороших результатов
            sim_val = float(row[4].replace('%', ''))
            if sim_val > 90:
                row[4] = f"[bold green]{row[4]}[/]"
            elif sim_val < 70:
                row[4] = f"[bold red]{row[4]}[/]"

            table.add_row(*row)

        console.print(table)


# Параметры теста
if __name__ == "__main__":
    test_text = "Full-bodied Cabernet with firm tannins and notes of dark chocolate."
    test_levels = [1, 2, 4]  # 2b и 7b
    test_langs = ["Russian", "Spanish", "Chinese", "French"]
    test_temps = [0.0, 0.5, 0.9]

    cli = BenchmarkingCLI()
    asyncio.run(cli.run(test_text, test_levels, test_langs, test_temps, "wine"))
