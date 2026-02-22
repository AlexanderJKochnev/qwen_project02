# app.auth.service.py
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.repository import UserRepository
from app.auth.models import User
from app.core.services.service import Service
from app.auth.schemas import UserInDB
from app.core.types import ModelType


class UserService(Service):
    pass

    @classmethod
    async def get_or_create(cls, data: User, repository: UserRepository,
                            model: ModelType, session: AsyncSession,
                            default: List[str] = None, **kwargs) -> Tuple[ModelType, bool]:
        try:
            data_dict = data.model_dump(exclude_unset=True)
            filter = {key: val for key, val in data_dict.items() if key in ('username', 'email')}
            response = await repository.get_by_username(filter, model, session)
            # response = await repository.get_by_fields(filter, model, session)
            if response:
                return response, False  # запись существует
            else:
                verified_data = UserInDB(**data_dict)
                data = User(**verified_data.model_dump())
                result = await repository.create(data, session)
                return result, True
        except Exception as e:
            print(f'UserService.get_or_create: {e}')
