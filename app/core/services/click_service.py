# app.support.clickhouse.service.py
from app.core.config.project_config import settings
from loguru import logger

class FullTextSearch:
    limit = settings.CH_LIMIT

    @classmethod
    def search(cls, query: str, table: str, ch_client, mode: str = 'auto'):
        """
        Универсальный метод поиска
        mode: 'auto', 'word', 'and', 'or', 'phrase', 'fuzzy'
        """
        logger.warning(f'{ch_client=}, {table=}, {mode=}')
        query_lower = query.lower()
        match mode:
            case 'auto':
                if '"' in query:
                    result = cls._search_phrase(query,  table, ch_client)
                elif len(query_lower.split()) > 1:
                    result = cls._search_ranked(query_lower, table, ch_client)
                else:
                    result = cls._search_word(query_lower, table, ch_client)
            case 'word':
                result = cls._search_word(query_lower, table, ch_client)
            case 'and':
                result = cls._search_and(query_lower, table, ch_client)
            case 'or':
                result = cls._search_or(query_lower, table, ch_client)
            case 'phrase':
                result = cls._search_phrase(query, table, ch_client)
            case 'fuzzy':
                result = cls._search_fuzzy(query_lower, table, ch_client)
            case 'ranked':
                result = cls._search_ranked(query_lower, table, ch_client)
        return tuple(row[0] for row in result.result_rows)

    def _search_word(cls, query: str, table: str, ch_client):
        sql = f"""
            SELECT id, search_content
            FROM {table} FINAL
            WHERE hasToken(search_content, {{token:String}})
            LIMIT {{cls.limit:UInt32}}
        """
        return ch_client.query(sql, parameters={'token': query})

    def _search_and(cls, query: str, table: str, ch_client):
        words = query.split()
        sql = f"""
            SELECT id, search_content
            FROM {table} FINAL
            WHERE hasAllTokens(search_content, {{words:Array(String)}})
            LIMIT {{cls.limit:UInt32}}
        """
        return ch_client.query(sql, parameters={'words': words})

    def _search_or(cls, query: str, table: str, ch_client):
        words = query.split()
        sql = f"""
            SELECT id, search_content
            FROM {table} FINAL
            WHERE hasAnyTokens(search_content, {{words:Array(String)}})
            LIMIT {{cls.limit:UInt32}}
        """
        return ch_client.query(sql, parameters={'words': words})

    def _search_ranked(cls, query: str, table: str, ch_client):
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
            LIMIT {{cls.limit:UInt32}}
        """
        return ch_client.query(sql, parameters={'words': words})

    def _search_phrase(cls, phrase: str, table: str, ch_client):
        sql = f"""
            SELECT id, search_content
            FROM {table} FINAL
            WHERE positionCaseInsensitive(search_content, {{phrase:String}}) > 0
            LIMIT {{cls.limit:UInt32}}
        """
        return ch_client.query(sql, parameters={'phrase': phrase})

    def _search_fuzzy(cls, query: str, table: str, ch_client, distance: int = 1):
        words = query.split()
        sql = f"""
            SELECT
                id,
                search_content,
                multiFuzzyMatchAnyIndex(search_content, {{distance:UInt8}}, {{words:Array(String)}}) AS score
            FROM {table} FINAL
            WHERE multiFuzzyMatchAny(search_content, {{distance:UInt8}}, {{words:Array(String)}})
            ORDER BY score DESC, id
            LIMIT {{cls.limit:UInt32}}
        """
        return ch_client.query(sql, parameters={
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
