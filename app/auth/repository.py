# app/auth/repository.py
from app.core.repositories.sqlalchemy_repository import Repository
from app.core.types import ModelType
from app.auth.models import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRepository(Repository):
    model = User

    @classmethod
    def get_query(cls, model: ModelType):
        return select(User)

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def get_password_hash(cls, password: str) -> str:
        return pwd_context.hash(password)

    @classmethod
    async def authenticate(cls, username: str, password: str, session: AsyncSession):
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not cls.verify_password(password, user.hashed_password):
            return None
        return user

    @classmethod
    async def create(cls, data: dict, session):
        data["hashed_password"] = cls.get_password_hash(data.pop("password"))
        verified_data = cls.model(**data)
        return await super().create(verified_data, cls.model, session)

    @classmethod
    async def get_superuser_by_username(cls, username: str, session: AsyncSession):
        from sqlalchemy import select
        stmt = select(User).where(User.username == username,
                                  User.is_superuser == True,  # NOQA: E712
                                  User.is_active == True)    # NOQA: E712
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
