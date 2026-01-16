#!/usr/bin/env python3
"""
Тестирование динамических локализованных полей
"""
import sys
import os
sys.path.insert(0, '/workspace')

from app.support.drink.schemas import CustomReadApiSchema, CustomReadFlatSchema
from app.support.item.schemas import CustomReadFlatSchema as ItemCustomReadFlatSchema, CustomReadSchema as ItemCustomReadSchema
from app.core.config.project_config import settings


def test_dynamic_fields():
    print("Тестируем динамические локализованные поля...")
    
    print(f"Доступные языки: {settings.LANGUAGES}")
    print(f"Язык по умолчанию: {settings.DEFAULT_LANG}")
    
    # Создаем фиктивный объект для тестирования
    class MockDrink:
        def __init__(self):
            self.updated_at = None
        
        def __getattr__(self, name):
            # Возвращаем фиктивный словарь для любого языка
            if name in settings.LANGUAGES:
                return {"title": f"Title in {name}", "description": f"Description in {name}"}
            raise AttributeError(f"'MockDrink' object has no attribute '{name}'")
    
    # Тестируем CustomReadApiSchema
    print("\nТестируем CustomReadApiSchema:")
    # Создаем объект напрямую, так как у него нет полей в конструкторе
    api_schema = CustomReadApiSchema.__new__(CustomReadApiSchema)
    # Устанавливаем атрибуты напрямую
    api_schema.drink = MockDrink()
    api_schema.title = "Test Title"
    api_schema.description = "Test Description"
    api_schema.subcategory = None
    api_schema.sweetness = None
    api_schema.subregion = None
    api_schema.alc = None
    api_schema.sugar = None
    api_schema.age = None
    api_schema.foods = None
    api_schema.food_associations = None
    api_schema.varietal_associations = None
    
    # Проверяем наличие динамических полей
    for lang in settings.LANGUAGES:
        try:
            lang_data = getattr(api_schema, lang)
            print(f"  Поле '{lang}': {lang_data}")
        except AttributeError as e:
            print(f"  Ошибка получения поля '{lang}': {e}")
    
    # Тестируем CustomReadFlatSchema
    print("\nТестируем CustomReadFlatSchema:")
    # Создаем объект напрямую
    flat_schema = CustomReadFlatSchema.__new__(CustomReadFlatSchema)
    flat_schema.title = "Test Title"
    flat_schema.description = "Test Description"
    flat_schema.subcategory = None
    flat_schema.sweetness = None
    flat_schema.subregion = None
    flat_schema.alc = None
    flat_schema.sugar = None
    flat_schema.age = None
    flat_schema.foods = None
    flat_schema.food_associations = None
    flat_schema.varietal_associations = None
    
    # Проверяем наличие динамических полей
    for lang in settings.LANGUAGES:
        try:
            lang_data = getattr(flat_schema, lang)
            print(f"  Поле '{lang}': {lang_data}")
        except AttributeError as e:
            print(f"  Ошибка получения поля '{lang}': {e}")
    
    # Тестируем ItemCustomReadFlatSchema
    print("\nТестируем ItemCustomReadFlatSchema:")
    # Создаем объект напрямую
    item_flat_schema = ItemCustomReadFlatSchema.__new__(ItemCustomReadFlatSchema)
    item_flat_schema.id = 1
    item_flat_schema.drink = MockDrink()
    
    # Проверяем наличие динамических полей
    for lang in settings.LANGUAGES:
        try:
            lang_data = getattr(item_flat_schema, lang)
            print(f"  Поле '{lang}': {lang_data}")
        except AttributeError as e:
            print(f"  Ошибка получения поля '{lang}': {e}")
    
    print("\nТестирование завершено!")


if __name__ == "__main__":
    test_dynamic_fields()