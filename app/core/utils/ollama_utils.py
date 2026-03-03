from typing import Dict, Any, Optional, Sequence, Literal


def build_ollama_payload(
        db_row: Dict[str, Any], user_text: str, mode: Literal['chat', 'generate'] = 'chat',
        context: Optional[Sequence[int]] = None
) -> Dict[str, Any]:
    """
    Преобразует плоский словарь из БД в структуру для Ollama API.

    """
    # 1. Список полей, которые Ollama ждет внутри объекта 'options'
    option_keys = {'num_ctx', 'temperature', 'top_p', 'top_k', 'seed', 'num_predict', 'repeat_penalty', 'stop'}

    # Собираем вложенный словарь options (только те поля, что есть в БД)
    options = {k: db_row[k] for k in option_keys if k in db_row and db_row[k] is not None}

    # Базовая структура запроса
    payload = {"model": db_row.get("model", "llama3"), "options": options, "stream": False}

    # 2. Формируем тело в зависимости от режима
    if mode == 'chat':
        payload["messages"] = [{"role": "system", "content": db_row["system_prompt"]},
                               {"role": "user", "content": user_text}]
    else:
        payload["prompt"] = user_text
        payload["system"] = db_row["system_prompt"]
        if context:
            payload["context"] = context

    return payload
