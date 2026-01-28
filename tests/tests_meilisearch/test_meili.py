import asyncio
from loguru import logger
from app.core.services.meili_service import MeiliManager

# Импортируйте ваши настройки и менеджер
# from app.core.config import settings
# from app.core.meili import MeiliManager


async def test_meili_connection():
    logger.info("Тест: Попытка подключения к Meilisearch...")

    try:
        # 1. Проверка получения клиента
        client = await MeiliManager.get_client()
        if client is None:
            logger.error("Ошибка: Менеджер вернул None вместо клиента!")
            return

        # 2. Проверка здоровья (health)
        health = await client.health()
        logger.success(f"Соединение установлено! Статус: {health.status}")

        # 3. Тест создания индекса
        index_name = "test_connection_index"
        logger.info(f"Тест: Создание индекса '{index_name}'...")
        await client.get_or_create_index(index_name, primary_key="id")

        # 4. Проверка получения индекса
        index = await client.get_index(index_name)
        logger.success(f"Индекс успешно создан и получен. UID: {index.uid}")

        # 5. Очистка (удаление тестового индекса)
        await client.delete_index(index_name)
        logger.info("Тест: Индекс удален.")

        await MeiliManager.disconnect()
        logger.success("Тест завершен успешно!")

    except Exception as e:
        logger.exception(f"Тест провален! Ошибка: {e}")


# if __name__ == "__main__":
#     asyncio.run(test_meili_connection())
