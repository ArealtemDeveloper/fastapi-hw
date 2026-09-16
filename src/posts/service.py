from datetime import timedelta
from math import ceil
from typing import Annotated

from fastapi import Depends

from core.settings import SettingsDeps
from posts.errors import (
    AuthorNotFoundError,
    PostDebounceError,
    PostNotFoundError,
    PostPermissionError,
)
from posts.model import Post
from posts.schemas import CreatePostRequest, GetAllPostsParams, UpdatePostRequest

from .repository import PostRepository, PostRepositoryDeps


def get_post_service(repo: PostRepositoryDeps, settings: SettingsDeps):
    return PostService(repo, settings.post_settings.debounce_time)


class PostService:
    def __init__(self, repo: PostRepository, debounce_time: int):
        self.repo = repo
        self.debounce_time = debounce_time

    async def get_post_id(self, post_id: int):
        return await self.repo.get_by_id(post_id)

    async def get_replies(self, post_id: int):
        return await self.repo.get_replies(post_id)

    async def get_all_posts_with_params(self, params: GetAllPostsParams):
        return await self.repo.get_all(params.offset, params.limit)

    async def create_post(
        self, data: CreatePostRequest, author_id: int, parent_id: int | None = None
    ) -> Post:
        # Authentication already starts this session's transaction. Keep its lock,
        # interval check and INSERT together until save() commits.
        try:
            if not await self.repo.lock_author(author_id):
                raise AuthorNotFoundError
            if parent_id is not None and await self.repo.get_by_id(parent_id) is None:
                raise PostNotFoundError

            now = await self.repo.current_time()
            last_created_at = await self.repo.last_created_at(author_id)
            if last_created_at is not None:
                remaining = (
                    last_created_at + timedelta(seconds=self.debounce_time) - now
                ).total_seconds()
                if remaining > 0:
                    raise PostDebounceError(ceil(remaining))

            post = Post(
                content=data.content,
                author_id=author_id,
                parent_id=parent_id,
                created_at=now,
                updated_at=now,
            )
            return await self.repo.save(post)
        except Exception:
            await self.repo.rollback()
            raise

    async def update_post(self, data: UpdatePostRequest, post_id: int, author_id: int):
        post = await self.get_post_id(post_id)

        if post is None:
            return None
        if post.author_id != author_id:
            raise PostPermissionError

        patch = data.model_dump(exclude_unset=True)

        for field, value in patch.items():
            setattr(post, field, value)
        post.updated_at = await self.repo.current_time()
        await self.repo.save(post)

        return post

    async def delete_post(self, post_id: int, author_id: int):
        post = await self.get_post_id(post_id)

        if post is None:
            return None
        if post.author_id != author_id:
            raise PostPermissionError

        post.is_deleted = True
        await self.repo.save(post)
        return True

    async def increase_post_likes(self, post_id: int):
        return await self.repo.increase_likes(post_id)


PostServiceDeps = Annotated[PostService, Depends(get_post_service)]
