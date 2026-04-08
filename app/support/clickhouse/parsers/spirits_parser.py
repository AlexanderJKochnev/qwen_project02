import pandas as pd
from typing import Dict, Any


def parse_spirits(row: pd.Series, filename: str) -> Dict[str, Any]:
    """Парсинг spirits_data.csv"""

    name = row.get('Name', '')
    description = row.get('Description', '')

    attributes = {}

    if pd.notna(row.get('Categories')):
        attributes['categories'] = row['Categories']
    if pd.notna(row.get('Tasting Notes')):
        attributes['tasting_notes'] = row['Tasting Notes']
    if pd.notna(row.get('Base Ingredient')):
        attributes['base_ingredient'] = row['Base Ingredient']
    if pd.notna(row.get('Years Aged')):
        attributes['years_aged'] = int(row['Years Aged'])

    return {'name': str(name), 'description': str(description), 'category': 'spirits',
            'country': row.get('Country', ''), 'brand': row.get('Brand', ''),
            'abv': float(str(row['ABV']).replace('%', '')) if pd.notna(row.get('ABV')) else None,
            'price': float(row['Price'].replace('$', '')) if pd.notna(row.get('Price')) else None,
            'rating': float(row['Rating']) if pd.notna(row.get('Rating')) else None,
            'rate_count': int(row['Rate Count']) if pd.notna(row.get('Rate Count')) else None, 'attributes': attributes,
            'source_file': filename}
