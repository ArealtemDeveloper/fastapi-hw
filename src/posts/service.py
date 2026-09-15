from typing import Annotated
from fastapi import Depends

from posts.model import Post
from posts.schemas import CreatePostRequest, GetAllPostsParams, UpdatePostRequest
from .repository import PostRepository, PostRepositoryDeps


def get_post_service(repo: PostRepositoryDeps):
    return PostService(repo)


class PostService:
    def __init__(self, repo: PostRepository):
        self.repo = repo

    async def get_post_id(self, post_id: int):
        return await self.repo.get_by_id(post_id)

    async def get_all_posts_with_params(self, params: GetAllPostsParams):
        return await self.repo.get_all(params.offset, params.limit)

    async def create_post(self, data: CreatePostRequest):
        post = Post(content=data.content)
        await self.repo.save(post)

        return post

    async def update_post(self, data: UpdatePostRequest, post_id: int):
        post = await self.get_post_id(post_id)

        if post is None:
            return None

        patch = data.model_dump(exclude_unset=True)

        for field, value in patch.items():
            setattr(post, field, value)
            await self.repo.save(post)

        return post

    async def delete_post(self, post_id: int):
        post = await self.get_post_id(post_id)

        if post is None:
            return None

        setattr(post, "is_deleted", True)
        await self.repo.save(post)
        return True

    async def increase_post_likes(self, post_id: int):
        post = await self.get_post_id(post_id)

        if post is None:
            return None

        setattr(post, "likes_count", post.likes_count + 1)
        await self.repo.save(post)
        return post


PostServiceDeps = Annotated[PostService, Depends(get_post_service)]
