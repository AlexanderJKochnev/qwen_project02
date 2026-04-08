# app.core.service.click_service.py
from typing import List
from app.core.services.service import ServiceMeta
from app.core.config.project_config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks
from loguru import logger

from app.support.clickhouse.parsers import PARSERS


class FullTextSearch:
    limit = settings.CH_LIMIT

    @classmethod
    async def search(cls, query: str, table: str, ch_client, mode: str = 'auto'):
        """
        Универсальный метод поиска
        mode: 'auto', 'word', 'and', 'or', 'phrase', 'fuzzy'
        """
        query_lower = query.lower()
        await ch_client.command("SET send_logs_level = 'debug'")
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
            case 'fuzzy2':
                result = await cls._search_fuzzy2(query_lower, table, ch_client)
            case 'ranked':
                result = await cls._search_ranked(query_lower, table, ch_client)
            case 'like':
                result = await cls._search_like(query_lower, table, ch_client)
        return tuple(row[0] for row in result.result_rows)

    @classmethod
    async def _search_like(cls, query: str, table: str, ch_client):
        sql = "SELECT id FROM items_search FINAL WHERE search_content LIKE {query:String} LIMIT 50"
        return await ch_client.query(sql, parameters={'query': f'%{query.lower()}%'})

    @classmethod
    async def _search_word(cls, query: str, table: str, ch_client):
        sql = f"""
            SELECT id, search_content
            FROM {table} FINAL
            WHERE hasToken(search_content, {{token:String}})
        """
        return await ch_client.query(sql, parameters={'token': query})

    @classmethod
    async def _search_and(cls, query: str, table: str, ch_client):
        words = query.split()
        sql = f"""
            SELECT id, search_content
            FROM {table} FINAL
            WHERE hasAllTokens(search_content, {{words:Array(String)}})
        """
        return await ch_client.query(sql, parameters={'words': words})

    @classmethod
    async def _search_or(cls, query: str, table: str, ch_client):
        words = query.split()
        sql = f"""
            SELECT id, search_content
            FROM {table} FINAL
            WHERE hasAnyTokens(search_content, {{words:Array(String)}})
        """
        return await ch_client.query(sql, parameters={'words': words})

    @classmethod
    async def _search_ranked(cls, query: str, table: str, ch_client):
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
        """
        return await ch_client.query(sql, parameters={'words': words})

    @classmethod
    async def _search_phrase(cls, phrase: str, table: str, ch_client):
        sql = f"""
            SELECT id, search_content
            FROM {table} FINAL
            WHERE positionCaseInsensitive(search_content, {{phrase:String}}) > 0
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
        """
        return await ch_client.query(sql, parameters={
            'words': words,
            'distance': distance,
            'limit': cls.limit
        })

    @classmethod
    async def _search_fuzzy2(cls, query: str, table: str, ch_client, distance: int = 1):
        words = query.split()
        sql = f"""
            WITH filtered AS (
                SELECT id, search_content
                FROM {table}
                WHERE hasAnyTokens(search_content, {{words:Array(String)}})
            )
            SELECT
                id,
                search_content,
                multiFuzzyMatchAnyIndex(search_content, {{distance:UInt8}}, {{words:Array(String)}}) AS score
            FROM {table} FINAL
            WHERE multiFuzzyMatchAny(search_content, {{distance:UInt8}}, {{words:Array(String)}})
            ORDER BY score DESC, id
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


class ClickService(ServiceMeta):
    pass

    @classmethod
    async def import_csv(cls, background_tasks: BackgroundTasks, ch_client):
        csv_files = [('data/beer_data.csv', PARSERS['beer_data.csv']),
                     ('data/scotch_review.csv', PARSERS['scotch_review.csv']),
                     ('data/spirits_data.csv', PARSERS['spirits_data.csv']), ('data/wine.csv', PARSERS['wine.csv']),
                     ('data/wine_data.csv', PARSERS['wine_data.csv']),
                     ('data/winemag-data-130k-v2.csv', PARSERS['winemag-data-130k-v2.csv']),
                     ('data/winemag-data_first150k.csv', PARSERS['winemag-data_first150k.csv']), ]
        background_tasks.add_task(cls.import_all_files, csv_files)
        return {"message": "Import started in background", "files": [f[0] for f in csv_files],
                "note": "GPU model will be loaded temporarily"}
    
    @classmethod
    async def import_all_files(cls, files: List[tuple]):
        """Фоновая задача импорта всех файлов"""
        try:
            for file_path, parser in files:
                file_name = file_path.split('/')[-1]
                await importer.import_file(file_path, parser, file_name)
            
            logger.info("All files imported successfully")
        finally:
            # Важно: выгружаем GPU модель после импорта
            hybrid_embeddings.unload_import_model()):