from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from app.core.hash_norm import get_cached_hash, tokenize
from app.support import Item
from app.support.hashing.model import WordHash
from collections import Counter
from app.core.config.database.db_async import get_db


async def seed_word_dictionary(session: AsyncSession, item_model: Any, word_model: Any):
    """
    Скрипт начального наполнения таблицы-словаря WordHash.
    """
    # 1. Выкачиваем весь сырой текст из основной таблицы
    # (Добавьте .limit() или чанки, если памяти < 16ГБ)
    res = await session.execute(select(item_model.search_content).where(item_model.search_content.is_not(None)))

    all_tokens = []
    print("Начинаю токенизацию данных...")

    for raw_text in res.scalars():
        # Собираем ВСЕ слова (с повторами) для правильного freq
        all_tokens.extend(tokenize(raw_text))

    if not all_tokens:
        print("Нет данных для индексации.")
        return

    # 2. Считаем частотность (Counter сделает set и count за один проход на C)
    print(f"Токенов собрано: {len(all_tokens)}. Считаю частотность...")
    counts = Counter(all_tokens)

    # 3. Подготовка к вставке
    data_to_insert = [{"word": w, "hash": get_cached_hash(w), "freq": c} for w, c in counts.items()]

    # 4. Массовая вставка батчами по 5000 строк
    print(f"Уникальных слов: {len(data_to_insert)}. Записываю в БД...")
    for i in range(0, len(data_to_insert), 5000):
        batch = data_to_insert[i:i + 5000]
        stmt = insert(word_model).values(batch)
        # Если слово уже есть, прибавляем частоту к существующей
        stmt = stmt.on_conflict_do_update(
            index_elements=['word'], set_={'freq': word_model.freq + stmt.excluded.freq}
        )
        await session.execute(stmt)

    await session.commit()
    print("Готово.")

seed_word_dictionary(get_db(), Item, WordHash)
