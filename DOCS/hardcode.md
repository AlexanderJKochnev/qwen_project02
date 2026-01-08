# Hardcoded Language Variables Analysis

This document contains all the hardcoded language variables with '_ru' and '_fr' suffixes found in the codebase.

## File: /workspace/app/core/models/base_model.py
- Line 131: # description_ru: Mapped[descr]
- Line 133: # name_ru: Mapped[str_null_index]
- Line 156: description_ru: Mapped[descr]
- Line 157: description_fr: Mapped[descr]
- Line 165: name_ru: Mapped[str_null_true]
- Line 166: name_fr: Mapped[str_null_true]
- Line 181: return self.name or self.name_fr or self.name_ru or ""

## File: /workspace/app/core/schemas/api_mixin.py
- Line 21: def __get_lang__(self, lang: str = '_ru', ) -> str:
- Line 30: def name_ru(self) -> str:
- Line 31: return self.__get_lang__('_ru')
- Line 35: def name_fr(self) -> str:
- Line 36: return self.__get_lang__('_fr')

## File: /workspace/app/core/schemas/base.py
- Line 77: description_ru: Optional[str] = None
- Line 78: description_fr: Optional[str] = None
- Line 84: description_ru: Optional[str] = Field(exclude=True)
- Line 85: description_fr: Optional[str] = Field(exclude=True)
- Line 91: name_ru: Optional[str] = None
- Line 92: name_fr: Optional[str] = None
- Line 98: name_ru: Optional[str] = Field(exclude=True)
- Line 99: name_fr: Optional[str] = Field(exclude=True)

## File: /workspace/app/core/schemas/lang_schemas.py
- Line 16: """Возвращает первое непустое значение из name, name_ru, name_fr"""
- Line 17: return self.name or self.name_ru or self.name_fr or ""
- Line 26: """Возвращает первое непустое значение из name, name_ru, name_fr"""
- Line 27: return self.name or self.name_ru or self.name_fr or ""
- Line 34: return self.description or self.description_ru or self.description_fr or ""
- Line 43: """Возвращает первое непустое значение из name, name_ru, name_fr"""
- Line 44: return self.name_ru or self.name or self.name_fr or ""
- Line 53: """Возвращает первое непустое значение из name, name_ru, name_fr"""
- Line 54: return self.name_ru or self.name or self.name_fr or ""
- Line 61: return self.description_ru or self.description or self.description_fr or ""
- Line 70: """Возвращает первое непустое значение из name, name_ru, name_fr"""
- Line 71: return self.name_fr or self.name or self.name_ru or ""
- Line 80: """Возвращает первое непустое значение из name, name_ru, name_fr"""
- Line 81: return self.name_ru or self.name or self.name_fr or ""
- Line 88: return self.description_fr or self.description or self.description_ru or ""

## File: /workspace/app/core/schemas/preact_mixin.py
- Line 17: return self.__get_lang__('_ru')

## File: /workspace/app/core/utils/alchemy_utils.py
- Line 70: ru -> '_ru'
- Line 333: 'russian': '_ru',
- Line 334: 'francaise': '_fr'}
- Line 357: pairing_ru = data.get("pairing_ru", [])
- Line 360: for en, ru in zip(pairing_en, pairing_ru):
- Line 362: {"name": en, "name_ru": ru}
- Line 618: if k2 in ['type', 'type_ru']:
- Line 622: if k2 in ['madeOf', 'madeOf_ru']:
- Line 628: if k2 in ['region', 'region_ru']:
- Line 638: for subkey in ['subregion', 'subregion_ru', 'subcategory']:
- Line 641: #    x = self.data[key].pop(f'{k1}_ru', None)
- Line 651: case 'pairing' | 'pairing_ru':
- Line 657: case 'varietal_ru':
- Line 658: result = self.parse_varietal_string_clean(val, 'name_ru')
- Line 659: case 'subcategory' | 'subcategory_ru':
- Line 661: case 'title' | 'title_ru' | 'subtitle' | 'subtitle_ru':
- Line 663: case 'description' | 'description_ru':
- Line 681: pairing_ru = []
- Line 684: varietals_ru = []
- Line 689: subregion['name_ru'] = self.camelcase(
- Line 690: self.data[key].pop('subregion_ru', None))
- Line 693: region['name_ru'] = self.camelcase(
- Line 694: self.data[key].pop('region_ru', None))
- Line 697: country['name_ru'] = self.camelcase(
- Line 698: self.data[key].pop('country_ru', None))
- Line 705: subcategory['name_ru'] = self.camelcase(
- Line 706: self.data[key].pop('subcategory_ru', None))
- Line 709: category['name_ru'] = self.camelcase(
- Line 710: self.data[key].pop('category_ru', None))
- Line 715: pairing_ru = self.data[key].pop("pairing_ru", [])
- Line 717: for en, ru in zip(pairing_en, pairing_ru):
- Line 718: foods.append({"name": en, "name_ru": ru})
- Line 724: varietals_ru = data[key].pop("varietal_ru", [])
- Line 727: if len(varietals_en) != len(varietals_ru):
- Line 728: raise ValueError("Списки 'varietal' и 'varietal_ru' "
- Line 731: for item_en, item_ru in zip(varietals_en, varietals_ru):
- Line 733: # if item_en["percentage"] != item_ru["percentage"]:
- Line 735: #                      f"{item_en} vs {item_ru}")
- Line 738: "name_ru": self.camelcase(item_ru["name_ru"])},
- Line 763: data[key]['drink'].pop('varietal_ru', None)

