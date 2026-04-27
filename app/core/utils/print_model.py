# app.core.utils.print_model.py

from app.support.drink.model import Drink
from app.support.item.model import Item


def print_model_fields():
    model = Item
    print(f"Поля модели {model.__name__}:")

    # Итерируемся по колонкам таблицы
    for column in model.__table__.columns:
        print(f"{column.key}: {column.type}")


if __name__ == "__main__":
    print_model_fields()
