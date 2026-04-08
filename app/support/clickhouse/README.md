## структура RAG
beverage_rag/
├── parsers/
│   ├── __init__.py
│   ├── beer_parser.py
│   ├── scotch_parser.py
│   ├── spirits_parser.py
│   ├── wine_parser.py
│   ├── wine_data_parser.py
│   ├── winemag_130k_parser.py
│   └── winemag_first150k_parser.py
├── database/
│   ├── __init__.py
│   ├── models.py
│   ├── crud.py
│   └── clickhouse_client.py
├── api/
│   ├── __init__.py
│   ├── routes.py
│   └── schemas.py
├── rag/
│   ├── __init__.py
│   ├── embeddings.py
│   └── search.py
├── main.py
├── config.py
└── requirements.txt