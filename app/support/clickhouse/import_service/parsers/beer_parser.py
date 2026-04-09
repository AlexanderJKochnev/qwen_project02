import pandas as pd
from typing import Dict, Any


def parse_beer(row: pd.Series, filename: str) -> Dict[str, Any]:
    """Парсинг beer_data.csv"""

    # Базовые поля
    name = row.get('Name', '')
    description = row.get('Description', '')

    # Если описание пустое, используем Tasting Notes + Categories
    if pd.isna(description) or description == '':
        tasting = row.get('Tasting Notes', '')
        categories = row.get('Categories', '')
        description = f"{categories}. {tasting}".strip()

    # Собираем все дополнительные атрибуты
    attributes = {}

    # Числовые характеристики
    if pd.notna(row.get('ABV')):
        attributes['abv'] = float(str(row['ABV']).replace('%', ''))
    if pd.notna(row.get('IBU')):
        attributes['ibu'] = int(row['IBU'])
    if pd.notna(row.get('Calories Per Serving (12 OZ/0.35L)')):
        attributes['calories'] = int(row['Calories Per Serving (12 OZ/0.35L)'])
    if pd.notna(row.get('Carbs Per Serving (12 OZ/0.35L)')):
        attributes['carbs'] = float(row['Carbs Per Serving (12 OZ/0.35L)'])

    # Текстовые характеристики
    if pd.notna(row.get('Categories')):
        attributes['categories'] = row['Categories']
    if pd.notna(row.get('Type')):
        attributes['type'] = row['Type']
    if pd.notna(row.get('Tasting Notes')):
        attributes['tasting_notes'] = row['Tasting Notes']
    if pd.notna(row.get('Food Pairing')):
        attributes['food_pairing'] = row['Food Pairing']
    if pd.notna(row.get('Suggested Serving Temperature')):
        attributes['serving_temp'] = row['Suggested Serving Temperature']

    return {'name': str(name), 'description': str(description), 'category': 'beer', 'country': row.get('Country', ''),
            'brand': row.get('Brand', ''), 'abv': attributes.get('abv'),
            'price': float(row['Price'].replace('$', '')) if pd.notna(row.get('Price')) else None,
            'rating': float(row['Rating']) if pd.notna(row.get('Rating')) else None,
            'rate_count': int(row['Rate Count']) if pd.notna(row.get('Rate Count')) else None, 'attributes': attributes,
            'source_file': filename}
