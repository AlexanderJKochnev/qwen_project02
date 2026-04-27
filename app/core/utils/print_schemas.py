# app.core.utils.print_schemas.py

# Замените 'your_module' на имя вашего файла,
# а 'YourPydanticModel' на имя вашей схемы
from app.support.item import schemas


def print_pydantic_schema():
    # Генерируем JSON-схему
    from app.core.utils.common_utils import jprint
    sch = schemas.ItemUpdatePreact
    schema = sch.model_json_schema()
    x = schema
    # Выводим в консоль с красивыми отступами
    # print(json.dumps(schema, indent=4, ensure_ascii=False))
    jprint(schema)


if __name__ == "__main__":
    print_pydantic_schema()
