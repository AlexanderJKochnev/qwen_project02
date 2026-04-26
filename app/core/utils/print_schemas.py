# app.core.utils.print_schemas.py

import json
# Замените 'your_module' на имя вашего файла,
# а 'YourPydanticModel' на имя вашей схемы
from app.support.item import schemas


def print_pydantic_schema():
    # Генерируем JSON-схему
    sch = schemas.ItemUpdatePreact
    schema = sch.model_json_schema()
    # Выводим в консоль с красивыми отступами
    print(json.dumps(schema, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    print_pydantic_schema()