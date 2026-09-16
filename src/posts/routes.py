from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from users.current_user import CurrentUserIdDeps

from .errors import (
    AuthorNotFoundError,
    PostDebounceError,
    PostNotFoundError,
    PostPermissionError,
)
from .schemas import (
    CreatePostRequest,
    CreatePostResponse,
    DeletePostResponse,
    GetAllPostsParams,
    GetAllPostsResponse,
    GetPostResponse,
    PostPath,
    PostResponse,
    UpdatePostRequest,
    UpdatePostResponse,
)
from .service import PostService, PostServiceDeps

router = APIRouter(prefix="/v1/posts", tags=["Posts"])
PostPathDeps = Annotated[PostPath, Depends()]
PostParamsDeps = Annotated[GetAllPostsParams, Depends()]


@router.get(
    "/{post_id}", response_model=GetPostResponse, description="Пост и его ответы"
)
async def get_post(service: PostServiceDeps, path: PostPathDeps):
    post = await service.get_post_id(path.post_id)
    if post is None:
        raise HTTPException(404, "Post not found")
    replies = await service.get_replies(post.id)
    return GetPostResponse(
        **PostResponse.model_validate(post).model_dump(),
        replies=[PostResponse.model_validate(reply) for reply in replies],
    )


@router.get("/", response_model=GetAllPostsResponse, description="Список постов")
async def get_all_posts(service: PostServiceDeps, params: PostParamsDeps):
    total, posts = await service.get_all_posts_with_params(params)
    return GetAllPostsResponse(
        posts=[PostResponse.model_validate(post) for post in posts],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


async def create_post_response(
    service: PostService,
    data: CreatePostRequest,
    author_id: int,
    parent_id: int | None = None,
) -> CreatePostResponse:
    try:
        post = await service.create_post(data, author_id, parent_id)
    except PostNotFoundError as error:
        raise HTTPException(404, "Post not found") from error
    except AuthorNotFoundError as error:
        raise HTTPException(
            401, "Invalid credentials", headers={"WWW-Authenticate": "Bearer"}
        ) from error
    except PostDebounceError as error:
        raise HTTPException(
            429, str(error), headers={"Retry-After": str(error.retry_after)}
        ) from error
    return CreatePostResponse.model_validate(post)


@router.post(
    "/",
    response_model=CreatePostResponse,
    status_code=201,
    description="Создание поста",
)
async def create_post(
    current_user_id: CurrentUserIdDeps,
    service: PostServiceDeps,
    data: CreatePostRequest,
):
    return await create_post_response(service, data, current_user_id)


@router.post(
    "/{post_id}/reply",
    response_model=CreatePostResponse,
    status_code=201,
    description="Ответ на пост",
)
async def reply_to_post(
    current_user_id: CurrentUserIdDeps,
    service: PostServiceDeps,
    data: CreatePostRequest,
    path: PostPathDeps,
):
    return await create_post_response(service, data, current_user_id, path.post_id)


@router.patch(
    "/{post_id}",
    response_model=UpdatePostResponse,
    description="Редактирование своего поста",
)
async def update_post(
    current_user_id: CurrentUserIdDeps,
    service: PostServiceDeps,
    data: UpdatePostRequest,
    path: PostPathDeps,
):
    try:
        post = await service.update_post(data, path.post_id, current_user_id)
    except PostPermissionError as error:
        raise HTTPException(403, "Only the author can edit this post") from error
    if post is None:
        raise HTTPException(404, "Post not found")
    return UpdatePostResponse.model_validate(post)


@router.delete(
    "/{post_id}",
    response_model=DeletePostResponse,
    description="Мягкое удаление своего поста",
)
async def delete_post(
    current_user_id: CurrentUserIdDeps, service: PostServiceDeps, path: PostPathDeps
):
    try:
        result = await service.delete_post(path.post_id, current_user_id)
    except PostPermissionError as error:
        raise HTTPException(403, "Only the author can delete this post") from error
    if result is None:
        raise HTTPException(404, "Post not found")
    return DeletePostResponse(removed_post_id=path.post_id)


@router.patch(
    "/{post_id}/like",
    response_model=PostResponse,
    description="Увеличение лайков поста",
)
async def increase_post_like(
    current_user_id: CurrentUserIdDeps, service: PostServiceDeps, path: PostPathDeps
):
    post = await service.increase_post_likes(path.post_id)
    if post is None:
        raise HTTPException(404, "Post not found")
    return PostResponse.model_validate(post)
