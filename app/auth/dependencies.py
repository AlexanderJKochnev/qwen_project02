# app/auth/dependencies.py
from fastapi import Depends, HTTPException, status, Request, Security
from typing import Optional
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config.database.db_async import get_db
from app.core.config.project_config import settings
from app.auth.repository import UserRepository
# from app.auth.utils import verify_token
from app.auth.models import User


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token",
                                     auto_error=False       # это для неавторизованных внутрисетевых запросов
                                     )
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

TECH_API_KEY = settings.API_KEY

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

user_repo = UserRepository()


async def allow_internal_network(request: Request) -> bool:
    """Быстрая проверка - запрос из внутренней сети Docker"""
    client_host = request.client.host
    # Разрешаем внутренние адреса Docker
    internal_prefixes = [
        "127.0.0.1",  # localhost
        "172.",  # Docker bridge network
        # "192.168.",  # это домашняя сеть не открывать
        "10.",  # Docker internal
        "frontend",  # имя сервиса фронтенда
    ]
    # Быстрая проверка по префиксам
    for prefix in internal_prefixes:
        if client_host.startswith(prefix):
            # отмена внутренних адресов
            return False
    return False


async def get_user_or_internal(
    request: Request, token: Optional[str] = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db)
) -> User:
    """
    Умная dependency:
    - Сначала проверяем внутреннюю сеть (быстро)
    - Только внешние запросы требуют аутентификации
    """
    # 1. Быстрая проверка внутренней сети (~1ms)
    if await allow_internal_network(request):
        # Создаем "системного пользователя" для внутренних запросов
        return User(id=0,
                    username="internal_user",
                    email="internal@localhost",
                    is_active=True,
                    is_superuser=False,
                    hashed_password="")
    if token is None:
        raise credentials_exception  # внешний запрос без токена → ошибка
    # 2. Для внешних запросов - полная аутентификация

    return await get_current_user(token, session)


async def get_active_user_or_internal(
    request: Request, token: Optional[str] = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db)
) -> User:
    """
    Умная dependency с проверкой активности пользователя
    """
    user = await get_user_or_internal(request, token, session)

    # Для внутренних запросов пропускаем проверку активности
    if user.username == "internal_user":
        return user

    # Для реальных пользователей проверяем активность
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_db)):
    """Получение текущего пользователя по JWT токену"""
    try:
        token = token or ''
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await user_repo.get_by_field("username", username, User, session)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
        current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_superuser(
        current_user: User = Depends(get_current_active_user)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=400,
                            detail="The user doesn't have enough privileges")
    return current_user


async def get_current_api_user(
    x_api_key: Optional[str] = Security(api_key_header)
):
    # 1. Проверка API Key (Технический аккаунт)
    print(f'{x_api_key=}')
    print(f'{TECH_API_KEY=}')
    if x_api_key == TECH_API_KEY:
        return {"user": "tech_account", "scope": "all"}

    # 3. Если ничего не подошло
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated aaa",
        headers={"WWW-Authenticate": "Bearer"},
    )
