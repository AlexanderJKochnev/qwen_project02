# tests/test_search.py
"""
    тестируем все методы SEARCH
    новые методы добавляются автоматически
"""

# from collections import Counter
from typing import Any, Dict, List  # NOQA: F401
from sqlalchemy import func, or_, select, and_, sql  # NOQA: F401
from sqlalchemy.sql import visitors
from sqlalchemy.dialects.postgresql import dialect
import pytest

from app.core.utils.common_utils import jprint  # NOQA: F401

pytestmark = pytest.mark.asyncio

txt_fields = ('description', 'title', 'subtitle', 'name', 'made_of', "recommendation")


def validate_query(stmt):
    try:
        compiled = stmt.compile(dialect=dialect(), compile_kwargs={"literal_binds": True})
        print("✅ SQL:", compiled)
        return True, "✅ Запрос корректен"
    except Exception as e:
        return False, f"❌ Ошибка: {e}"


def comprehensive_validation(filter_condition, model):
    """Комплексная проверка условия фильтрации"""

    # 1. Проверка типа
    if not isinstance(filter_condition, sql.ClauseElement):
        return False, "❌ Не является SQL выражением SQLAlchemy"

    # 2. Проверка ссылок на таблицы
    tables_referenced = set()

    def collect_tables(element):
        if hasattr(element, 'table'):
            tables_referenced.add(element.table)

    visitors.traverse(filter_condition, {}, {'column': collect_tables})

    model_table = model.__table__
    for table in tables_referenced:
        if table != model_table:
            return False, f"❌ Ссылка на чужую таблицу: {table}"

    # 3. Проверка синтаксиса через компиляцию
    try:
        test_stmt = sql.select(model).where(filter_condition).limit(1)
        _ = str(test_stmt.compile(compile_kwargs={"literal_binds": True}))
        print("✅ SQL компилируется без ошибок")
        return True, "✅ Условие корректно"
    except Exception as e:
        return False, f"❌ Ошибка компиляции: {e}"


def test_create_search_model():
    """
        test method create_search_model
        test method build_search_condition
        check sql request
    """
    from app.core.utils.alchemy_utils import create_search_model
    from app.support.drink.model import Drink as model
    from sqlalchemy import Column
    from sqlalchemy.orm import MapperProperty
    from sqlalchemy.orm.attributes import QueryableAttribute
    from app.core.utils.alchemy_utils import build_search_condition, create_search_conditions
    from sqlalchemy.dialects import postgresql
    # from app.support.drink.schemas import DrinkRead
    search_model = create_search_model(model)
    search_str: str = 'Some Words'
    conditions: list = []
    for key in search_model.model_fields.keys():
        # search_model возвращает поля из модели и ничего лишнего
        assert isinstance(getattr(model, key), (Column, MapperProperty, QueryableAttribute))
        assert getattr(model, key, None), f'{key} лишнее поле, ошибка метода create_search_model'
        # проверка метода build_search_condition
        field = getattr(model, key)
        condition = build_search_condition(field, search_str)
        conditions.append(condition)
    query = select(model).where(or_(*conditions))
    try:
        compiled_query = query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
        sql_text = str(compiled_query)
        print(sql_text)
    except Exception as e:
        assert False, f"Ошибка синтаксиса запроса на выборку: {e}"
    try:
        query = select(func.count()).select_from(model).where(or_(*conditions))
        compiled_query = query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
        sql_text = str(compiled_query)
        print(sql_text)
    except Exception as e:
        assert False, f"Ошибка синтаксиса запроса на подсчет записей: {e}"
    try:
        conditions = create_search_conditions(model, search_str)
        queries = {'select': select(model).where(or_(*conditions)),
                   'count': select(func.count()).select_from(model).where(or_(*conditions))}
        for key, val in queries.items():
            compiled_query = query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
            sql_text = str(compiled_query)
    except Exception:
        assert False, f'error in {key} query, {sql_text}'


@pytest.mark.skip
def test_get_text_model_fields():
    """
        тестирование метода get_text_model_fields
    """
    from app.support.drink.model import Drink
    from app.core.utils.common_utils import get_text_model_fields
    # from app.support.drink.repository import DrinkRepository
    model = Drink
    text_fields = get_text_model_fields(model)
    jprint(text_fields)
    search_query: str = 'search query'
    conditions = []
    for field in text_fields:
        conditions.append(getattr(model, field).ilike(f"%{search_query}%"))
    print(conditions)

    assert False


