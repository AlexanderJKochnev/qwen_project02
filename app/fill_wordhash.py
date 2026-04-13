from collections import Counter
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.hash_norm import get_cached_hash, tokenize


async def seed_word_dictionary(session: AsyncSession, result_stream, word_model: Any):
    """
    Версия с поддержкой асинхронного стрима для экономии памяти Docker-контейнера.
    """
    all_tokens = []

    # Читаем стрим построчно
    async for row in result_stream:
        raw_text = row[0]
        if raw_text:
            all_tokens.extend(tokenize(raw_text))

        # Чтобы список all_tokens не стал гигантским,
        # можно сбрасывать промежуточные результаты в Counter каждые 100к строк,
        # но для 600к строк обычный Counter в конце должен выдержать (это ~30-50МБ RAM).

    if not all_tokens:
        print("Нет данных.")
        return

    counts = Counter(all_tokens)
    del all_tokens  # явно освобождаем память

    data = [{"word": w, "hash": get_cached_hash(w), "freq": c} for w, c in counts.items()]

    for i in range(0, len(data), 5000):
        batch = data[i:i + 5000]
        stmt = insert(word_model).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=['word'], set_={'freq': word_model.freq + stmt.excluded.freq}
        )
        await session.execute(stmt)
        await session.commit()
