# debug_services.py
from app.core.hash_norm import tokenize
from app.core.utils.reindexation import extract_text_optimized, extract_text_ultra_fast

phrase = 'Gin Hendrick’s'
drink_dict = {
    "alc": 41.4,
    "subcategory_id": 17,
    "id": 122,
    "created_at": "2025-11-26T10:44:32.149298+00:00",
    "updated_at": "2026-05-05T21:48:25.364458+00:00",
    "title": "Gin Hendrick’s",
    "title_ru": "Gin Hendrick’s",
    "subtitle": "William Grant & Sons ",
    "subtitle_ru": "William Grant & Sons ",
    "description": "Each still is infused with an unusual symphony of 11 botanicals: chamomile, elderflower, juniper, lemon peel, orange peel, caraway, coriander, cubeb berries, angelica root, yarrow root and orris root. \nThe curious, yet marvellous, infusions of rose & cucumber imbue   with uniquely balanced flavour resulting in an impeccably smooth distinct gin.",
    "description_ru": "В состав каждого перегонного куба Hendricks входит необычная симфония из 11 растительных "
                      "компонентов: ромашки, цветов бузины, можжевельника, лимонной и апельсиновой цедры, тмина, кориандра, ягод кубеба, корня дягиля, тысячелистника и ириса. \nНеобычные, но в то же время изумительные сочетания розы и огурца придают джину уникальный сбалансированный вкус, в результате чего получается безупречно гладкий и самобытный джин.",
    "recommendation": "In its pure form or as part of classic and original cocktails.",
    "recommendation_ru": "в чистом виде или в составе классических и авторских коктейлей.",
    "madeof": "Purified grain alcohol and 11 botanicals",
    "madeof_ru": "очищенного зернового спирта и 11 растительных компонентов.",
    "source_id": 1,
    "site_id": 57,
    "subcategory": {
        "category_id": 5,
        "id": 17,
        "name": "Gin",
        "created_at": "2025-11-26T10:44:09.175557+00:00",
        "updated_at": "2025-11-26T10:44:09.175557+00:00",
        "name_ru": "Джин",
        "category": {
            "id": 5,
            "name": "Other",
            "created_at": "2025-11-26T10:43:45.174257+00:00",
            "updated_at": "2025-12-21T14:48:48.693909+00:00",
            "name_ru": "Прочее"
        }
    },
    "source": {
        "id": 1,
        "name": "manual",
        "created_at": "2026-03-13T23:29:13.134720+00:00",
        "updated_at": "2026-03-13T23:29:13.134720+00:00",
        "description_ru": "ручной ввод"
    },
    "site": {
        "subregion_id": 55,
        "id": 57,
        "created_at": "2026-03-15T15:17:26.519496+00:00",
        "updated_at": "2026-03-15T15:17:26.519496+00:00",
        "subregion": {
            "region_id": 51,
            "id": 55,
            "created_at": "2025-11-26T10:44:32.127460+00:00",
            "updated_at": "2025-11-26T10:44:32.127460+00:00",
            "region": {
                "country_id": 4,
                "id": 51,
                "created_at": "2025-11-26T10:44:32.050208+00:00",
                "updated_at": "2025-11-26T10:44:32.050208+00:00",
                "country": {
                    "id": 4,
                    "name": "Scotland",
                    "created_at": "2025-11-26T10:43:44.051596+00:00",
                    "updated_at": "2025-12-21T14:48:48.693909+00:00",
                    "name_ru": "Шотландия"
                }
            }
        }
    }
}

if __name__ == "__main__":
    print(tokenize(phrase))
    result1 = list(set(tokenize(extract_text_optimized(drink_dict))))
    print(len(result1), 'hendricks' in result1, result1)
    result2 = list(set(tokenize(extract_text_ultra_fast(drink_dict))))
    print(len(result2), 'handricks' in result2, result2)
