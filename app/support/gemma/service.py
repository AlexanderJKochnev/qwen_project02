# app.support.gemma.service.py
import asyncio
import time
from difflib import SequenceMatcher
from app.support.gemma.schemas import BenchmarkRequest


class TranslationService:
    # ... (предыдущий код инициализации)

    def _get_similarity(self, text1: str, text2: str) -> float:
        return round(SequenceMatcher(None, text1.lower(), text2.lower()).ratio() * 100, 1)

    async def run_benchmark(self, req: BenchmarkRequest):
        report = []
        # Выбираем промпт отрасли
        sys_prompt = INDUSTRY_PROMPTS.get(req.industry, INDUSTRY_PROMPTS["general"])

        for lvl in req.model_levels:
            model_name = self.model_map.get(lvl)
            for lang in req.target_langs:
                for temp in req.temperatures:
                    try:
                        # 1. Прямой перевод
                        start_f = time.perf_counter()
                        forward_res = await self.repository.call_api(
                            "chat", {"model": model_name, "messages": [
                                {"role": "system", "content": f"{sys_prompt} Translate to {lang}."},
                                {"role": "user", "content": req.text}], "options": {"temperature": temp},
                                "stream": False}
                        )
                        end_f = time.perf_counter()
                        f_text = forward_res.get("message", {}).get("content", "")

                        # 2. Обратный перевод (Back-translation)
                        start_b = time.perf_counter()
                        backward_res = await self.repository.call_api(
                            "chat", {"model": model_name, "messages": [
                                {"role": "system", "content": f"{sys_prompt} Translate back to English."},
                                {"role": "user", "content": f_text}], "options": {"temperature": temp},
                                "stream": False}
                        )
                        end_b = time.perf_counter()
                        b_text = backward_res.get("message", {}).get("content", "")

                        # Считаем метрики
                        sim = self._get_similarity(req.text, b_text)
                        avg_time = round(((end_f - start_f) + (end_b - start_b)) / 2, 3)

                        report.append(
                            {"model": model_name, "lang": lang, "temp": temp, "avg_time_sec": avg_time,
                             "similarity_pct": sim, "status": "ok"}
                        )
                    except Exception as e:
                        report.append({"model": model_name, "lang": lang, "status": f"error: {str(e)}"})

        # Печатаем красивую таблицу в консоль сервера
        self._print_table(report)
        return report

    def _print_table(self, report):
        print("\n" + "=" * 80)
        print(f"{'MODEL':<15} | {'LANG':<10} | {'TEMP':<5} | {'TIME':<7} | {'SIMILARITY'}")
        print("-" * 80)
        for r in report:
            if r['status'] == 'ok':
                print(
                    f"{r['model']:<15} | {r['lang']:<10} | {r['temp']:<5} | {r['avg_time_sec']:<7} | {r['similarity_pct']}%"
                )
        print("=" * 80 + "\n")