## File: /workspace/app/core/utils/common_utils.py
- Line 330: :param priority_fields: приоритетные поля для извлечения значения (например, ['name', 'name_ru'])

## File: /workspace/app/core/utils/converters.py
- Line 154: "name_ru": {"Каберне Совиньон": 91, "Мерло": 6, "Пти Вердо": 2, "Мальбек": 1}
- Line 156: varietals = [{"varietal": {"name": "Pinot Noir", "name_ru": "Пино Нуар"},
- Line 183: if lang == '_ru':
- Line 193: item: dict = {"superfood": {"name": "Unclassified", "name_ru": "Не классифицированный"}}
- Line 637: в ['', '_ru', '_fr', ...]

## File: /workspace/app/core/utils/translation_utils.py
- Line 95: if field_name.endswith(('_ru', '_fr')):
- Line 96: return field_name[:-3]  # Remove _ru or _fr
- Line 120: # Group fields by their base name {'name': ['name', 'name_ru', 'name_fr', ...], ...}
- Line 126: # {'name': 'text', 'name_ru': 'текст', ...}

## File: /workspace/app/preact/handbook/router.py
- Line 29: # lang = self.get_lang_prefix(lang)  # convert lang to lang pref 'en' -> '', 'ru' -> '_ru' ...

## File: /workspace/app/support/drink/drink_food_schema.py
- Line 22: def __get_lang__(self, lang: str = '_ru', ) -> str:

## File: /workspace/app/support/drink/drink_varietal_schema.py
- Line 43: def __get_lang__(self, lang: str = '_ru', ) -> str:

## File: /workspace/app/support/drink/model.py
- Line 25: title_ru: Mapped[str_null_true]
- Line 26: title_fr: Mapped[str_null_true]
- Line 29: subtitle_ru: Mapped[str_null_true]
- Line 30: subtitle_fr: Mapped[str_null_true]
- Line 33: description_ru: Mapped[descr]
- Line 34: description_fr: Mapped[descr]
- Line 37: recommendation_ru: Mapped[descr]
- Line 38: recommendation_fr: Mapped[descr]
- Line 41: madeof_ru: Mapped[descr]
- Line 42: madeof_fr: Mapped[descr]
- Line 119: coalesce(title_ru, '') || ' ' ||
- Line 122: coalesce(subtitle_ru, '') || ' ' ||
- Line 125: coalesce(description_ru, '') || ' ' ||
- Line 128: coalesce(recommendation_ru, '') || ' ' ||
- Line 131: coalesce(madeof_ru, '') || ' ' ||

## File: /workspace/app/support/drink/repository.py
- Line 201: return (func.coalesce(cls.title, '') + ' ' + func.coalesce(cls.title_ru, '') + ' ' + func.coalesce(
- Line 203: ) + ' ' + func.coalesce(cls.subtitle, '') + ' ' + func.coalesce(cls.subtitle_ru, '') + ' ' + func.coalesce(
- Line 206: cls.description_ru, ''
- Line 210: cls.recommendation_ru, ''
- Line 213: ) + ' ' + func.coalesce(cls.madeof, '') + ' ' + func.coalesce(cls.madeof_ru, '') + ' ' + func.coalesce(

## File: /workspace/app/support/drink/schemas.py
- Line 20: title_ru: Optional[str] = None
- Line 24: subtitle_ru: Optional[str] = None
- Line 28: description_ru: Optional[str] = None
- Line 32: recommendation_ru: Optional[str] = None
- Line 36: madeof_ru: Optional[str] = None
- Line 45: title_ru: Optional[str] = Field(exclude=True)
- Line 49: subtitle_ru: Optional[str] = Field(exclude=True)
- Line 53: description_ru: Optional[str] = Field(exclude=True)
- Line 57: recommendation_ru: Optional[str] = Field(exclude=True)
- Line 61: madeof_ru: Optional[str] = Field(exclude=True)
- Line 292: lang_map = {"": "en", "_ru": "ru", "_fr": "fr"}
- Line 369: return self.__parser__("_ru")
- Line 396: Автоматически определяет базовые языковые поля по наличию полей с суффиксом '_ru'.
- Line 397: Например: если есть 'title_ru' → базовое поле 'title'.
- Line 402: if name.endswith('_ru'):
- Line 403: base_name = name[:-3]  # убираем '_ru'
- Line 476: return self._lang_('_ru')

## File: /workspace/app/support/drink/service.py
- Line 52: flatresult = flatten_dict(subresult, ['name', 'name_ru'])

## File: /workspace/app/support/item/repository.py
- Line 377: cls.title_ru, EMPTY_STRING
- Line 381: cls.subtitle_ru, EMPTY_STRING
- Line 385: cls.description_ru, EMPTY_STRING
- Line 389: cls.recommendation_ru, EMPTY_STRING
- Line 393: cls.madeof_ru, EMPTY_STRING

## File: /workspace/app/support/item/schemas.py
- Line 208: title_ru: Optional[str]
- Line 218: title: str  # Item.drinks.title or Item.drinks.title_ru or Item.drinks.title_fr зависит от параметра lang в роуте
- Line 220: country: str  # Country.name or country.name_ru, or country.name_fr зависит от параметра lang в роуте
- Line 243: title: str  # Item.drink.title or Item.drinks.title_ru or Item.drinks.title_fr
- Line 245: recommendation: Optional[str] = None   # Drink.recommendation (_ru, _fr)
- Line 246: madeof: Optional[str] = None  # Drink.madeof (_ru, _fr)
- Line 247: description: Optional[str] = None  # Drink.description (_ru, _fr)
- Line 277: title_ru: Optional[str] = None
- Line 281: subtitle_ru: Optional[str] = None
- Line 285: description_ru: Optional[str] = None
- Line 289: recommendation_ru: Optional[str] = None
- Line 293: madeof_ru: Optional[str] = None

## File: /workspace/app/support/region/schemas.py
- Line 15: def __get_lang__(self, lang: str = '_ru', ) -> str:
- Line 24: def country_ru(self) -> str:
- Line 25: return self.__get_lang__('_ru')

## File: /workspace/app/support/subcategory/schemas.py
- Line 19: def __get_lang__(self, lang: str = '_ru', ) -> str:
- Line 28: def category_ru(self) -> str:
- Line 29: return self.__get_lang__('_ru')

## File: /workspace/process_localized_fields.py
- Line 24: # Find lines with localized field patterns (like name_ru, description_fr, etc.)
- Line 25: # This regex looks for field names that end with _ru or _fr
- Line 26: matches_ru = re.findall(r'\b\w+_ru\b', line)
- Line 30: for match in matches_ru:
- Line 62: processed_content = re.sub(r'_ru\b', '_<xx>', content)
- Line 142: if '_ru' in content or '_fr' in content:

## File: /workspace/tests/data_factory/comparator.py
- Line 107: "description_ru": "string",
- Line 109: "name_ru": "string",
- Line 114: "description_ru": "string",
- Line 116: "name_ru": "string",
- Line 122: "description_ru": "string",
- Line 124: "name_ru": "string",
- Line 132: "description_ru": "string",
- Line 134: "name_ru": "string",
- Line 139: "description_ru": "string",
- Line 141: "name_ru": "string",
- Line 146: "description_ru": "string",
- Line 148: "name_ru": "string",
- Line 156: "recommendation_ru": "string",
- Line 159: "madeof_ru": "string",
- Line 169: "description_ru": "string",
- Line 171: "name_ru": "string",
- Line 180: "description_ru": "string",
- Line 182: "name_ru": "string",
- Line 190: "description_ru": "string",
- Line 210: "description_ru": "Насыщенное, полнотелое вино, глубокого рубинового оттенка предлагает элегантные, сложные ароматы красных фруктов. Вино имеет богатый и плотный, но гармоничный вкус, со сладкими, сбалансированными танинами. \nОбладает послевкусием с глубиной и структурой, обеспечивающей его необычайную продолжительность.",
- Line 211: "subtitle_ru": "Tenuta San Guido",
- Line 212: "title_ru": "Bolgheri Sassicaia 2014 DOC",
- Line 213: "varietal_ru": [
- Line 215: "name_ru": "каберне совиньон",
- Line 219: "name_ru": "каберне фран",
- Line 226: "name_ru": None,
- Line 229: "name_ru": "Мадейра",
- Line 232: "name_ru": None
- Line 238: "name_ru": None,
- Line 241: "name_ru": None,
- Line 247: "name_ru": "С дичью"
- Line 251: "name_ru": "Бараниной"
- Line 258: "name_ru": "каберне совиньон"
- Line 265: "name_ru": "каберне фран"

## File: /workspace/tests/data_factory/fake_generator.py
- Line 17: self.fake_ru = Faker('ru_RU')
- Line 23: 'ru': self.fake_ru,
- Line 91: if key.endswith('_ru'):
- Line 118: if key.endswith('_ru'):
- Line 132: 'name_ru': country_data['country']['ru'],
- Line 135: 'description_ru': f"{country_data['country']['ru']} — страна в Европе, известная своими винами.",
- Line 140: 'name_ru': region_data['name']['ru'],
- Line 143: 'description_ru': f"{region_data['name']['ru']} — винный регион в {country_data['country']['ru']}.",
- Line 148: 'name_ru': subregion_name['ru'],
- Line 151: 'description_ru': f"{subregion_name['ru']} — субрегион {region_data['name']['ru']}.",
- Line 186: 'name_ru': self._generate_color('name_ru'),
- Line 189: 'description_ru': self._generate_string('description_ru'),
- Line 198: 'name_ru': geo_data['region']['name_ru'],
- Line 201: 'description_ru': geo_data['region']['description_ru'],
- Line 205: 'name_ru': geo_data['subregion']['name_ru'],
- Line 208: 'description_ru': geo_data['subregion']['description_ru'],
- Line 216: 'name_ru': self._generate_string('name_ru'),
- Line 219: 'description_ru': self._generate_string('description_ru'),
- Line 247: for lang_key in ['description', 'description_ru', 'description_fr']:

## File: /workspace/tests/data_factory/reader_json.py
- Line 16: 'russian': '_ru',
- Line 37: pairing_ru = data.get("pairing_ru", [])
- Line 40: for en, ru in zip(pairing_en, pairing_ru):
- Line 42: {"name": en, "name_ru": ru}
- Line 285: if k2 in ['type', 'type_ru']:
- Line 290: if k2 in ['region', 'region_ru']:
- Line 326: case 'pairing_ru':
- Line 334: case 'varietal_ru':
- Line 335: result = self.parse_varietal_string_clean(val, 'name_ru')
- Line 349: pairing_ru = []
- Line 352: varietals_ru = []
- Line 357: subregion['name_ru'] = self.camelcase(
- Line 358: self.data[key].pop('subregion_ru', None))
- Line 361: region['name_ru'] = self.camelcase(
- Line 362: self.data[key].pop('region_ru', None))
- Line 365: country['name_ru'] = self.camelcase(
- Line 366: self.data[key].pop('country_ru', None))
- Line 373: subcategory['name_ru'] = self.camelcase(
- Line 374: self.data[key].pop('subcategory_ru', None))
- Line 377: category['name_ru'] = self.camelcase(
- Line 378: self.data[key].pop('category_ru', None))
- Line 383: pairing_ru = self.data[key].pop("pairing_ru", [])
- Line 385: for en, ru in zip(pairing_en, pairing_ru):
- Line 386: foods.append({"name": en, "name_ru": ru})
- Line 392: varietals_ru = data[key].pop("varietal_ru", [])
- Line 395: if len(varietals_en) != len(varietals_ru):
- Line 396: raise ValueError("Списки 'varietal' и 'varietal_ru' "
- Line 399: for item_en, item_ru in zip(varietals_en, varietals_ru):
- Line 401: # if item_en["percentage"] != item_ru["percentage"]:
- Line 403: #                      f"{item_en} vs {item_ru}")
- Line 406: "name_ru": self.camelcase(item_ru["name_ru"])},

## File: /workspace/tests/data_factory/validator.py
- Line 12: "description_ru": "deonOSYyUjPFGaEpHRHg",
- Line 14: "name_ru": None,
- Line 19: "description_ru": "bRfOvqReyRoNomLvQBYP",
- Line 21: "name_ru": "acqjHAEBMBzBVpwzuwLD",
- Line 30: "description_ru": None,
- Line 32: "name_ru": None,
- Line 37: "description_ru": None,
- Line 39: "name_ru": None,
- Line 44: "description_ru": None,
- Line 46: "name_ru": "ESbEsxZPJltaQiYSxbGh",
- Line 61: "description_ru": "iYWPUSzwtQQhQcLgpQwR",
- Line 63: "name_ru": None,
- Line 72: "description_ru": None,
- Line 74: "name_ru": "JHGNTTAXjqbrNRscktYQ",
- Line 81: "description_ru": None,
- Line 93: "description_ru": None,
- Line 95: "name_ru": None,

## File: /workspace/tests/qwen/test_create_item_drink.py
- Line 38: category = Category(name="Wine", name_ru="Вино", name_fr="Vin")
- Line 50: sweetness = Sweetness(name="Dry", name_ru="Сухое", name_fr="Sec")
- Line 56: country = Country(name="France", name_ru="Франция", name_fr="France")
- Line 74: varietal = Varietal(name="Cabernet Sauvignon", name_ru="Каберне Совиньон", name_fr="Cabernet Sauvignon")
- Line 80: food = Food(name="Cheese", name_ru="Сыр", name_fr="Fromage")
- Line 88: "title_ru": "Тестовое вино",
- Line 91: "subtitle_ru": "Сабтайтл тестового вина",
- Line 94: "description_ru": "Описание тестового вина",
- Line 97: "recommendation_ru": "Отлично с сыром",
- Line 100: "madeof_ru": "Виноград",
- Line 130: assert result["drink"]["title_ru"] == "Тестовое вино"
- Line 159: category = Category(name="Wine", name_ru="Вино", name_fr="Vin")
- Line 171: sweetness = Sweetness(name="Dry", name_ru="Сухое", name_fr="Sec")
- Line 177: country = Country(name="France", name_ru="Франция", name_fr="France")
- Line 195: varietal = Varietal(name="Cabernet Sauvignon", name_ru="Каберне Совиньон", name_fr="Cabernet Sauvignon")
- Line 201: food = Food(name="Cheese", name_ru="Сыр", name_fr="Fromage")
- Line 209: "title_ru": "Тестовое вино с изображением",
- Line 212: "subtitle_ru": "Сабтайтл тестового вина с изображением",
- Line 215: "description_ru": "Описание тестового вина с изображением",
- Line 218: "recommendation_ru": "Отлично с сыром",
- Line 221: "madeof_ru": "Виноград",
- Line 314: category = Category(name="Wine", name_ru="Вино", name_fr="Vin")
- Line 334: sweetness = Sweetness(name="Dry", name_ru="Сухое", name_fr="Sec")
- Line 344: country = Country(name="France", name_ru="Франция", name_fr="France")
- Line 43: category = Category(name="Wine", name_ru="Вино", name_fr="Vin")
- Line 55: sweetness = Sweetness(name="Dry", name_ru="Сухое", name_fr="Sec")
- Line 61: country = Country(name="France", name_ru="Франция", name_fr="France")
- Line 79: varietal = Varietal(name="Cabernet Sauvignon", name_ru="Каберне Совиньон", name_fr="Cabernet Sauvignon")
- Line 80: varietal1 = Varietal(name="Shiraz", name_ru="Шираз")
- Line 88: food = Food(name="Cheese", name_ru="Сыр", name_fr="Fromage")
- Line 89: food1 = Food(name="Meet", name_ru="Мясо")
- Line 99: "title_ru": "Тестовое вино",
- Line 102: "subtitle_ru": "Сабтайтл тестового вина",
- Line 105: "description_ru": "Описание тестового вина",
- Line 108: "recommendation_ru": "Отлично с сыром",
- Line 111: "madeof_ru": "Виноград",
- Line 174: category = Category(name="Wine", name_ru="Вино", name_fr="Vin")
- Line 186: sweetness = Sweetness(name="Dry", name_ru="Сухое", name_fr="Sec")
- Line 192: country = Country(name="France", name_ru="Франция", name_fr="France")
- Line 210: varietal = Varietal(name="Cabernet Sauvignon", name_ru="Каберне Совиньон", name_fr="Cabernet Sauvignon")
- Line 216: food = Food(name="Cheese", name_ru="Сыр", name_fr="Fromage")
- Line 224: "title_ru": "Тестовое вино с изображением",
- Line 227: "subtitle_ru": "Сабтайтл тестового вина с изображением",
- Line 230: "description_ru": "Описание тестового вина с изображением",
- Line 233: "recommendation_ru": "Отлично с сыром",
- Line 236: "madeof_ru": "Виноград",
- Line 332: category = Category(name="Wine", name_ru="Вино", name_fr="Vin")
- Line 352: sweetness = Sweetness(name="Dry", name_ru="Сухое", name_fr="Sec")
- Line 362: country = Country(name="France", name_ru="Франция", name_fr="France")

## File: /workspace/tests/tests_common/test_converter.py
- Line 31: name_ru: Optional[str] = None
- Line 37: name_ru: Optional[str] = None
- Line 47: name_ru: Optional[str] = None
- Line 53: name_ru: Optional[str] = None
- Line 58: name_ru: Optional[str] = None
- Line 64: name_ru: Optional[str] = None
- Line 183: "name_ru": {"Каберне Совиньон": 91,
- Line 189: "name_ru": "Каберне Совиньон"},
- Line 192: "name_ru": "Мерло"},
- Line 195: "name_ru": "Пти Вердо"},
- Line 198: "name_ru": "Мальбек"},
- Line 248: assert drink_dict.get('region_ru') is None, 'ключ region_ru не удалился'
- Line 269: assert drink_dict.get('type_ru') is None, 'ключ type_ru не удалился'

## File: /workspace/tests/tests_common/test_translation_utils.py
- Line 8: 'name_ru': None,
- Line 11: 'title_ru': 'russian title',
- Line 14: 'subtitle_ru': None,
- Line 22: 'name_ru': f"english name <{ai}>",
- Line 25: 'title_ru': 'russian title',
- Line 28: 'subtitle_ru': None,

## File: /workspace/tests/tests_crud/test_update.py
- Line 23: 'name_ru': 'обновленные данные', 'description_ru': 'обновленные данные'
- Line 26: 'description_ru': 'обновленные данные',
- Line 27: 'title_ru': 'обновленные данные title'}

## File: /workspace/tests/tests_qwen/test_alchemy_utils_unit.py
- Line 60: def test_get_lang_prefix_ru(self):
- Line 66: assert prefix == '_ru'

## File: /workspace/tests/tests_skipped/test_interim.py
- Line 427: "description_ru": "русск",
- Line 431: "name_ru": "Новокузнецк",
- Line 435: "name_ru": "Кемеровская область",
- Line 438: "name_ru": "Россия",
- Line 445: tzinfo=datetime.timezone.utc), 'name_ru': None,
- Line 446: 'description_ru': 'Нервно исследование хозяйка валюта. Еврейский райком товар пропаганда кольцо багровый.'
- Line 459: 'name_ru': 'Жидкий неожиданно решение.', 'description_ru': None, 'description': None,
- Line 493: dict1 = {'drink': {'title': 'Bolgheri Sassicaia 2014 DOC', 'title_ru': 'Bolgheri Sassicaia 2014 DOC',
- Line 494: 'subtitle': 'Tenuta San Guido', 'subtitle_ru': 'Tenuta San Guido',
- Line 496: 'description_ru': 'Насыщенное, полнотелое вино, глубокого рубинового оттенка предлагает элегантные, сложные ароматы красных фруктов. Вино имеет богатый и плотный, но гармоничный вкус, со сладкими, сбалансированными танинами. \nОбладает послевкусием с глубиной и структурой, обеспечивающей его необычайную продолжительность.',
- Line 498: 'subregion': {'region': {'country': {'name': 'Italy'}, 'name': 'Tuscany', 'name_ru': 'Тоскана'},
- Line 499: 'name': 'Bolgheri', 'name_ru': 'Болгери'}, 'alc': 13.5, 'foods': [
- Line 500: {'superfood': {'name': 'Unclassified', 'name_ru': 'Не классифицированный'},
- Line 501: 'name': 'Game (venison)', 'name_ru': 'Дичь'},
- Line 502: {'superfood': {'name': 'Unclassified', 'name_ru': 'Не классифицированный'}, 'name': 'Lamb',
- Line 503: 'name_ru': 'Баранина'}], 'varietals': [
- Line 504: {'varietal': {'name': 'Cabernet Sauvignon', 'name_ru': 'Каберне Совиньон'}, 'percentage': 85.0},
- Line 505: {'varietal': {'name': 'Cabernet Franc', 'name_ru': 'Каберне Фран'}, 'percentage': 15.0}]},
- Line 508: 'drink': {'title': 'Bolgheri Sassicaia 2014 DOC', 'title_ru': 'Bolgheri Sassicaia 2014 DOC',
- Line 509: 'subtitle': 'Tenuta San Guido', 'subtitle_ru': 'Tenuta San Guido',
- Line 511: 'description_ru': 'Насыщенное, полнотелое вино, глубокого рубинового оттенка предлагает элегантные, сложные ароматы красных фруктов. Вино имеет богатый и плотный, но гармоничный вкус, со сладкими, сбалансированными танинами. \nОбладает послевкусием с глубиной и структурой, обеспечивающей его необычайную продолжительность.',
- Line 513: 'subregion': {'region': {'country': {'name': 'Italy'}, 'name': 'Tuscany', 'name_ru': 'Тоскана'},
- Line 514: 'name': 'Bolgheri', 'name_ru': 'Болгери'}, 'alc': 13.5, 'id': 1}, 'vol': 0.75,

## File: /workspace/tests/tests_skipped/test_routers.py
- Line 69: 'description_ru': 'changed_Range important several short box picture. '
- Line 72: 'name_ru': 'changed_Christopher King',
- Line 94: 'firstname': 'name_ru',
- Line 163: "name_ru": "Заработать",
- Line 166: "description_ru": "Зачем висеть смеяться кидать пропаганда художественный основание тусклый. Жить спалить лиловый возбуждение. Наткнуться редактор растеряться тяжелый ложиться материя. Построить наступать успокоиться. Скользить кузнец засунуть светило нервно заявление передо металл.",
- Line 198: "name_ru": "Испания",
- Line 201: "description_ru": "Испания — страна в Европе, известная своими винами.",
- Line 205: "name_ru": "Рибера-дель-Дуэро",
- Line 208: "description_ru": "Рибера-дель-Дуэро — винный регион в Испания.",
- Line 212: "name_ru": "Алавеса",
- Line 215: "description_ru": "Алавеса — субрегион Рибера-дель-Дуэро.",
- Line 501: "description_ru": "string",
- Line 503: "name_ru": "string",
- Line 509: "description_ru": "string",
- Line 511: "name_ru": "string",
- Line 517: "description_ru": "string",
- Line 519: "name_ru": "string",
- Line 527: "description_ru": "string",
- Line 529: "name_ru": "string",
- Line 534: "description_ru": "string",
- Line 536: "name_ru": "string",
- Line 541: "description_ru": "string",
- Line 543: "name_ru": "string",
- Line 558: "description_ru": "string",
- Line 560: "name_ru": "string",
- Line 569: "description_ru": "string",
- Line 571: "name_ru": "string",
- Line 579: "description_ru": "string",
- Line 591: "description_ru": "string",
- Line 593: "name_ru": "string",