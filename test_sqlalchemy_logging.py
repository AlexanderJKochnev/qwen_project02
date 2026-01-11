#!/usr/bin/env python3
"""
Простой тест для проверки отключения логирования SQLAlchemy
"""

import logging
import sys
from io import StringIO

# Устанавливаем уровень логирования до начала импорта
logging.getLogger('sqlalchemy').setLevel(logging.CRITICAL)
logging.getLogger('sqlalchemy.engine').setLevel(logging.CRITICAL)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.CRITICAL)
logging.getLogger('sqlalchemy.pool').setLevel(logging.CRITICAL)
logging.getLogger('sqlalchemy.orm').setLevel(logging.CRITICAL)

# Перехватываем stdout/stderr для проверки наличия логов
old_stdout = sys.stdout
old_stderr = sys.stderr
captured_output = StringIO()
sys.stdout = captured_output
sys.stderr = captured_output

try:
    # Импортируем основные модули приложения
    from app.core.config.database.db_async import engine
    from sqlalchemy import text
    
    print("Модули импортированы успешно")
    
    # Попробуем выполнить простой запрос
    async def test_query():
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("Запрос выполнен")
    
    import asyncio
    asyncio.run(test_query())
    
except Exception as e:
    print(f"Ошибка: {e}")

# Возвращаем оригинальные потоки
sys.stdout = old_stdout
sys.stderr = old_stderr

# Проверяем, были ли какие-либо сообщения SQLAlchemy
output = captured_output.getvalue()
print("\n=== ЗАХВАЧЕННЫЙ ВЫВОД ===")
print(output)
print("========================")

if "session type:" in output or "hasattr execute:" in output or "session object:" in output:
    print("\n! Обнаружены сообщения от SQLAlchemy - логирование НЕ отключено !")
else:
    print("\n✓ Логирование SQLAlchemy успешно отключено")