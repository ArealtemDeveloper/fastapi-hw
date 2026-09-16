from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from users.jwt import decode_access_token
from users.model import User
from users.service import UserServiceDeps

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    service: UserServiceDeps,
) -> User:
    unauthorized = HTTPException(
        401, "Invalid or missing credentials", headers={"WWW-Authenticate": "Bearer"}
    )
    if credentials is None:
        raise unauthorized
    user_id = decode_access_token(credentials.credentials)

    if user_id is None:
        raise unauthorized

    user = await service.get_by_id(user_id)

    if user is None:
        raise unauthorized

    return user


CurrentUserDeps = Annotated[User, Depends(get_current_user)]


def get_current_user_id(current_user: CurrentUserDeps) -> int:
    return current_user.id


CurrentUserIdDeps = Annotated[int, Depends(get_current_user_id)]
