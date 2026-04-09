import pandas as pd
from typing import Dict, Any


def parse_wine(row: pd.Series, filename: str) -> Dict[str, Any]:
    """Парсинг wine.csv"""

    # Формируем имя из winery + designation + varietal
    winery = row.get('winery', '')
    designation = row.get('designation', '')
    varietal = row.get('varietal', '')
    name = f"{winery} {designation} {varietal}".strip()

    description = row.get('review', '')

    attributes = {'appellation': row.get('appellation', ''), 'varietal': varietal, 'winery': winery,
                  'reviewer': row.get('reviewer', '')}

    return {'name': str(name), 'description': str(description), 'category': 'wine',
            'country': row.get('country', 'US') if pd.notna(row.get('country')) else 'US', 'brand': winery,
            'abv': float(row['alcohol'].replace('%', '')) if pd.notna(row.get('alcohol')) else None,
            'price': float(row['price']) if pd.notna(row.get('price')) else None,
            'rating': float(row['rating']) if pd.notna(row.get('rating')) else None, 'rate_count': None,
            'attributes': attributes, 'source_file': filename}
