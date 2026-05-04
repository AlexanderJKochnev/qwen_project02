# app/core/utils/morphology.py
#  НЕ ИСПОЛЬЗУЕТСЯ !!!

# Совместимость pymorphy2 с Python 3.11+
import inspect
if not hasattr(inspect, 'getargspec'):
    def getargspec(func):
        spec = inspect.getfullargspec(func)
        return spec.args, spec.varargs, spec.varkw, spec.defaults
    inspect.getargspec = getargspec


from pymorphy2 import MorphAnalyzer

morph = MorphAnalyzer()

# Список распространённых предлогов, после которых идёт косвенный падеж
PREPOSITIONS = {'с', 'со', 'к', 'ко', 'для', 'от', 'из', 'у', 'на', 'в', 'о', 'об', 'про'}


def to_nominative(phrase: str) -> str:
    """
    Пытается привести фразу на русском языке к именительному падежу,
    заменяя первое существительное на форму именительного падежа.
    """
    phrase = phrase.strip()
    if not phrase:
        return phrase

    # Убираем начальный предлог, если он есть
    words = phrase.split()
    if not words:
        return phrase

    first_word = words[0].lower()
    if first_word in PREPOSITIONS:
        # Отбрасываем предлог
        rest = ' '.join(words[1:])
    else:
        rest = phrase

    # Разбиваем оставшуюся часть на слова
    rest_words = rest.split()
    if not rest_words:
        return phrase

    # Пытаемся преобразовать первое слово в именительный падеж
    first_noun = rest_words[0]
    parsed = morph.parse(first_noun)

    # Ищем разбор как существительного
    nominative_word = None
    for p in parsed:
        if 'NOUN' in p.tag or 'nomn' in p.tag:
            # Пробуем поставить в именительный падеж
            try:
                nominative = p.inflect({'nomn'})
                if nominative:
                    nominative_word = nominative.word
                    break
            except Exception:
                continue

    # Если не удалось — оставляем как есть
    if nominative_word is None:
        nominative_word = first_noun

    # Собираем фразу обратно: именительное существительное + остальное
    result = [nominative_word] + rest_words[1:]
    return ' '.join(result)
