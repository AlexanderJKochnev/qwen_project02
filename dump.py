from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import aliased
import asyncio
from typing import List, Dict
from loguru import logger


@classmethod
async def sync_items_by_path(
        cls, session: AsyncSession, current_model, start_id: int, path_str: str, skip_keys: set
) -> int:
    """Оптимизированная версия для 600к записей"""

    try:
        ItemModel = get_model_by_name('Item')
        DrinkModel = get_model_by_name('Drink')
        WordHashModel = get_model_by_name('WordHash')

        target_drink = aliased(DrinkModel)
        target_item = aliased(ItemModel)

        # 1. Получаем ID всех записей одной операцией
        stmt = select(target_item.id, target_drink.id).select_from(current_model)

        active_model_class = current_model
        path_parts = path_str.split('.')

        for part in path_parts:
            mapper = inspect(active_model_class)
            rel_key = next(
                (r.key for r in mapper.relationships if r.mapper.class_.__name__.lower() == part.lower()), None
            )
            if not rel_key:
                raise AttributeError(f"Связь '{part}' не найдена")

            next_model_class = getattr(active_model_class, rel_key).property.mapper.class_

            if next_model_class == DrinkModel:
                step_target = target_drink
            elif next_model_class == ItemModel:
                step_target = target_item
            else:
                step_target = next_model_class

            stmt = stmt.join(step_target, getattr(active_model_class, rel_key))
            active_model_class = next_model_class

        stmt = stmt.where(current_model.id == start_id)
        result = await session.execute(stmt)
        ids = result.all()  # [(item_id, drink_id), ...]

        if not ids:
            return 0

        # 2. Получаем все Drink записи одним запросом
        drink_ids = list(set([drink_id for _, drink_id in ids]))

        drink_stmt = select(DrinkModel).where(DrinkModel.id.in_(drink_ids))
        drink_result = await session.execute(drink_stmt)
        drinks = {drink.id: drink.to_dict_fast() for drink in drink_result.scalars()}

        # 3. Получаем все Item записи одним запросом
        item_ids = [item_id for item_id, _ in ids]
        item_stmt = select(ItemModel).where(ItemModel.id.in_(item_ids))
        item_result = await session.execute(item_stmt)
        items = {item.id: item for item in item_result.scalars()}

        # 4. Пакетная обработка (чанками по 1000 записей)
        chunk_size = 1000
        all_word_hashes = []

        for i in range(0, len(items), chunk_size):
            chunk_items = list(items.items())[i:i + chunk_size]

            # Собираем данные для этого чанка
            for item_id, item_obj in chunk_items:
                # Находим соответствующий drink
                drink_id = next((did for iid, did in ids if iid == item_id), None)
                if not drink_id or drink_id not in drinks:
                    continue

                drink_dict = drinks[drink_id]
                content = extract_text_ultra_fast(drink_dict, skip_keys).lower()

                # Получаем хэши слов
                word_hashes_dict = get_word_hashes_dict(content)
                item_obj.word_hashes = list(word_hashes_dict.values())
                item_obj.search_content = content

                # Готовим данные для WordHash
                for word, hash_val in word_hashes_dict.items():
                    all_word_hashes.append(
                        {'word': word, 'hash': hash_val, 'freq': 1}
                    )

            # Обновляем Item чанком
            await session.flush()

            # Даем время другим задачам
            if i % (chunk_size * 10) == 0:
                await asyncio.sleep(0.01)

        # 5. Массовое обновление WordHash одной операцией
        if all_word_hashes:
            from sqlalchemy.dialects.postgresql import insert as pg_insert

            # Группируем по словам для суммирования частоты
            word_freq = {}
            for wh in all_word_hashes:
                word_freq[wh['word']] = word_freq.get(wh['word'], 0) + 1

            # Подготавливаем финальные данные
            final_hashes = [{'word': word, 'hash': get_word_hash(word), 'freq': freq} for word, freq in
                            word_freq.items()]

            # Один массовый upsert
            stmt = pg_insert(WordHashModel).values(final_hashes)
            stmt = stmt.on_conflict_do_update(
                index_elements=['word'], set_={'freq': WordHashModel.freq + stmt.excluded.freq}
            )
            await session.execute(stmt)

        await session.flush()
        logger.success(f'Обновлено {len(items)} записей')
        return len(items)

    except Exception as e:
        raise AppBaseException(message=f'sync_items_by_path.error; {str(e)}', status_code=404)
