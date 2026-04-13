import asyncio
import sys
from loguru import logger
from sqlalchemy import select
# Импорты твоего менеджера и моделей
from app.core.config.database.db_async import DatabaseManager
from app.fill_wordhash import seed_word_dictionary
from app.support import Item
from app.support.hashing.model import WordHash


async def run_seeding():
    # 1. Инициализация БД
    DatabaseManager()

    logger.info("Проверка соединения с базой...")
    try:
        await DatabaseManager.check_connection()
    except Exception as e:
        logger.error(f"Не удалось подключиться к БД: {e}")
        return

    # 2. Запуск процесса
    logger.info("Начинаю наполнение таблицы WordHash...")

    async with DatabaseManager.session_maker() as session:
        try:
            # Используем потоковую выборку, чтобы не забить RAM докера
            # stream() выкачивает данные порциями
            result_stream = await session.stream(
                select(Item.search_content).where(Item.search_content.is_not(None))
            )

            # Передаем стрим в функцию (нужно убедиться, что seed_word_dictionary его примет)
            await seed_word_dictionary(session, result_stream, WordHash)

            logger.success("Наполнение словаря завершено успешно!")
        except Exception as e:
            logger.exception(f"Критическая ошибка при наполнении: {e}")
            await session.rollback()
        finally:
            await session.close()
            await DatabaseManager.close()


if __name__ == "__main__":
    # Настройка логгера (опционально)
    logger.add("seed_process.log", rotation="10 MB")

    try:
        asyncio.run(run_seeding())
    except KeyboardInterrupt:
        logger.warning("Процесс прерван пользователем")
        sys.exit(0)
