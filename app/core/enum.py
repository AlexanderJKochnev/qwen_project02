# app.core.enum.py
from enum import Enum
from app.core.config.database.db_sync import SessionLocalSync
from app.support.ollama.model import Ollama, Prompt, Proption


# 3. Синхронная функция для получения списка строк
def fetch_all_startup_data() -> dict:
    data = {}
    # session.query(LlmModel.name)
    with SessionLocalSync() as session:
        # Запрос 1: Модели
        models = session.query(Ollama.model).order_by(Ollama.model.asc()).scalars().all()
        # models = session.execute(text("SELECT name FROM llm_models")).scalars().all()
        data['models'] = [m for m in models] or ["qwen3:8b"]
        # Запрос 2: Prompt
        prompts = session.query(Prompt.role).order_by(Prompt.role.asc()).scalars().all()
        data['prompts'] = [pr for pr in prompts] or ["translator"]

        # Запрос 3: Preset
        presets = session.query(Proption.preset).order_by(Proption.preset.asc()).scalars().all()
        data['presets'] = [c for c in presets] or ["balanced"]

    return data


# data вызовется автоматически при импорте модулей в main.py
data = fetch_all_startup_data()

Preset = Enum("Preset", {v: v for v in data['presets']}, type=str)
LLmodel = Enum("Llmodel", {v: v for v in data['models']}, type=str)
Prompts = Enum("Prompts", {v: v for v in data['prompts']}, type=str)