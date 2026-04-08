# изготовление distilled models на базе model2vec
1. Первый запуск (подготовка моделей)
bash
# Установите зависимости (если ещё нет)
pip install sentence-transformers model2vec[distill] torch

# Запустите подготовку моделей
python setup_models.py
Скрипт:

Скачает оригинальную intfloat/multilingual-e5-small в кэш Hugging Face

Выполнит дистилляцию до 256 измерений

Сохранит дистиллированную модель в ./models/distilled_e5_256d/

