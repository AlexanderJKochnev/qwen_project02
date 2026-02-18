import asyncio
from app.core.utils.translation_utils import TranslationService, OllamaRepository


async def run_benchmark():
    repo = OllamaRepository()
    service = TranslationService(repo)

    test_params = {"text": "Full-bodied wine with oak notes.", "target_lang": "russian", "model_level": 4,  # Qwen
                   "industry": "wine", "temperature": 0.0}

    # 1. Прямой перевод
    forward = await service.translate(test_params)
    print(f"Прямой: {forward['result']}")

    # 2. Обратный перевод
    rev_params = test_params.copy()
    rev_params.update({"text": forward['result'], "target_lang": "english"})
    backward = await service.translate(rev_params)
    print(f"Обратный: {backward['result']}")

    # 3. Сравнение через тот же сервис
    score = service.get_similarity_score(test_params["text"], backward["result"])
    print(f"Схожесть: {score}%")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
