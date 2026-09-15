from typing import Annotated
from fastapi import Depends
from sqlalchemy import func, select

from core.db import DbSessionDeps
from posts.model import Post


def get_post_repository(session: DbSessionDeps):
    return PostRepository(session)


class PostRepository:
    def __init__(self, session: DbSessionDeps) -> None:
        self.session = session

    async def get_by_id(self, post_id: int):
        return await self.session.get(Post, post_id)

    async def save(self, post: Post):
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def get_all(self, offset: int, limit: int):
        total_query = (
            select(func.count()).select_from(Post).where(Post.is_deleted != True)
        )
        total_count = await self.session.execute(total_query)
        total = total_count.scalar_one()

        posts_query = (
            select(Post)
            .order_by(Post.created_at.desc(), Post.id.desc())
            .limit(limit)
            .offset(offset)
            .where(Post.is_deleted != True)
        )
        posts = await self.session.execute(posts_query)

        result = list(posts.scalars().all())

        return total, result


PostRepositoryDeps = Annotated[PostRepository, Depends(get_post_repository)]
