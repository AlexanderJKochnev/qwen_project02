# app/admin/create_superuser.py
import asyncio
import getpass
from app.core.config.database.db_async import DatabaseManager
from app.auth.models import User
from app.auth.repository import UserRepository
from sqlalchemy import select


async def create_superuser_interactive():
    """Интерактивное создание суперпользователя"""
    print("=== Создание суперпользователя ===")

    # Ввод данных
    username = input("Введите имя пользователя: ").strip()
    if not username:
        print("Имя пользователя не может быть пустым!")
        return

    email = input("Введите email (необязательно, нажмите Enter для пропуска): ").strip()
    if not email:
        email = None

    # Ввод пароля с подтверждением
    while True:
        password = getpass.getpass("Введите пароль: ")
        if not password:
            print("Пароль не может быть пустым!")
            continue

        password_confirm = getpass.getpass("Подтвердите пароль: ")
        if password != password_confirm:
            print("Пароли не совпадают! Попробуйте еще раз.")
            continue
        break

    async with DatabaseManager.session_maker() as session:
        # Проверяем, существует ли уже пользователь с таким именем
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"Пользователь '{username}' уже существует!")
            # Спрашиваем, хочет ли пользователь обновить существующего
            update = input("Хотите обновить существующего пользователя до суперпользователя? (y/N): ").strip().lower()
            if update in ['y', 'yes', 'да']:
                existing_user.is_superuser = True
                existing_user.is_active = True
                if email:
                    existing_user.email = email
                # Обновляем пароль
                user_repo = UserRepository()
                existing_user.hashed_password = user_repo.get_password_hash(password)
                await session.commit()
                print(f"Пользователь '{username}' обновлен до суперпользователя!")
            else:
                print("Операция отменена.")
            return

        # Создаем суперпользователя
        user_repo = UserRepository()
        user_data = {"username": username,
                     "email": email,
                     "password": password,
                     "is_active": True,
                     "is_superuser": True}

        try:
            user = await user_repo.create(user_data, session)
            print(f"✅ Суперпользователь '{user.username}' успешно создан!")
        except Exception as e:
            print(f"❌ Ошибка при создании пользователя: {e}")


async def create_superuser(login: str = 'admin',
                           email: str = 'admin@example.com',
                           password: str = 'admin'):
    """Создание суперпользователя с заданными параметрами"""
    async with AsyncSessionLocal() as session:
        # Проверяем, существует ли уже пользователь с таким именем
        stmt = select(User).where(User.username == login)
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"Пользователь '{login}' уже существует!")
            return

        # Создаем суперпользователя
        user_repo = UserRepository()
        user_data = {"username": login,
                     "email": email,
                     "password": password,
                     "is_active": True,
                     "is_superuser": True,
                     "disabled": False}

        try:
            user = await user_repo.create(user_data, session)
            print(f"✅ Суперпользователь '{user.username}' успешно создан!")
        except Exception as e:
            print(f"❌ Ошибка при создании пользователя: {e}")


def main():
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        # Интерактивный режим
        asyncio.run(create_superuser_interactive())
    elif len(sys.argv) == 4:
        # Режим с аргументами
        login, email, password = sys.argv[1], sys.argv[2], sys.argv[3]
        asyncio.run(create_superuser(login, email, password))
    else:
        # По умолчанию - интерактивный режим
        asyncio.run(create_superuser_interactive())


if __name__ == "__main__":
    main()
