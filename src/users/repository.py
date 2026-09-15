from typing import Annotated

from fastapi import Depends
from sqlalchemy import select

from core.db import DbSessionDeps
from users.model import User


def get_user_repository(session: DbSessionDeps):
    return UserRepository(session)


class UserRepository:
    def __init__(self, session: DbSessionDeps):
        self.session = session

    async def get_by_email(self, email: str):
        user = await self.session.execute(select(User).where(User.email == email))
        return user.scalar_one_or_none()

    async def get_by_id(self, user_id: int):
        return await self.session.get(User, user_id)

    async def save(self, user: User):
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return user


UserRepositoryDeps = Annotated[UserRepository, Depends(get_user_repository)]
