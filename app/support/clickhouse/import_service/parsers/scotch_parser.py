import pandas as pd
from typing import Dict, Any


def parse_scotch(row: pd.Series, filename: str) -> Dict[str, Any]:
    """Парсинг scotch_review.csv"""

    name = row.get('name', '')
    description = row.get('description', '')

    attributes = {}
    if pd.notna(row.get('category')):
        attributes['whisky_category'] = row['category']

    return {'name': str(name), 'description': str(description), 'category': 'whisky', 'country': 'Scotland',
            # По умолчанию для скотча
            'brand': name.split()[0] if name else '', 'abv': None,  # В этом файле нет ABV
            'price': float(row['price'].replace('$', '')) if pd.notna(row.get('price')) else None,
            'rating': float(row['review.point']) if pd.notna(row.get('review.point')) else None, 'rate_count': None,
            'attributes': attributes, 'source_file': filename}
