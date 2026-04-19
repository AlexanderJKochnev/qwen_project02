# app.core.repositories.repo_backround_tasks.py
import asyncio
from typing import Any, Optional

from loguru import logger
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from app.core.utils.alchemy_utils import get_sql_from_query
from app.core.hash_norm import get_word_hashes_dict
from app.core.models.base_model import get_model_by_name
from app.core.utils.backgound_tasks import background_unique
from app.core.utils.reindexation import extract_text_optimized, extract_text_ultra_fast


class Background:

    @classmethod
    @background_unique
    async def run_sync_background(
            cls, start_model, start_id: int, path_str: str, session_factory, skip_keys: set
    ):
        """Точка входа для фоновой синхронизации"""
        task_name = f"{start_model.__name__}_{start_id}"
        logger.info(f"🚀 Начало фоновой синхронизации: {task_name}")

        async with session_factory() as session:
            try:
                # Получаем ID пар для обработки
                pairs = await cls._get_item_drink_pairs(
                    session, start_model, start_id, path_str
                )

                if not pairs:
                    logger.warning(f"⚠️ Нет данных для синхронизации: {task_name}")
                    return

                logger.info(f"📊 Найдено {len(pairs)} записей для обработки")

                # Обрабатываем с прогресс-баром
                updated_count = await cls._process_pairs(
                    session, pairs, skip_keys
                )

                await session.commit()
                logger.success(f"✅ Синхронизация завершена: {task_name}, обновлено {updated_count} записей")

            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Ошибка синхронизации {task_name}: {e}")
                raise

    @classmethod
    async def _get_item_drink_pairs(
            cls, session: AsyncSession, current_model, start_id: int, path_str: str
    ) -> list:
        """
        Возвращает список пар [(item_id, drink_id), ...]
        """

        try:
            ItemModel = cls._get_model('Item')
            DrinkModel = cls._get_model('Drink')

            target_drink = aliased(DrinkModel)
            target_item = aliased(ItemModel)

            # Строим запрос
            stmt = cls._build_join_query(
                current_model, target_item, target_drink, path_str
            )
            stmt = stmt.where(current_model.id == start_id)
            logger.warning(f'{get_sql_from_query(stmt)=}')
            logger.debug(f"🔍 Выполнение запроса для {current_model.__name__}.{start_id}")

            result = await session.execute(stmt)
            pairs = [(item_id, drink_id) for item_id, drink_id in result.all()]

            logger.debug(f"📋 Получено {len(pairs)} пар Item-Drink")
            return pairs

        except Exception as e:
            logger.error(f"Ошибка получения пар: {e}")
            raise

    @staticmethod
    def _get_model(model_name: str):
        """Безопасное получение модели"""
        model = get_model_by_name(model_name)
        if not model:
            raise ValueError(f"Модель {model_name} не найдена")
        return model

    @classmethod
    def _build_join_query(cls, start_model, target_item, target_drink, path_str: str):
        """Строит динамический запрос с JOIN"""

        DrinkModel = cls._get_model('Drink')
        ItemModel = cls._get_model('Item')

        stmt = select(target_item.id, target_drink.id).select_from(start_model)
        current = start_model
        path_parts = path_str.split('.')

        for part in path_parts:
            # Находим relationship
            mapper = inspect(current)
            rel_key = cls._find_relationship(mapper, part)

            if not rel_key:
                raise AttributeError(f"Связь '{part}' не найдена в {current.__name__}")

            # Определяем следующий класс
            next_model = getattr(current, rel_key).property.mapper.class_

            # Выбираем алиас
            if next_model == DrinkModel:
                step_target = target_drink
            elif next_model == ItemModel:
                step_target = target_item
            else:
                step_target = next_model

            # Добавляем JOIN
            stmt = stmt.join(step_target, getattr(current, rel_key))
            current = next_model

        return stmt

    @staticmethod
    def _find_relationship(mapper, part_name: str) -> Optional[str]:
        """Ищет relationship по имени"""
        part_lower = part_name.lower()
        for rel in mapper.relationships:
            if rel.mapper.class_.__name__.lower() == part_lower:
                return rel.key
        return None

    @classmethod
    async def _process_pairs(
            cls, session: AsyncSession, pairs: list, skip_keys: set
    ) -> int:
        """
        Обрабатывает пары (item_id, drink_id) с логированием прогресса
        """
        chunk_size = 1500
        total = len(pairs)
        updated_count = 0
        all_word_hashes = {}

        logger.info(f"🔄 Начало обработки {total} записей")

        # Логируем прогресс каждые 5%
        next_log_percent = 5
        start_time = asyncio.get_event_loop().time()

        for i in range(0, total, chunk_size):
            chunk = pairs[i:i + chunk_size]

            # Получаем Drink данные для чанка
            drinks = await cls._load_drinks_batch(session, chunk)

            # Обрабатываем чанк
            chunk_updates, chunk_hashes = await cls._process_chunk(
                chunk, drinks, skip_keys
            )

            # Сохраняем результаты
            if chunk_updates:
                await cls._bulk_update_items(session, chunk_updates)
                updated_count += len(chunk_updates)

            # Накопливаем WordHash
            for word, hash_val in chunk_hashes.items():
                if word not in all_word_hashes:
                    all_word_hashes[word] = hash_val

            # Логируем прогресс
            current_percent = (updated_count / total) * 100
            if current_percent >= next_log_percent:
                elapsed = asyncio.get_event_loop().time() - start_time
                speed = updated_count / elapsed if elapsed > 0 else 0
                logger.info(
                    f"📈 Прогресс: {current_percent:.1f}% "
                    f"({updated_count}/{total}) "
                    f"скорость: {speed:.0f} зап/сек"
                )
                next_log_percent += 5

            # Даем время другим задачам
            await asyncio.sleep(0.01)

        # Финальный лог
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.success(
            f"✅ Обработка завершена: {updated_count} записей за {elapsed:.1f} сек, "
            f"средняя скорость: {updated_count / elapsed:.0f} зап/сек"
        )

        # Сохраняем WordHash
        if all_word_hashes:
            await cls._bulk_upsert_wordhash(session, all_word_hashes)
            logger.info(f"💾 WordHash: сохранено {len(all_word_hashes)} уникальных слов")

        return updated_count

    @classmethod
    async def _load_drinks_batch(
            cls, session: AsyncSession, chunk: list
    ) -> dict:
        """
        Загружает Drink данные для чанка пар
        Возвращает словарь {drink_id: drink_dict}
        """
        from app.support.drink.repository import DrinkRepository
        DrinkModel = cls._get_model('Drink')
        # Получаем уникальные drink_id
        drink_ids = list(set([drink_id for _, drink_id in chunk]))
        stmt = DrinkRepository.get_query(DrinkModel)
        # Загружаем Drink объекты
        stmt = stmt.where(DrinkModel.id.in_(drink_ids))
        result = await session.execute(stmt)

        # Превращаем в словари
        # drinks = {drink.id: drink.to_dict_fast() for drink in result.unique().scalars()}
        drinks = {drink.id: drink.to_dict_fast() for drink in result.scalars()}
        logger.debug(f"📦 Загружено {len(drinks)} Drink записей")
        return drinks
        drinks = {}
        for drink in result.scalars():
            try:
                drinks[drink.id] = drink.to_dict_fast()
            except Exception as e:
                logger.warning(f"⚠️ Ошибка преобразования Drink {drink.id}: {e}")
                drinks[drink.id] = {}

        logger.debug(f"📦 Загружено {len(drinks)} Drink записей")
        return drinks

    @classmethod
    async def _process_chunk(
            cls, chunk: list, drinks: dict, skip_keys: set
    ) -> tuple[list, dict]:
        """
        Обрабатывает чанк пар
        Возвращает (updates, word_hashes)
        """
        updates = []
        word_hashes = {}

        for item_id, drink_id in chunk:
            drink_dict = drinks.get(drink_id)

            if not drink_dict:
                logger.debug(f"⚠️ Drink {drink_id} не найден для Item {item_id}")
                continue

            # Извлекаем текст
            try:
                # content = extract_text_ultra_fast(drink_dict, skip_keys)
                content = extract_text_optimized(drink_dict, skip_keys)
            except Exception as e:
                logger.error(f"Ошибка извлечения текста для Drink {drink_id}: {e}")
                content = ""

            # Получаем хэши слов
            word_hashes_dict = get_word_hashes_dict(content)

            # Готовим обновление
            updates.append(
                {'id': item_id, 'search_content': content, 'word_hashes': list(word_hashes_dict.values())}
            )

            # Собираем уникальные слова
            for word, hash_val in word_hashes_dict.items():
                if word not in word_hashes:
                    word_hashes[word] = hash_val

        return updates, word_hashes

    @classmethod
    async def _bulk_update_items(cls, session: AsyncSession, updates: list):
        """Массовое обновление Item полей"""
        if not updates:
            return

        ItemModel = cls._get_model('Item')

        # Получаем все Item одним запросом
        item_ids = [u['id'] for u in updates]
        stmt = select(ItemModel).where(ItemModel.id.in_(item_ids))
        result = await session.execute(stmt)
        items = {item.id: item for item in result.scalars()}

        # Обновляем поля
        updated = 0
        for update in updates:
            item = items.get(update['id'])
            if item:
                item.search_content = update['search_content']
                item.word_hashes = update['word_hashes']
                updated += 1

        await session.flush()
        logger.debug(f"✏️ Обновлено Item: {updated}/{len(updates)}")

    @classmethod
    async def _bulk_upsert_wordhash(cls, session: AsyncSession, word_hashes: dict):
        """Добавляет новые слова и обновляет частоту существующих"""
        if not word_hashes:
            return

        from sqlalchemy.dialects.postgresql import insert as pg_insert

        WordHashModel = cls._get_model('WordHash')

        # Подготавливаем данные
        values = [{'word': word, 'hash': hash_val, 'freq': 1} for word, hash_val in word_hashes.items()]

        chunk_size = 2000
        total = 0
        real_total = 0
        for i in range(0, len(values), chunk_size):
            chunk = values[i:i + chunk_size]
            stmt = pg_insert(WordHashModel).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=['word'], set_={'freq': WordHashModel.freq + stmt.excluded.freq}
            )
            tmp = await session.execute(stmt)
            real_total += tmp.rowcount
            total += len(chunk)

        await session.flush()
        logger.success(f"💾 WordHash: обработано {total} слов (добавлены новые, обновлена частота существующих) "
                       f"{real_total}")

    def extract_text_optimized(data: Any, skip_keys: set = None) -> str:
        """
        Извлекает текст из глубоко вложенных словарей
        Без рекурсии, через стек
        """
        if skip_keys is None:
            skip_keys = {'id', 'created_at', 'updated_at', 'deleted_at', 'version', 'is_deleted'}

        parts = []
        stack = [data]

        while stack:
            current = stack.pop()

            if isinstance(current, dict):
                for key, value in current.items():
                    if key not in skip_keys:
                        if isinstance(value, (dict, list)):
                            stack.append(value)
                        elif isinstance(value, str) and value.strip():
                            # Быстрая очистка строки
                            cleaned = value.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                            if '  ' in cleaned:
                                cleaned = ' '.join(cleaned.split())
                            parts.append(cleaned)
                        elif isinstance(value, (int, float, bool)):
                            parts.append(str(value))
            elif isinstance(current, list):
                # Добавляем элементы в обратном порядке для сохранения порядка
                stack.extend(reversed(current))

        return ' '.join(parts)


"""
    class YourService:
        @classmethod
        @background_unique
        async def run_sync_background(cls, start_model, start_id: int,
                                       path_str: str, session_factory, skip_keys: set):
            await cls._run_sync_background_impl(
                start_model, start_id, path_str, session_factory, skip_keys
            )

    # В эндпоинте
    @app.post("/sync")
    async def sync_endpoint(background_tasks: BackgroundTasks):
        await YourService.run_sync_background(
            start_model=Category,
            start_id=1,
            path_str="items.drink",
            session_factory=DatabaseManager.session_maker,
            skip_keys={'id', 'created_at'},
            background_tasks=background_tasks
        )
        return {"message": "Синхронизация запущена"}
"""
