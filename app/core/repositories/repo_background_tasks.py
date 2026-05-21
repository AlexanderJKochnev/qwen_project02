# app.core.repositories.repo_backround_tasks.py
import asyncio
from typing import Any, Optional, Dict
from loguru import logger
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.project_config import settings
from app.core.hash_norm import get_word_hashes_dict
from app.core.models.base_model import get_model_by_name
from app.core.repositories.clickhouse_repository import ClickHouseRepository
from app.core.utils.backgound_tasks import background_unique
from app.core.utils.hashes import FastImageHasher
from app.core.utils.headers import content_type_magic, make_meta
from app.core.utils.image_processor import ImageProcessingConfig, ImageProcessor
from app.core.utils.reindexation import extract_text_optimized  # , extract_text_ultra_fast
from app.mongodb.service import ThumbnailImageService


class Background:
    """
        run_sync_background:            запуск фоновой синхронизации
            _get_item_drink_pairs:      Получаем ID пар ITEM_ID, DRINK_ID для обработки (индекс hash)
            _process_pairs:             Обработка пар ITEM_ID, DRINK_ID
                _load_drinks_batch:     Получение данных для чанка (словарь {drink_id: drink_dict}
                _process_chunk:         Обработка чанка
                    extract_text_optimized:     Извлечение текста из словаря
                _bulk_update_items:     Сохранение результата
                _bulk_upsert_wordhash:  Сохранение word hash
    """

    @classmethod
    def get_item_drink(cls, id: int):
        # переопределеяемый метод, для получения списка ids of Item отфильтрованного по id в связанной таблице
        # если не значит см ниже
        return select(None, None)

    @classmethod
    @background_unique
    async def run_sync_background(
            cls, start_model, start_id: int, path_str: str, session_factory, skip_keys: set
    ):
        """ Точка входа для фоновой синхронизации
            если start_model = None: полная реиндексация
        """
        if start_model:
            task_name = f"{start_model.__name__}_{start_id}"
        else:
            task_name = 'full_reindexation'
        logger.info(f"🚀 Начало фоновой синхронизации: {task_name}")

        async with session_factory() as session:
            try:
                # Получаем ID пар для обработки (индекс hash)
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
        если current_model == None - полная переиндексация
        """

        try:
            # Строим запрос
            if current_model:
                stmt = cls.get_item_drink(start_id)
                logger.debug(f"🔍 Выполнение запроса для {current_model.__name__}.{start_id}")
            else:
                logger.warning('full reindexation')
                ItemModel = cls._get_model('Item')
                # DrinkModel = cls._get_model('Drink')
                stmt = select(ItemModel.id, ItemModel.drink_id).where(ItemModel.drink_id.isnot(None))
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
        """Строит динамический запрос с JOIN
            УДАЛИТЬ
        """

        DrinkModel = cls._get_model('Drink')
        ItemModel = cls._get_model('Item')

        stmt = select(target_item.id, target_drink.id).select_from(start_model)
        current = start_model
        path_parts = path_str.split('.')
        logger.warning(f'{current=}, {path_parts=}')

        for part in path_parts:
            # Находим relationship
            mapper = inspect(current)
            rel_key = cls._find_relationship(mapper, part)

            if not rel_key:
                raise AttributeError(f"Связь {part} не найдена в {current.__name__} "
                                     f"проверяй аргументы декоратора @registers_search_update над классом модели "
                                     f"{part} и всех в цепочке до items")

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
        _process_pairs
        _load_drinks_batch
        _process_chunk
        _bulk_update_items
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
            drinks: Dict[Any, dict] = await cls._load_drinks_batch(session, chunk)
            # {drink_id: drink_dict}
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
    ) -> Dict[Any, Dict]:
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

        # Превращаем в словари (unique - только уникальные)
        drinks = {drink.id: drink.to_dict_fast() for drink in result.unique().scalars()}
        # drinks = {drink.id: drink.to_dict_fast() for drink in result.scalars()}
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
                content: str = extract_text_optimized(drink_dict, skip_keys)
            except Exception as e:
                logger.error(f"Ошибка извлечения текста для Drink {drink_id}: {e}")
                content = ""

            # Получаем хэши слов {word: hash}
            word_hashes_dict: dict = get_word_hashes_dict(content)

            # Готовим обновление
            updates.append(
                {'id': item_id, 'search_content': content, 'word_hashes': list(word_hashes_dict.values())}
            )

            # Собираем уникальные слова
            for word, hash_val in word_hashes_dict.items():
                if word not in word_hashes:
                    word_hashes[word] = hash_val
        # updated {id: , search_content: , word_hashes: }  индекс для items
        # word_hashes {word: hash} уникальные слова в словарь
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
                # это удалить
                item.search_content = update['search_content']
                # это оставить
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

    @classmethod
    @background_unique
    async def run_mongo_to_seaweed(
            cls, repository, model, image_service: ThumbnailImageService,
            click_repo: ClickHouseRepository, fs,
            session_factory):
        """
            запуск переноса изображений из mongodb в seaweed)
        """
        task_name = 'import_mongo_to_seaweed'
        logger.info(f"🚀 Начало фоновой синхронизации: {task_name}")
        contents: list = []
        ids: list = []
        tags: list = []
        hashes: list = []
        updates: list = []  # List[Dict[id:int, seaweed_fids: []]
        click_meta: list = []  # list of tuple meta
        config_fast = ImageProcessingConfig(**settings.imageprocessing_config)
        processor_fast = ImageProcessor(config_fast)

        async def image_processing():
            nonlocal contents
            nonlocal ids
            nonlocal tags
            nonlocal hashes
            nonlocal updates
            nonlocal click_meta
            result = await processor_fast.process_batch(contents, remove_bg=True)
            for id, content, tag, shash, (full_data, thumb_data, _) in zip(
                    ids, contents, tags, hashes, result):
                if len(content) <= 150000:
                    full_data = content
                # 1. load to seawweed
                fid = await fs.upload(full_data)
                fid_thumb = await fs.upload(thumb_data)
                mime_type, _, _ = content_type_magic(full_data)
                meta_data = make_meta(
                    fid, fid_thumb, full_data, thumb_data, tag, shash, 'items', mime_type
                )
                click_meta.append(meta_data)
                logger.warning(f'{id}, {meta_data.get('mime_type')}, {meta_data.get('size_bytes')},'
                               f' {meta_data.get('thumb_size_bytes')}')
                updates.append({'id': id, 'seaweed_fids': (fid, fid_thumb)})

            ids, tags, result, contents, hashes = [], [], [], [], []

        async def get_item_drink():
            async with session_factory() as session:
                response = await repository.get_item_drink(session)
                if not response:
                    logger.warning(f"⚠️ Нет данных для синхронизации: {task_name}")
                else:
                    logger.info(f"📊 Найдено {len(response)} записей для обработки")
                return response

        async def update_item_drink():
            async with session_factory() as session:
                response = await repository.bulk_update(updates, model, session)
                logger.info(f"📊 Обновлено {len(response)} записей в postgesql")
                return response

        response = await get_item_drink()
        if not response:
            return
        try:
            source_data = [(a.id, a.image_id, a.concat) for a in response]

            for id, image_id, tag in source_data:
                content: bytes = await image_service.get_full_image(image_id)
                source_hash = FastImageHasher.xxhash64(content)
                fid_thumb: tuple = await cls.hash_exists(source_hash, click_repo)
                if fid_thumb:
                    # message is available (defined by orinal image hash) - добавляем в items
                    updates.append({'id': id, 'seaweed_fids': fid_thumb})
                    logger.warning(f'hash found! {id}: {fid_thumb}')
                    continue
                hashes.append(source_hash)
                contents.append(content)
                ids.append(id)
                tags.append(tag)
                if len(contents) >= 20:
                    await image_processing()
            if ids:
                logger.warning(f'tail of cycle is {len(ids)}')
                await image_processing()
            from app.core.utils.common_utils import jprint
            jprint(updates)
            logger.warning('-----------------------------')
            # add to clickhouse
            if click_meta:
                await click_repo.bulk_insert(click_meta)
            # update postgresql
            await update_item_drink()
            # await session.commit()
            logger.success(f"✅ Синхронизация завершена: {task_name}, обновлено записей")
        except Exception as e:
            logger.error(f"❌ Ошибка синхронизации {task_name}: {e}")
            # await session.rollback()
            raise

    @classmethod
    async def hash_exists(cls, source_hash: int, click_repo: ClickHouseRepository) -> tuple:
        """
            проверка - существует ли уже изображение если до возвращает fis fid_thumb
        """
        res: dict = await click_repo.get_by_id(
            'data_hash', source_hash, ['fid', 'fid_thumb', 'tags']
        )
        if res:  # изображение с этим хэшем уже есть - просто возвращаем его без создания нового
            fid, fid_thumb, tags = res.values()
            return fid, fid_thumb
        return None
