# app.core.repository.clickhouse_repository.py
"""
    Метод	Назначение
    create()	Создание одной записи
    bulk_insert()	Массовая вставка (сотни/тысячи записей)
    get_by_id()	Получение по ID
    get_all()	Все записи с фильтрацией и пагинацией
    search()	Поиск по массиву тегов
    update()	Обновление (через версионирование)
    soft_delete()	Мягкое удаление
    soft_delete_batch()	Массовое мягкое удаление
    cleanup_deleted()	Физическое удаление старых записей
    cleanup_old_versions()	Очистка старых версий
"""
from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from clickhouse_connect.driver.asyncclient import AsyncClient
from pypika import Table, Query, Order, functions as fn, CustomFunction
from loguru import logger


class ClickHouseRepository:
    """
    Универсальный асинхронный репозиторий для работы с ClickHouse.
    ОСОБЕННОСТИ - НЕ ЗАБЫВАТЬ:
    CREATE = INSERT
    UPDATE = INSERT (точно указать уникальные ключи! если предполагается и их изименение - тогда DELETE + INSERT)
    DELETE = INSERT (deleted_at=1, остальные поля оставить пустые)
    ПОКА ЖЕСТКО ЗАШИТА ПОД ТАБЛИЦУ images_metadata
    НУЖНО ОБЕСПЕЧИТЬ ЧТО БЫ В WHERE подставлялись поля из ORDER BY (это уникальные индексы по ним идентифицируется
    запись и ее версия
    """

    def __init__(self, client: AsyncClient, table_name: str):
        """
        Args:
            client: ClickHouse async client
            table_name: Имя таблицы (в формате 'database.table' или просто 'table')
            soft_delete_field: Имя поля для хранения времени мягкого удаления
        """
        self.client = client
        self.table_name = table_name  # таблица для create/update/delete (можно также посмотреть/восстановить
        # удаленные записи
        self.select_table = f'{table_name}_active'
        self.deleted_at = 'deleted_at'
        self.orderby = ['fid', 'table']

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создание одной записи
        Args: data: Словарь с данными для вставки
        Returns: Вставленные данные
        """
        columns = list(data.keys())
        values = list(data.values())
        events = Table(self.table_name)
        q = Query.into(events).columns(*columns).insert(*values)
        print(q.get_sql())
        logger.critical('-----------------')
        await self.client.query(q.get_sql())
        return data

    async def bulk_insert(self, records: List[Dict[str, Any]]) -> int:
        """
        ПЕРЕДЕЛАТЬ
        Массовая вставка записей.

        Args:
            records: Список словарей с данными
            version_field: Имя поля версии

        Returns:
            Количество вставленных записей
        """
        if not records:
            return 0

        # Подготавливаем все записи
        prepared_records = []
        for record in records:
            record = record.copy()
            prepared_records.append(record)

        # Получаем все уникальные колонки
        all_columns = set()
        for record in prepared_records:
            all_columns.update(record.keys())
        columns = list(all_columns)

        # Формируем данные для вставки
        values = []
        for record in prepared_records:
            row = [record.get(col) for col in columns]
            values.append(row)

        query = f"""
            INSERT INTO {self.table_name} ({', '.join(columns)})
            VALUES ({', '.join(['%s'] * len(columns))})
        """

        await self.client.execute(query, values)
        return len(prepared_records)

    # ============================================================
    # READ
    # ============================================================

    async def get_by_id(
            self, id_field: str, id_value: Any, fields: list = None,
            order_by: str = 'inserted_at DESC'
    ) -> Optional[Dict[str, Any]]:
        """
        Получение записи по ID.

        Args:
            id_field: Имя поля ID
            id_value: Значение ID
        """
        # events = Table(self.table_name)
        events = Table(self.select_table)
        if fields:
            q = Query.from_(events).select(*(events[k] for k in fields))
        else:
            q = Query.from_(events)
        q = q.where(events[id_field] == id_value)
        if order_by:
            if 'DESC' in order_by:
                order_by = order_by.replace('DESC', '').strip()
                q = q.orderby(events[order_by], order=Order.desc)
            else:
                q = q.orderby(order_by)
        q = q.limit(1)
        print(q.get_sql())
        result = await self.client.query(q.get_sql())
        # result = await self.client.query(query, {'id': id_value})
        return result.first_item if result.row_count > 0 else None

    async def get(
            self,
            order_by: Optional[str] = None, limit: int = 30, page: int = 1, fields: list = None
    ) -> List[Dict[str, Any]]:
        """
        Получение всех записей с фильтрацией и пагинацией.
        Args:
            filters: Словарь фильтров {поле: значение}
            include_deleted: Включать мягко удаленные записи
            order_by: Сортировка (например, 'created_at DESC')
            limit: Лимит записей
            offset: Смещение
            fields - возвращаемые поля
        """
        # events = Table(self.table_name)
        events = Table(self.select_table)
        if fields:
            q = Query.from_(events).select(*(events[k] for k in fields))
        else:
            q = Query.from_(events)
        if limit:
            q = q.limit(limit)
        if page:
            q = q.offset((page - 1) * limit)
        if order_by:
            if 'DESC' in order_by:
                order_by = order_by.replace('DESC', '').strip()
                q = q.orderby(events[order_by], order=Order.desc)
            else:
                q = q.orderby(order_by)
        # print(q.get_sql())
        result = await self.client.query(q.get_sql())
        if result.row_count == 0:
            return []
        data: List[dict] = [dict(zip(result.column_names, row)) for row in result.result_rows]
        return data

    async def search(
            self, search_field: str, search_value: str, filters: Optional[Dict[str, Any]] = None,
            limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Текстовый поиск по полю. ПЕРЕДЕЛАТЬ
        SELECT * FROM images_metadata_active WHERE has(tags, 'my_tag') для поиска по тэгам
        has_tag = CustomFunction("has", ["array", "value"])
        target_tag = "nature"
        if target_tag:
            q = q.where(has_tag(images.tags, target_tag))
        Args:
            search_field: Поле для поиска (массив строк)
            search_value: Значение для поиска (токен)
            filters: Дополнительные фильтры
            include_deleted: Включать мягко удаленные
            limit: Лимит
            offset: Смещение
        """
        where_conditions = [f"has({search_field}, %(search)s)"]
        params = {'search': search_value}

        if filters:
            for key, value in filters.items():
                where_conditions.append(f"{key} = %(__{key})s")
                params[f"__{key}"] = value

        where_clause = "WHERE " + " AND ".join(where_conditions)

        query = f"""
            SELECT * FROM {self.table_name}
            {where_clause}
            ORDER BY uploaded_at DESC
            LIMIT {limit}
            OFFSET {offset}
        """

        result = await self.client.query(query, parameters=params)
        return result.result_rows_as_dict

    # ============================================================
    # UPDATE (через версионирование)
    # ============================================================

    async def update(
            self, id_field: str, id_value: Any, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Обновление записи (создается новая версия, старая "удаляется").
        если обновляется ключевое поле (id_field) - это delete + insert
        если любые другие это insert поверх прежней записи
        Args:
            id_field: Имя поля ID
            id_value: Значение ID
            data: Новые данные

        Returns:
            Новая версия записи
        """
        if data.get(id_field) is None:
            data[id_field] = id_value
        if data.get[id_field] != id_value:
            # DELETE PREV VERSION
            table_name = data.get['table']
            try:
                events = Table(self.table_name)
                # events = Table(self.select_table)
                q = (Query.into(events).columns(
                    events[id_field], events['table'], events[self.deleted_at]
                ).insert(id_value, table_name, 1))
                _ = await self.client.command(q.get_sql())
            except Exception as e:
                pass  # на сулчай если запись не существует - пропускаем ошибку и создаем новую
        result = await self.create(data)
        return result

    # ============================================================
    # DELETE (soft delete)
    # ============================================================

    async def soft_delete(
            self, id_field: str, id_value: Any, table_name: str
    ) -> bool:
        """
        Мягкое удаление записи (заполняется deleted_at).

        Returns:
            True если удалили хотя бы одну запись
        """
        events = Table(self.table_name)
        # events = Table(self.select_table)

        q = (Query.into(events).columns(events[id_field],
                                        events['table'],
                                        events[self.deleted_at])
             .insert(id_value, table_name, 1))
        _ = await self.client.command(q.get_sql())
        return True  # Если нет ошибки - считаем успехом

    async def soft_delete_batch(
            self, id_field: str, id_values: List[Any]
    ) -> int:
        """
        ПЕРЕДЕЛАТЬ
        Массовое мягкое удаление записей.

        Returns:
            Количество помеченных на удаление записей
        """
        if not id_values:
            return 0

        query = f"""
            ALTER TABLE {self.table_name}
            UPDATE {self.soft_delete_field} = now()
            WHERE {id_field} IN %(ids)s AND {self.soft_delete_field} IS NULL
        """

        await self.client.command(query, {'ids': tuple(id_values)})
        return len(id_values)

    # ============================================================
    # ОЧИСТКА (удаление физическое) автоматически через 30 дней
    # ============================================================


# ============================================================
# ФАБРИКА ДЛЯ БЫСТРОГО СОЗДАНИЯ РЕПОЗИТОРИЕВ
# ============================================================

class ClickHouseRepositoryFactory:
    """Фабрика для создания репозиториев с предустановленным клиентом."""

    def __init__(self, client: AsyncClient):
        self.client = client

    def for_table(self, table_name: str) -> ClickHouseRepository:
        """Создать репозиторий для конкретной таблицы."""
        return ClickHouseRepository(self.client, table_name)
