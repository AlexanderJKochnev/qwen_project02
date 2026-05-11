# app.core.utils.spacy_utils.py
import spacy
from datasketch import MinHash
from functools import lru_cache
import re
from app.core.hash_norm import tokenize


# Загружаем модель (отключаем лишнее: парсер и распознавание сущностей для скорости)
nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])

# Список стоп-единиц измерения
UNITS = {'ml', 'kg', 'km', 'h', 'kmh', 'mm', 'cm', 'm', 'g', 'oz', 'lb'}


def clean_text(text: str) -> str:
    """
    Базовая очистка строки перед обработкой.
    """
    if not text:
        return ""
    # Убираем спецсимволы и цифры, оставляя только слова
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    return text.lower().strip()


@lru_cache(maxsize=10000)
def get_minhash(lemmas_tuple: tuple, num_perm=128):
    """
    Создает MinHash из кортежа лемм.
    Используем tuple, так как list нельзя кэшировать в lru_cache.
    """
    m = MinHash(num_perm=num_perm)
    for lemma in lemmas_tuple:
        m.update(lemma.encode('utf8'))
    return m.digest()  # Возвращает массив чисел (сигнатуру)


def process_texts(texts: list[str]):
    """
    Основная функция: лемматизация + фильтрация + получение MinHash.
    texts: список входящих строк.
    """
    results = []

    # 1. Предварительная очистка
    cleaned_texts = [clean_text(t) for t in texts]
    cleaned_texts1 = [' '.join(tokenize(t)) for t in texts]
    print(cleaned_texts)
    print(cleaned_texts1)
    # 2. Пакетная обработка spaCy (nlp.pipe эффективнее для bulk)
    # n_process=-1 задействует все ядра CPU
    for doc in nlp.pipe(cleaned_texts, batch_size=1000, n_process=-1):
        lemmas = []
        for token in doc:
            # Фильтрация:
            # - не стоп-слово (союзы/предлоги)
            # - не пунктуация
            # - не единица измерения
            # - длина больше 2 символов
            if not token.is_stop and not token.is_punct and token.lemma_ not in UNITS and len(token.lemma_) > 2:
                lemmas.append(token.lemma_)

        # Убираем дубликаты слов внутри одной записи
        unique_lemmas = tuple(sorted(set(lemmas)))

        if unique_lemmas:
            # Получаем MinHash (из кэша, если такой набор слов уже был)
            signature = get_minhash(unique_lemmas)
            results.append(
                {"lemmas": list(unique_lemmas), "signature": signature.tolist()  # Готово для вставки в ClickHouse
                 }
            )
        else:
            results.append({"lemmas": [], "signature": []})

    return results


# --- ПРИМЕР ИСПОЛЬЗОВАНИЯ ---
if __name__ == "__main__":
    raw_data = ["Engine 1.5L with 150 hp and 200 km/h max speed", "Engines 1.5 liters, 150hp, maximum speed 200km/h!",
                "Simple test with some kg and ml", "Hennessy privé Hendrick's, 346 15 Русский язык"]
    processed = process_texts(raw_data)
    for i, res in enumerate(processed):
        print(f"Text {i + 1} Lemmas: {res['lemmas']}")
        print(f"Signature (first 5): {res['signature'][:5]}...")
