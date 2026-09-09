from fastapi import APIRouter, Depends

from core.settings import SettingsDeps
from .schemas import (
    PostPath,
    CreatePostRequest,
    UpdatePostRequest,
    UpdatePostResponse,
    GetPostResponse,
    CreatePostResponse,
    DeletePostResponse,
)
from .service import PostServiceDeps

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get(
    "/{post_id}",
    response_model=GetPostResponse,
    description="""
    Получения id поста
""",
)
def get_post(
    settings: SettingsDeps, service: PostServiceDeps, path: PostPath = Depends()
):
    res = service.get_post_id(path.post_id)
    print(settings.app.name)
    print(settings.db.url)
    print(settings.post_settings.debounce_time)
    print(settings.auth.secret)
    return GetPostResponse(post_id=res)


@router.post(
    "/",
    response_model=CreatePostResponse,
    status_code=201,
    description="""
    Создание поста
""",
)
def create_post(data: CreatePostRequest):
    return data


@router.patch(
    "/{post_id}",
    response_model=UpdatePostResponse,
    description="""
    Обновление поста
""",
)
def update_post(data: UpdatePostRequest, path: PostPath = Depends()):
    return UpdatePostResponse(id=path.post_id, content=data.content)


@router.delete(
    "/{post_id}",
    response_model=DeletePostResponse,
    description="""
    Удаление поста
""",
)
def delete_post(path: PostPath = Depends()):
    return DeletePostResponse(removed_post_id=path.post_id)
