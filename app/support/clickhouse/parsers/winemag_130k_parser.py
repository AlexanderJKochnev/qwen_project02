import pandas as pd
from typing import Dict, Any


def parse_winemag_130k(row: pd.Series, filename: str) -> Dict[str, Any]:
    """Парсинг winemag-data-130k-v2.csv"""

    title = row.get('title', '')
    description = row.get('description', '')

    attributes = {'designation': row.get('designation', ''), 'variety': row.get('variety', ''),
                  'province': row.get('province', ''), 'region_1': row.get('region_1', ''),
                  'region_2': row.get('region_2', ''), 'taster_name': row.get('taster_name', ''),
                  'taster_twitter': row.get('taster_twitter_handle', '')}

    return {'name': str(title), 'description': str(description), 'category': 'wine', 'country': row.get('country', ''),
            'brand': row.get('winery', ''), 'abv': None,
            'price': float(row['price']) if pd.notna(row.get('price')) else None,
            'rating': float(row['points']) if pd.notna(row.get('points')) else None, 'rate_count': None,
            'attributes': attributes, 'source_file': filename}
