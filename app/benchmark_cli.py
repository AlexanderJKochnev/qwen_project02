import asyncio
import time
import csv
from datetime import datetime
import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from app.app.support.gemma.logic import get_ollama_payload, get_similarity_score

OLLAMA_HOST = "http://ollama:11434/api/chat"
console = Console()


class BenchmarkingCLI:
    def __init__(self):
        self.model_map = {1: "translategemma", 2: "qwen2.5:7b", 3: "gemma2:9b"}

    async def step(self, client, text, model, lang, industry, options):
        payload = get_ollama_payload(text, lang, model, industry, options)
        resp = await client.post(OLLAMA_HOST, json=payload, timeout=120.0)
        resp.raise_for_status()
        d = resp.json()

        tps = round(d.get("eval_count", 0) / (d.get("eval_duration", 1) / 1e9), 1)
        return d["message"]["content"].strip(), tps

    async def run(self, text, levels, langs, temps, industry):
        results = []
        total = len(levels) * len(langs) * len(temps)

        with Progress(SpinnerColumn(), TextColumn("[cyan]{task.description}"), BarColumn(), TaskProgressColumn(), console=console) as pr:
            task = pr.add_task("Тестирование...", total=total)
            async with httpx.AsyncClient() as client:
                for lvl in levels:
                    m = self.model_map[lvl]
                    for ln in langs:
                        for tp in temps:
                            pr.update(task, description=f"Модель: {m} | Lang: {ln} | T: {tp}")
                            try:
                                start = time.perf_counter()
                                f_txt, tps1 = await self.step(client, text, m, ln, industry, {"temperature": tp})
                                b_txt, tps2 = await self.step(client, f_txt, m, "English", industry, {"temperature": tp})
                                end = time.perf_counter()

                                # ИСПОЛЬЗУЕМ RAPIDFUZZ ЧЕРЕЗ LOGIC
                                sim = get_similarity_score(text, b_txt)

                                results.append({
                                    "Model": m, "Lang": ln, "Temp": tp,
                                    "Time": round((end - start) / 2, 2),
                                    "TPS": round((tps1 + tps2) / 2, 1),
                                    "Sim": sim
                                })
                            except Exception:
                                results.append({"Model": m, "Lang": ln, "Temp": tp, "Time": 0, "TPS": 0, "Sim": 0})
                            pr.advance(task)

        self.report(results, text, industry)

    def report(self, data, text, ind):
        table = Table(title=f"Бенчмарк: {ind.upper()}\n[grey62]Оригинал: {text[:50]}...")
        table.add_column("Model")
        table.add_column("Lang")
        table.add_column("T°")
        table.add_column("Time (s)")
        table.add_column("TPS", style="bold blue")
        table.add_column("Similarity (RapidFuzz)")

        for r in data:
            color = "green" if r['Sim'] > 85 else "yellow" if r['Sim'] > 65 else "red"
            table.add_row(r['Model'], r['Lang'], str(r['Temp']), str(
                r['Time']), str(r['TPS']), f"[{color}]{r['Sim']}%[/]")

        console.print(table)

        fname = f"bench_{datetime.now().strftime('%H%M%S')}.csv"
        with open(fname, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=data[0].keys())
            w.writeheader()
            w.writerows(data)
        console.print(f"\n[bold green]✓ CSV создан: {fname}[/]")


if __name__ == "__main__":
    T_TEXT = "Full-bodied Cabernet Sauvignon with firm tannins and notes of blackcurrant."
    asyncio.run(BenchmarkingCLI().run(T_TEXT, [1, 2, 3],
                                      ["russian", "spanish", "chinese", "english"],
                                      [0.0, 0.4, 1.0],
                                      "wine"))
