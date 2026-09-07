from fastapi import APIRouter, Depends
from .schemas import (
    PostPath,
    CreatePostRequest,
    UpdatePostRequest,
    UpdatePostResponse,
    GetPostResponse,
    CreatePostResponse,
    DeletePostResponse,
)

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get(
    "/{post_id}",
    response_model=GetPostResponse,
    description="""
    Получения id поста
""",
)
def get_post(path: PostPath = Depends()):
    return GetPostResponse(post_id=path.post_id)


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
