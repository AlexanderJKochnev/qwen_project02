# app.support.clickhouse.service.py
from app.core.config.project_config import settings
from loguru import logger


class FullTextSearch:
    limit = settings.CH_LIMIT

    @classmethod
    async def search(cls, query: str, table: str, ch_client, mode: str = 'auto'):
        """
        Универсальный метод поиска
        mode: 'auto', 'word', 'and', 'or', 'phrase', 'fuzzy'
        """
        query_lower = query.lower()
        match mode:
            case 'auto':
                if '"' in query:
                    result = await cls._search_phrase(query, table, ch_client)
                elif len(query_lower.split()) > 1:
                    result = await cls._search_ranked(query_lower, table, ch_client)
                else:
                    result = await cls._search_word(query_lower, table, ch_client)
            case 'word':
                result = await cls._search_word(query_lower, table, ch_client)
            case 'and':
                result = await cls._search_and(query_lower, table, ch_client)
            case 'or':
                result = await cls._search_or(query_lower, table, ch_client)
            case 'phrase':
                result = await cls._search_phrase(query, table, ch_client)
            case 'fuzzy':
                result = await cls._search_fuzzy(query_lower, table, ch_client)
            case 'ranked':
                result = await cls._search_ranked(query_lower, table, ch_client)
            case 'like':
                result = await cls._search_like(query_lower, table, ch_client)
        logger.warning(result)
        return tuple(row[0] for row in result.result_rows)

    @classmethod
    async def _search_like(cls, query: str, table: str, ch_client):
        logger.warning(f'{query=} {type(query)=}')
        sql = "SELECT id FROM items_search FINAL WHERE search_content LIKE {query:String} LIMIT 50"
        return await ch_client.query(sql, parameters={'query': f'%{query.lower()}%'})

    @classmethod
    async def _search_word(cls, query: str, table: str, ch_client):
        sql = f"""
            SELECT id, search_content
            FROM {table} FINAL
            WHERE hasToken(search_content, {{token:String}})
            LIMIT {cls.limit}
        """
        return await ch_client.query(sql, parameters={'token': query})

    @classmethod
    async def _search_and(cls, query: str, table: str, ch_client):
        words = query.split()
        sql = f"""
            SELECT id, search_content
            FROM {table} FINAL
            WHERE hasAllTokens(search_content, {{words:Array(String)}})
            LIMIT {cls.limit}
        """
        return await ch_client.query(sql, parameters={'words': words})

    @classmethod
    async def _search_or(cls, query: str, table: str, ch_client):
        words = query.split()
        sql = f"""
            SELECT id, search_content
            FROM {table} FINAL
            WHERE hasAnyTokens(search_content, {{words:Array(String)}})
            LIMIT {cls.limit}
        """
        return await ch_client.query(sql, parameters={'words': words})

    @classmethod
    async def _search_ranked(cls, query: str, table: str, ch_client):
        logger.warning(f'{query=}')
        logger.warning(f'{table=}')
        logger.warning(f'{ch_client=}')
        words = query.split()
        sql = f"""
            SELECT
                id,
                search_content,
                length(arrayIntersect(
                    splitByNonAlpha(lower(search_content)),
                    {{words:Array(String)}}
                )) AS score
            FROM {table} FINAL
            WHERE hasAnyTokens(search_content, {{words:Array(String)}})
            ORDER BY score DESC, id
            LIMIT {cls.limit}
        """
        return await ch_client.query(sql, parameters={'words': words})

    @classmethod
    async def _search_phrase(cls, phrase: str, table: str, ch_client):
        sql = f"""
            SELECT id, search_content
            FROM {table} FINAL
            WHERE positionCaseInsensitive(search_content, {{phrase:String}}) > 0
            LIMIT {cls.limit}
        """
        return await ch_client.query(sql, parameters={'phrase': phrase})

    @classmethod
    async def _search_fuzzy(cls, query: str, table: str, ch_client, distance: int = 1):
        words = query.split()
        sql = f"""
            SELECT
                id,
                search_content,
                multiFuzzyMatchAnyIndex(search_content, {{distance:UInt8}}, {{words:Array(String)}}) AS score
            FROM {table} FINAL
            WHERE multiFuzzyMatchAny(search_content, {{distance:UInt8}}, {{words:Array(String)}})
            ORDER BY score DESC, id
            LIMIT {cls.limit}
        """
        return await ch_client.query(sql, parameters={
            'words': words,
            'distance': distance,
            'limit': cls.limit
        })


"""
# Использование
fts = FullTextSearch(client)

# Разные режимы поиска
results = fts.search("clickhouse", mode='word')           # одно слово
results = fts.search("database performance", mode='and')  # все слова
results = fts.search("error timeout", mode='ranked')      # с ранжированием
results = fts.search('"exact phrase"', mode='phrase')     # точная фраза
results = fts.search("ClickHose", mode='fuzzy')           # с опечатками
results = fts.search("database", mode='auto')             # автоматический выбор
"""
