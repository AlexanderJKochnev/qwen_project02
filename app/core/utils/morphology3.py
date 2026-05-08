# app/core/utils/morphology3.py
import re
# import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from pymorphy3 import MorphAnalyzer
from functools import lru_cache
from nltk.corpus import wordnet as wn

# Инициализация
_morph_ru = MorphAnalyzer()
_lemmatizer_en = WordNetLemmatizer()

# Загружаем стоп-слова (nltk подтянет их из вашей папки /corpora/stopwords/)
try:
    _stop_words = set(stopwords.words('russian') + stopwords.words('english'))
except LookupError:
    _stop_words = set()  # На случай, если база еще не проброшена

# Регулярка для "винного мусора" (цифры, объемы, спецсимволы)
RE_WINE_GARBAGE = re.compile(
    r'\b(\d+(ml|мл|l|л|vol|%|gr|гр|deg|год|г|кв))\b|'
    r'\b\d+\b|'  # Удаляем все чистые цифры
    r'[^\w\s]', re.IGNORECASE
)


@lru_cache(maxsize=100000)
def get_lemma(word: str) -> str:
    if not word or not isinstance(word, str):
        return ""

    # 1. Предварительная очистка от спецсимволов и цифр
    word = RE_WINE_GARBAGE.sub('', word).strip().lower()

    # 2. Проверка: не является ли слово стоп-словом ДО лемматизации (артикли "a", "the")
    if not word or word in _stop_words or len(word) < 2:
        return ""

    # 3. Лемматизация
    if re.search('[а-яА-ЯёЁ]', word):
        lemma = _morph_ru.parse(word)[0].normal_form
    else:
        lemma = _lemmatizer_en.lemmatize(word, pos='n')
        if lemma == word:
            lemma = _lemmatizer_en.lemmatize(word, pos='v')

    # 4. Повторная проверка: не стало ли слово стоп-словом ПОСЛЕ лемматизации
    # (актуально для русских союзов и предлогов, например "своими" -> "свой")
    if lemma in _stop_words:
        return ""

    return lemma


@lru_cache(maxsize=50000)
def get_synonym_leader(lemma: str) -> str:
    """
    Находит эталонное слово для группы синонимов.
    Если синонимов нет, возвращает саму лемму.
    """
    if not lemma:
        return ""

    # Проверка для английского языка через WordNet
    synsets = wn.synsets(lemma, lang='eng')
    if synsets:
        # Берем самый первый (частотный) синсет
        # И из него берем имя первой леммы как "лидера" группы
        leader = synsets[0].lemmas()[0].name().lower().replace('_', ' ')
        return leader

    # Для русского языка:
    # В NLTK OMW 1.4 поддержка русского слабая.
    # Если нужна высокая точность для РФ, здесь обычно подключают
    # небольшой JSON-словарь специфических винных синонимов.

    return lemma