def test_create_search_conditions():
    """
        тестирование метода create_search_conditions
    """
    from app.core.utils.alchemy_utils import create_search_conditions
    from app.support.drink.model import Drink as Model
    result = create_search_conditions(Model, 'test Search')
    # assert isinstance(result, list)
    condition = result  # (or_(*result))
    res, message = comprehensive_validation(condition, Model)
    assert res, message


def test_create_search_conditions2():
    """
        тестирование метода create_search_conditions
    """
    from app.core.utils.alchemy_utils import create_search_conditions2
    from app.support.drink.model import Drink as Model
    result = create_search_conditions2(Model, 'test Search')
    condition = result
    res, message = comprehensive_validation(condition, Model)
    assert res, message
    # удачный запрос
    source = {'title': 'some wine'}
    result = create_search_conditions2(Model, source)
    condition = result
    res, message = comprehensive_validation(condition, Model)
    assert res, message
    # неудачный запрос
    source = {'name': 'some wine'}
    result = create_search_conditions2(Model, source)
    condition = result
    res, message = comprehensive_validation(condition, Model)
    assert not res, message


def test_create_enum_conditions():
    """
        тестирование метода create_search_conditions
    """
    from app.core.utils.alchemy_utils import create_enum_conditions
    from app.support.drink.model import Drink as Model

    result = create_enum_conditions(Model, 'test Search')
    condition = result
    res, message = comprehensive_validation(condition, Model)
    assert res, message


def test_typing():
    from app.core.utils.alchemy_utils import ModelType
    from app.support.item.model import Item
    from sqlalchemy import Select, select
    a = Item
    b = select(Item)
    c = select(func.count()).select_from(Item)
    print(f'{type(a)=}, {type(b)=}, {type(c)=}, {ModelType=}')
    print(f'{isinstance(b, Select)=}, {isinstance(c, Select)}, {isinstance(a, Select)}')
    assert True


def split_string(s: str, n: int = 3) -> List[str]:
    #  разбивает строку на список слов
    # return [s[i:i + n] for i in range(0, len(s), n)]
    return s.split(' ')


async def test_search(authenticated_client_with_db, test_db_session,
                      routers_get_all, fakedata_generator):
    from app.core.schemas.base import PaginatedResponse
    # from app.support.item.router import ItemRouter
    from random import randint
    client = authenticated_client_with_db
    routers = routers_get_all
    routers = ['/items']

    expected_response = PaginatedResponse.model_fields.keys()
    for prefix in routers:
        # получение записей из базы,
        response = await client.get(f'{prefix}')
        assert response.status_code == 200, f'метод GET не работает для пути "{prefix}"'
        assert response.json().keys() == expected_response, \
            f'метод GET для пути "{prefix}" возвращает некорректные данные'
        result = response.json()
        total = result.get('total')
        x = randint(1, total)
        response = await client.get(f'{prefix}/{x}')
        assert response.status_code == 200, f'{x}, {total=}'
        result = response.json()
        id = result.get('id')
        category = result.get('category')
        country = result.get('country')
        tmp = result['en'].get('description', result['en'].get('title'))
        search = tmp.split(' ')[-1]
        # http://localhost:8091/api/search?search=barol&country_enum=italy&category_enum=wine&page=1&page_size=20
        # http://localhost:8091/api/search_all?search=barol&country_enum=italy&category_enum=wine
        # поиск без paging
        response = await client.get(f'{prefix}/search_all?category={category}')
        assert response.status_code == 200, response.text
        result = response.json()
        jprint(result)
        ids = [item.get('id') for item in result]
        assert id in ids, f'{id=} not in {ids}'
        # поиск с paging
        response = await client.get(f'{prefix}/search?category={category}&page=1&page_size=20')
        assert response.status_code == 200, response.text
        # поиск без аргументов (должен вернуть все записи - сравниваем количество)
        response = await client.get(f'{prefix}/search_all')
        assert response.status_code == 200, response.text
        result = response.json()
        assert total == len(result)
        """
        доделать все виды поиска вставить
        """
