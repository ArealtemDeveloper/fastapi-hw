import logging

from fastapi import APIRouter, Depends, HTTPException

from .schemas import (
    GetAllPostsParams,
    GetAllPostsResponse,
    PostPath,
    CreatePostRequest,
    UpdatePostRequest,
    UpdatePostResponse,
    GetPostResponse,
    CreatePostResponse,
    DeletePostResponse,
)
from .service import PostServiceDeps

router = APIRouter(prefix="/v1/posts", tags=["Posts"])

logger = logging.getLogger(__name__)


@router.get(
    "/{post_id}",
    response_model=GetPostResponse,
    description="""
    Получения id поста
""",
)
async def get_post(service: PostServiceDeps, path: PostPath = Depends()):
    post = await service.get_post_id(path.post_id)

    if post is None:
        raise HTTPException(404, "Post not found")

    return GetPostResponse(
        id=post.id,
        content=post.content,
        created_at=post.created_at,
        updated_at=post.updated_at,
        likes_count=post.likes_count,
        is_deleted=post.is_deleted,
    )


@router.get(
    "/",
    response_model=GetAllPostsResponse,
    description="""
    Получения всех постов с query параметрами
""",
)
async def get_all_posts(
    service: PostServiceDeps, params: GetAllPostsParams = Depends()
):
    total, posts = await service.get_all_posts_with_params(params)

    return GetAllPostsResponse(
        posts=[
            GetPostResponse.model_validate(post, from_attributes=True) for post in posts
        ],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@router.post(
    "/",
    response_model=CreatePostResponse,
    status_code=201,
    description="""
    Создание поста
""",
)
async def create_post(service: PostServiceDeps, data: CreatePostRequest):
    post = await service.create_post(data)
    return CreatePostResponse(
        id=post.id,
        content=post.content,
        created_at=post.created_at,
        updated_at=post.updated_at,
        likes_count=post.likes_count,
        is_deleted=post.is_deleted,
    )


@router.patch(
    "/{post_id}",
    response_model=UpdatePostResponse,
    description="""
    Обновление поста
""",
)
async def update_post(
    service: PostServiceDeps, data: UpdatePostRequest, path: PostPath = Depends()
):
    post = await service.update_post(data, path.post_id)

    if post is None:
        raise HTTPException(404, "Post not found")

    return UpdatePostResponse(
        id=post.id,
        content=post.content,
        created_at=post.created_at,
        updated_at=post.updated_at,
        likes_count=post.likes_count,
        is_deleted=post.is_deleted,
    )


@router.delete(
    "/{post_id}",
    response_model=DeletePostResponse,
    description="""
    Удаление поста
""",
)
async def delete_post(service: PostServiceDeps, path: PostPath = Depends()):
    res = await service.delete_post(path.post_id)

    if res is None:
        raise HTTPException(404, "Post not found")

    return DeletePostResponse(removed_post_id=path.post_id)


@router.patch(
    "/{post_id}/like",
    response_model=GetPostResponse,
    description="""
    Увеличение лайков поста
""",
)
async def increase_post_like(service: PostServiceDeps, path: PostPath = Depends()):
    post = await service.increase_post_likes(path.post_id)

    if post is None:
        raise HTTPException(404, "Post not found")

    return GetPostResponse(
        id=post.id,
        content=post.content,
        created_at=post.created_at,
        updated_at=post.updated_at,
        likes_count=post.likes_count,
        is_deleted=post.is_deleted,
    )
