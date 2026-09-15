from typing import Annotated
from fastapi import Depends

from users.jwt import create_access_token
from users.model import User
from users.repository import UserRepositoryDeps
from users.schemas import UserLoginRequest, UserRegisterRequest
from users.security import hash_password, verify_password


def get_user_service(repo: UserRepositoryDeps):
    return UserService(repo)


class UserService:
    def __init__(self, repo: UserRepositoryDeps):
        self.repo = repo

    async def get_by_email(self, email: str):
        return await self.repo.get_by_email(email)

    async def get_by_id(self, user_id: int):
        return await self.repo.get_by_id(user_id)

    async def register(self, data: UserRegisterRequest) -> str | None:
        user = await self.get_by_email(data.email)

        if user:
            return None

        hashed_password = hash_password(data.password)
        formatted_user = User(email=data.email, password_hash=hashed_password)

        await self.repo.save(formatted_user)
        token = create_access_token(formatted_user.id)

        return token

    async def login(self, data: UserLoginRequest) -> str | None:
        user = await self.get_by_email(data.email)

        if user is None:
            return None
        if not verify_password(data.password, user.password_hash):
            return None

        token = create_access_token(user.id)
        return token


UserServiceDeps = Annotated[UserService, Depends(get_user_service)]
