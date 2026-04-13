from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from app.core.hash_norm import fast_normalize_v4, get_cached_hash
from app.support import Item
from app.support.hashing.model import WordHash
from collections import Counter


async def seed_word_dictionary_v2(session: AsyncSession):
    # 1. Загружаем данные
    result = await session.execute(select(Item.search_content).where(Item.search_content != None))

    # 2. Собираем ВСЕ токены из всех строк в один плоский список
    # Это быстрее, чем обновлять словарь на каждой итерации
    all_tokens = []
    for raw_text in result.scalars():
        _, tokens = fast_normalize_v4(raw_text)
        all_tokens.extend(tokens)

    if not all_tokens:
        return

    # 3. Уникальные значения и их количество одним махом (через Counter на базе хеш-таблиц C)
    counts = Counter(all_tokens)

    # 4. Формируем финальный список для вставки
    # Хеши берем из кэша (они там уже лежат после шага 2)
    data_to_insert = [{"word": w, "hash": get_cached_hash(w), "freq": c} for w, c in counts.items()]

    # 5. Массовая вставка батчами
    for i in range(0, len(data_to_insert), 5000):
        batch = data_to_insert[i: i + 5000]
        # Так как данные внутри батча уникальны (благодаря Counter),
        # ON CONFLICT сработает только для старых данных в БД
        stmt = insert(WordHash).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=['word'], set_={'freq': WordHash.freq + stmt.excluded.freq}
        )
        await session.execute(stmt)

    await session.commit()
    print(f"Обработано {len(counts)} уникальных слов.")
