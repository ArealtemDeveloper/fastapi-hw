from fastapi import APIRouter, HTTPException

from users.schemas import (
    GetUserResponse,
    UserLoginRequest,
    TokenResponse,
    UserRegisterRequest,
)
from users.service import UserServiceDeps


router = APIRouter(prefix="/v1/users", tags=["Users"])


@router.get(
    "/{user_id}",
    response_model=GetUserResponse,
    status_code=200,
    description="""
    Получение пользователя по id
""",
)
async def get_user(service: UserServiceDeps, user_id: int):
    user = await service.get_by_id(user_id)

    if user is None:
        raise HTTPException(404, "User not found")

    return GetUserResponse(id=user.id, email=user.email)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    description="""
    Создание пользователя
""",
)
async def register(service: UserServiceDeps, data: UserRegisterRequest):
    token = await service.register(data)

    if token is None:
        raise HTTPException(409, "User is already exist")

    return TokenResponse(token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=200,
    description="""
    Вход в аккаунт пользователя
""",
)
async def login(service: UserServiceDeps, data: UserLoginRequest):
    token = await service.login(data)

    if token is None:
        raise HTTPException(401, "Invalid credentials")

    return TokenResponse(token=token)
