# app.core.hash_norm.py
"""  нормализация текста для хэширования """
import cityhash
import struct
import string

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


def fast_normalize(text):
    # 1. translate убирает мусор, меняет умляуты и ставит # на место точек/запятых
    text = text.lower().translate(final_map)

    # 2. Теперь разбиваем по пробелам.
    # split() без аргументов эффективно схлопывает любые цепочки пробелов
    tokens = text.split()

    # 3. Очищаем токены от '#' по краям (если это была точка в конце предложения)
    # но оставляем внутри (1#6)
    clean_tokens = [t.strip('#') for t in tokens if len(t) > 1]

    return clean_tokens


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


def fast_normalize_v2(text):
    # ... логика с final_map и .translate() из предыдущего шага ...
    text = text.lower().translate(final_map)
    tokens = text.split()

    clean_hashes = []
    for t in tokens:
        t = t.strip('#')
        if len(t) > 1 and is_valid_token(t):
            h_unsigned = cityhash.CityHash64(t)
            clean_hashes.append(to_signed_bigint(h_unsigned))

    return list(set(clean_hashes)), tokens  # возвращаем хеши
