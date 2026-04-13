from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from app.core.hash_norm import fast_normalize_v2
from app.support import Item
from app.support.hashing.model import WordHash


async def seed_word_dictionary(session: AsyncSession):
    # 1. Извлекаем сырой текст из текущей колонки search_content
    # (Берем только те, где есть текст)
    result = await session.execute(select(Item.search_content).where(Item.search_content.is_not(None)))

    word_map = {}  # word -> {hash, freq}

    for row in result.scalars():
        # Используем нашу новую логику фильтрации
        hashes, tokens = fast_normalize_v2(row)

        for i, h in enumerate(hashes):
            word = tokens[i]  # Упрощенно, для сопоставления слова и хеша
            if word not in word_map:
                word_map[word] = {"hash": h, "freq": 0}
            word_map[word]["freq"] += 1

    # 2. Массовая вставка в wordhashs
    # Готовим объекты для Upsert
    for word, data in word_map.items():
        stmt = insert(WordHash).values(
            word=word, hash=data["hash"], freq=data["freq"]
        ).on_conflict_do_update(
            index_elements=['word'], set_=dict(freq=WordHash.freq + data["freq"])
        )
        await session.execute(stmt)

    await session.commit()
