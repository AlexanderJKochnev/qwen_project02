# parsers/__init__.py
import pandas as pd
from .beer_parser import parse_beer
from .scotch_parser import parse_scotch
from .spirits_parser import parse_spirits
from .wine_parser import parse_wine
from .wine_data_parser import parse_wine_data
from .winemag_130k_parser import parse_winemag_130k
from .winemag_first150k_parser import parse_winemag_first150k

PARSERS = {'beer_data.csv': parse_beer, 'scotch_review.csv': parse_scotch, 'spirits_data.csv': parse_spirits,
           'wine.csv': parse_wine, 'wine_data.csv': parse_wine_data, 'winemag-data-130k-v2.csv': parse_winemag_130k,
           'winemag-data_first150k.csv': parse_winemag_first150k, }


def import_all_csv_files(client, embedding_model):
    """Импорт всех CSV файлов"""

    for filename, parser in PARSERS.items():
        print(f"Importing {filename}...")

        df = pd.read_csv(filename)

        for _, row in df.iterrows():
            try:
                # Парсим строку
                data = parser(row, filename)

                # Генерируем эмбеддинг
                text_for_embedding = f"{data['name']}. {data['description']}"
                embedding = embedding_model.encode(text_for_embedding).tolist()

                # Вставляем в ClickHouse
                client.insert(
                    'beverages_rag', [
                        [data['name'], data['description'], data['category'], data['country'], data['brand'],
                         data['abv'], data['price'], None,  # volume_ml
                         data['rating'], data['rate_count'], data['attributes'], embedding,
                         data['source_file']]],
                    column_names=['name', 'description', 'category', 'country', 'brand', 'abv', 'price',
                                  'volume_ml', 'rating', 'rate_count', 'attributes', 'embedding', 'source_file']
                )
            except Exception as e:
                print(f"Error parsing row: {e}")

        print(f"Finished {filename}")
