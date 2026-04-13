# app.core.hash_norm.py
"""  нормализация текста для хэширования """
import string
from functools import lru_cache
import cityhash
import struct

# 1. Формируем строку всех допустимых символов
allowed_chars = (string.ascii_lowercase + string.digits + "abcdefghijklmnopqrstuvwxyz" +
                 "абвгдёежзийклмнопрстуфхцчшщъыьэюя" + "., ")  # добавляем точку и запятую, как вы просили


# 2. Создаем карту для translate:
# По умолчанию заменяем ВЕЩЬ символ (0-65535 для Unicode) на пробел
trans_map = {i: ' ' for i in range(65536)}

# 3. Переопределяем разрешенные символы (они остаются самими собой)
for char in allowed_chars:
    trans_map[ord(char)] = char

# 4. Добавляем вашу европейскую диакритику (сразу с заменой)
extra_fixes = {'ü': 'u', 'ö': 'o', 'ä': 'a', 'ß': 'ss', 'é': 'e', 'è': 'e', 'ç': 'c',  # и так далее
               }
for char, replacement in extra_fixes.items():
    trans_map[ord(char)] = replacement

# 5. Реализуем замену разделителей (.,) на спецсимвол для чисел
# Чтобы потом просто сделать .replace('.', '#').replace(',', '#')
trans_map[ord('.')] = '#'
trans_map[ord(',')] = '#'

# Финальный объект для translate
final_map = str.maketrans({chr(k): v for k, v in trans_map.items()})


def to_signed_bigint(unsigned_64):
    """Конвертирует unsigned CityHash в signed BigInt для Postgres"""
    return struct.unpack('q', struct.pack('Q', unsigned_64))[0]


def is_valid_token(t):
    # Если это число
    if t.isdigit() or ('#' in t and t.replace('#', '').isdigit()):
        try:
            # Пытаемся понять, входит ли число в наш диапазон
            # Для дробных (1#6) берем целую часть
            val = int(t.split('#')[0])
            return 1 <= val <= 2050
        except ValueError:
            return False
    # Если это слово - оставляем (мы уже отсекли 1-символьные в fast_normalize)
    return True


@lru_cache(maxsize=32768)
def get_cached_hash(token: str) -> int:
    """Детерминированный CityHash64 -> Signed BigInt"""
    return struct.unpack('q', struct.pack('Q', cityhash.CityHash64(token)))[0]


def fast_normalize_v4(text: str):
    """Минималистичный генератор токенов"""
    # translate + split + фильтр в одном списковом включении
    return [t for t in (w.strip('#') for w in text.lower().translate(final_map).split()) if
            len(t) > 1 and is_valid_token(t)]
