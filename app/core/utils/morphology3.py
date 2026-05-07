# app/core/utils/morphology3.py
import re
import nltk
from nltk.stem import WordNetLemmatizer
from pymorphy3 import MorphAnalyzer
from functools import lru_cache

# Инициализация
_morph_ru = MorphAnalyzer()
_lemmatizer_en = WordNetLemmatizer()

# Регулярки для "винного мусора"
# Удаляем: мл, ml, л, l, % vol, градусы, года (2020), спецсимволы
RE_WINE_GARBAGE = re.compile(
    r'\b(\d+(ml|мл|l|л|vol|%|gr|гр|deg|год|г))\b|'  # Объемы и ед. изм
    r'\b\d{4}\b|'  # Года (4 цифры)
    r'[^\w\s]',  # Пунктуация
    re.IGNORECASE
)


@lru_cache(maxsize=100000)
def get_lemma(word: str) -> str:
    if not word or not isinstance(word, str):
        return ""

    # 1. Базовая очистка мусора
    word = RE_WINE_GARBAGE.sub('', word).strip().lower()
    if not word or len(word) < 2:  # Игнорируем одиночные буквы после чистки
        return ""

    # 2. Определение языка и лемматизация
    if re.search('[а-яА-ЯёЁ]', word):
        return _morph_ru.parse(word)[0].normal_form

    # Английский (пытаемся как сущ., потом как глагол)
    lemma = _lemmatizer_en.lemmatize(word, pos='n')
    if lemma == word:
        lemma = _lemmatizer_en.lemmatize(word, pos='v')

    return lemma
