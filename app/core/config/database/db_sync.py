# app/core/congig/database/db_sync.py
# синхронный драйвер
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config.database.db_config import settings_db
from app.support.ollama.model import Proption, Prompt, Ollama

# 0. url для подключения
sync_database_url = settings_db.database_url.replace("postgresql+asyncpg://", "postgresql://")

#  1. Синхронный двигатель
engine_sync = create_engine(
    sync_database_url,
    echo=settings_db.DB_ECHO_LOG,
    pool_pre_ping=True,
)

# 2. Синхронная фабрика сессий
SessionLocalSync = sessionmaker(autocommit=False, autoflush=False, bind=engine_sync)


# 3. Функция для получения списка строк
def fetch_all_startup_data() -> dict:
    data = {}
    # session.query(LlmModel.name)
    with SessionLocalSync() as session:
        # Запрос 1: Модели
        models = session.query(Ollama.model).scalar().all()
        # models = session.execute(text("SELECT name FROM llm_models")).scalars().all()
        data['models'] = [m for m in models] or ["qwen3:8b"]
        # Запрос 2: Prompt
        prompts = session.query(Prompt.role).scalar().all()
        data['prompts'] = [pr for pr in prompts] or ["translator"]

        # Запрос 3: Preset
        presets = session.query(Proption.preset).scalar().all()
        data['presets'] = [c for c in presets] or ["balanced"]

    return data
