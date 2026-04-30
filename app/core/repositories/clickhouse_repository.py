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

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from clickhouse_connect.driver.asyncclient import AsyncClient


class ClickHouseRepository:
    """
    Универсальный асинхронный репозиторий для работы с ClickHouse.

    Поддерживает:
    - Soft delete (помечает записи как удаленные)
    - Версионирование для UPDATE
    - Batch insert
    - Пагинацию
    - Очистку удаленных и старых версий
    """

    def __init__(self, client: AsyncClient, table_name: str, soft_delete_field: str = 'deleted_at'):
        """
        Args:
            client: ClickHouse async client
            table_name: Имя таблицы (в формате 'database.table' или просто 'table')
            soft_delete_field: Имя поля для хранения времени мягкого удаления
        """
        self.client = client
        self.table_name = table_name
        self.soft_delete_field = soft_delete_field

    # ============================================================
    # CREATE
    # ============================================================

    async def create(self, data: Dict[str, Any], version_field: str = 'version') -> Dict[str, Any]:
        """
        Создание одной записи с поддержкой версионирования.

        Args:
            data: Словарь с данными для вставки
            version_field: Имя поля версии

        Returns:
            Вставленные данные с добавленной версией
        """
        # Добавляем версию если поле существует
        if version_field not in data:
            data[version_field] = 1
        else:
            data[version_field] = int(data.get(version_field, 0)) + 1

        # Убираем soft delete поле если оно было передано
        data.pop(self.soft_delete_field, None)

        columns = list(data.keys())
        values = list(data.values())

        query = f"""
            INSERT INTO {self.table_name} ({', '.join(columns)})
            VALUES ({', '.join(['%s'] * len(columns))})
        """

        await self.client.execute(query, values)
        return data

    async def bulk_insert(self, records: List[Dict[str, Any]], version_field: str = 'version') -> int:
        """
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
            record.pop(self.soft_delete_field, None)

            if version_field not in record:
                record[version_field] = 1
            else:
                record[version_field] = int(record.get(version_field, 0)) + 1

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
            self, id_field: str, id_value: Any, include_deleted: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Получение записи по ID.

        Args:
            id_field: Имя поля ID
            id_value: Значение ID
            include_deleted: Включать мягко удаленные записи
        """
        deleted_condition = '' if include_deleted else f'AND {self.soft_delete_field} IS NULL'

        query = f"""
            SELECT * FROM {self.table_name}
            WHERE {id_field} = %(id)s
            {deleted_condition}
            ORDER BY version DESC
            LIMIT 1
        """

        result = await self.client.query(query, {'id': id_value})
        return result.first_item if result.row_count > 0 else None

    async def get(
            self, filters: Optional[Dict[str, Any]] = None, include_deleted: bool = False,
            order_by: Optional[str] = None, limit: int = 30, page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Получение всех записей с фильтрацией и пагинацией.

        Args:
            filters: Словарь фильтров {поле: значение}
            include_deleted: Включать мягко удаленные записи
            order_by: Сортировка (например, 'created_at DESC')
            limit: Лимит записей
            offset: Смещение
        """
        offset = limit * (page - 1)
        where_conditions = []
        params = {}

        # Фильтр по мягкому удалению
        if not include_deleted:
            where_conditions.append(f"{self.soft_delete_field} IS NULL")

        # Пользовательские фильтры
        if filters:
            for key, value in filters.items():
                if isinstance(value, (list, tuple)):
                    # IN условие
                    placeholders = [f"__{key}_{i}" for i in range(len(value))]
                    where_conditions.append(f"{key} IN ({', '.join(['%(' + p + ')s' for p in placeholders])})")
                    for i, v in enumerate(value):
                        params[f"{key}_{i}"] = v
                elif isinstance(value, dict):
                    # Диапазон (gt, gte, lt, lte, like)
                    op = value.get('op', '=')
                    param_name = f"__{key}"
                    if op == 'like':
                        where_conditions.append(f"{key} LIKE %({param_name})s")
                        params[param_name] = value['value']
                    else:
                        where_conditions.append(f"{key} {op} %({param_name})s")
                        params[param_name] = value['value']
                else:
                    where_conditions.append(f"{key} = %(__{key})s")
                    params[f"__{key}"] = value

        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        order_clause = f"ORDER BY {order_by}" if order_by else ""

        query = f"""
            SELECT * FROM {self.table_name}
            {where_clause}
            {order_clause}
            LIMIT {limit}
            OFFSET {offset}
        """

        result = await self.client.query(query)
        if result.row_count == 0:
            return []
        data: List[dict] = [dict(zip(result.column_names, row)) for row in result.result_rows]
        return data

    async def search(
            self, search_field: str, search_value: str, filters: Optional[Dict[str, Any]] = None,
            include_deleted: bool = False, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Текстовый поиск по полю.

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

        if not include_deleted:
            where_conditions.append(f"{self.soft_delete_field} IS NULL")

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
            self, id_field: str, id_value: Any, data: Dict[str, Any], version_field: str = 'version'
    ) -> Optional[Dict[str, Any]]:
        """
        Обновление записи (создается новая версия, старая помечается удаленной).

        Args:
            id_field: Имя поля ID
            id_value: Значение ID
            data: Новые данные
            version_field: Имя поля версии

        Returns:
            Новая версия записи
        """
        # Получаем текущую версию
        current = await self.get_by_id(id_field, id_value, include_deleted=True)
        if not current:
            return None

        # Помечаем старую как удаленную
        await self.soft_delete(id_field, id_value)

        # Создаем новую с увеличенной версией
        new_data = {**current, **data}
        new_data.pop(self.soft_delete_field, None)
        new_data[version_field] = current.get(version_field, 0) + 1
        new_data.pop(id_field, None)  # ID не меняем

        # Вставляем новую версию
        columns = [id_field] + list(new_data.keys())
        values = [id_value] + list(new_data.values())

        query = f"""
            INSERT INTO {self.table_name} ({', '.join(columns)})
            VALUES ({', '.join(['%s'] * len(columns))})
        """

        await self.client.execute(query, values)

        # Возвращаем новую запись
        return await self.get_by_id(id_field, id_value)

    # ============================================================
    # DELETE (soft delete)
    # ============================================================

    async def soft_delete(
            self, id_field: str, id_value: Any
    ) -> bool:
        """
        Мягкое удаление записи (заполняется deleted_at).

        Returns:
            True если удалили хотя бы одну запись
        """
        query = f"""
            ALTER TABLE {self.table_name}
            UPDATE {self.soft_delete_field} = now()
            WHERE {id_field} = %(id)s AND {self.soft_delete_field} IS NULL
        """
        _ = await self.client.command(query, {'id': id_value})
        # ClickHouse ALTER UPDATE возвращает строку, извлечем количество обновленных строк
        return True  # Если нет ошибки - считаем успехом

    async def soft_delete_batch(
            self, id_field: str, id_values: List[Any]
    ) -> int:
        """
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
    # ОЧИСТКА (удаление физическое)
    # ============================================================

    async def cleanup_deleted(
            self, older_than_days: int = 30
    ) -> int:
        """
        Физическое удаление записей, помеченных как удаленные и старых версий.

        Args:
            older_than_days: Удалять записи старше N дней после мягкого удаления

        Returns:
            Количество удаленных записей
        """
        cutoff_date = datetime.now() - timedelta(days=older_than_days)

        query = f"""
            ALTER TABLE {self.table_name}
            DELETE WHERE {self.soft_delete_field} IS NOT NULL
            AND {self.soft_delete_field} < %(cutoff)s
        """

        await self.client.command(query, {'cutoff': cutoff_date})
        # Возвращаем примерное количество (ClickHouse не возвращает точное число при DELETE)
        return -1  # Индикатор успеха

    async def cleanup_old_versions(
            self, id_field: str, keep_last_n: int = 1, older_than_days: Optional[int] = None
    ) -> int:
        """
        Очистка старых версий записей (для освобождения места).

        Args:
            id_field: Имя поля ID
            keep_last_n: Сколько последних версий оставить
            older_than_days: Дополнительное ограничение по возрасту

        Returns:
            Количество удаленных записей
        """
        # Сложный запрос для удаления старых версий
        # Для каждой группы по id оставляем только top N по версии + свежие
        age_filter = f"AND {self.soft_delete_field} < now() - INTERVAL {older_than_days} DAY" if older_than_days else ""

        query = f"""
            ALTER TABLE {self.table_name}
            DELETE WHERE ({id_field}, version) NOT IN (
                SELECT {id_field}, version FROM (
                    SELECT {id_field}, version,
                           row_number() OVER (PARTITION BY {id_field} ORDER BY version DESC, inserted_at DESC) as rn
                    FROM {self.table_name}
                    WHERE {self.soft_delete_field} IS NOT NULL {age_filter}
                ) WHERE rn <= {keep_last_n}
            ) AND {self.soft_delete_field} IS NOT NULL
        """

        await self.client.command(query)
        return -1  # Индикатор успеха


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
