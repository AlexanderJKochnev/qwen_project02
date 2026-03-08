# app/auth/routers/user.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config.database.db_async import get_db
from app.core.schemas.base import DeleteResponse
from app.auth.repository import UserRepository
from app.auth.service import UserService
from app.auth.schemas import UserCreate, UserRead, UserResponse, UserUpdate
from app.auth.dependencies import get_current_active_user
from app.auth.models import User
from app.core.config.project_config import settings

prefix = settings.USER_PREFIX
router = APIRouter(prefix=f"/{prefix}", tags=[f"{prefix}"])

repository = UserRepository
service = UserService
model = User


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, session: AsyncSession = Depends(get_db)):
    #   Создание нового пользователя с проверкой, существует ли пользователь с таким именем
    try:
        db_user, exist = await service.get_or_create(user, repository, model, session, default=('username',))
        if not exist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered"
            )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'register user.error: {e}')
    return db_user


@router.get("/get_full", response_model=List[UserResponse], status_code=status.HTTP_200_OK)
async def get_users(session: AsyncSession = Depends(get_db)):
    """ получениее списка пользователей """
    result = await service.get_full(repository, model, session)
    return result


@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: UserRead = Depends(get_current_active_user)):
    """ получить данные о себе """
    return current_user


@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    """ проверка отклика """
    return {"message": f"Hello {current_user.username}"}


@router.get("/{id}", response_model=UserResponse)
async def read_user(id: int, db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(get_current_active_user)):
    """Получение пользователя по ID"""
    user = await repository.get_by_id(id=id, model=User, session=db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{id}", response_model=UserResponse)
async def update_user(
    id: int, user_update: UserUpdate, background_task: BackgroundTasks, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """ Обновление данных пользователя """
    if current_user.id != id and current_user.is_superuser is False:
        # только super или сам пользователь менять свои данные
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = await service.patch(id, user_update, repository, model, background_task, db)
    user: User = result.get('data')
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user_dict = user.to_dict()
    return UserResponse(**user_dict)


@router.delete("/{id}", response_model=DeleteResponse)
async def delete_user(id, int, background_task: BackgroundTasks, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_active_user)):
    return await service.delete(id, model, repository, background_task, db)
