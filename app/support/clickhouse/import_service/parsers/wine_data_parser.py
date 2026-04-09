import pandas as pd
from typing import Dict, Any


def parse_wine_data(row: pd.Series, filename: str) -> Dict[str, Any]:
    """Парсинг wine_data.csv"""

    name = row.get('Name', '')
    description = row.get('Description', '')

    attributes = {}

    # Специфичные для вина атрибуты
    if pd.notna(row.get('Categories')):
        attributes['categories'] = row['Categories']
    if pd.notna(row.get('Tasting Notes')):
        attributes['tasting_notes'] = row['Tasting Notes']
    if pd.notna(row.get('Food Pairing')):
        attributes['food_pairing'] = row['Food Pairing']
    if pd.notna(row.get('Suggested Glassware')):
        attributes['glassware'] = row['Suggested Glassware']
    if pd.notna(row.get('Suggested Serving Temperature')):
        attributes['serving_temp'] = row['Suggested Serving Temperature']
    if pd.notna(row.get('Sweet-Dry Scale')):
        attributes['sweet_dry_scale'] = row['Sweet-Dry Scale']
    if pd.notna(row.get('Body')):
        attributes['body'] = row['Body']

    return {'name': str(name), 'description': str(description), 'category': 'wine', 'country': row.get('Country', ''),
            'brand': row.get('Brand', ''), 'abv': None,  # В этом файле нет ABV
            'price': float(row['Price'].replace('$', '')) if pd.notna(row.get('Price')) else None,
            'rating': float(row['Rating']) if pd.notna(row.get('Rating')) else None,
            'rate_count': int(row['Rate Count']) if pd.notna(row.get('Rate Count')) else None, 'attributes': attributes,
            'source_file': filename}
