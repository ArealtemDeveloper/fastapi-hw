from datetime import datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import DbSessionDeps
from posts.model import Post
from users.model import User


def get_post_repository(session: DbSessionDeps):
    return PostRepository(session)


class PostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, post_id: int):
        return await self.session.scalar(
            select(Post).where(Post.id == post_id, Post.is_deleted.is_(False))
        )

    async def get_replies(self, post_id: int):
        result = await self.session.scalars(
            select(Post)
            .where(Post.parent_id == post_id, Post.is_deleted.is_(False))
            .order_by(Post.created_at, Post.id)
        )
        return list(result.all())

    async def lock_author(self, author_id: int) -> bool:
        # Lock a row that exists even before the author's first post.
        result = await self.session.scalar(
            select(User.id).where(User.id == author_id).with_for_update()
        )
        return result is not None

    async def current_time(self) -> datetime:
        # Existing columns store timestamps without a timezone. Keep UTC consistently.
        # clock_timestamp() is evaluated AFTER any wait for the author lock.
        result = await self.session.execute(
            select(func.timezone("UTC", func.clock_timestamp()))
        )
        return result.scalar_one()

    async def last_created_at(self, author_id: int) -> datetime | None:
        # Deleted posts and replies also count towards the publication interval.
        return await self.session.scalar(
            select(Post.created_at)
            .where(Post.author_id == author_id)
            .order_by(Post.created_at.desc(), Post.id.desc())
            .limit(1)
        )

    async def rollback(self) -> None:
        await self.session.rollback()

    async def save(self, post: Post):
        self.session.add(post)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        await self.session.refresh(post)
        return post

    async def increase_likes(self, post_id: int) -> Post | None:
        post = await self.session.scalar(
            update(Post)
            .where(Post.id == post_id, Post.is_deleted.is_(False))
            .values(likes_count=func.coalesce(Post.likes_count, 0) + 1)
            .returning(Post)
        )
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return post

    async def get_all(self, offset: int, limit: int):
        total_query = (
            select(func.count()).select_from(Post).where(Post.is_deleted.is_(False))
        )
        total_count = await self.session.execute(total_query)
        total = total_count.scalar_one()

        posts_query = (
            select(Post)
            .order_by(Post.created_at.desc(), Post.id.desc())
            .limit(limit)
            .offset(offset)
            .where(Post.is_deleted.is_(False))
        )
        posts = await self.session.execute(posts_query)

        result = list(posts.scalars().all())

        return total, result


PostRepositoryDeps = Annotated[PostRepository, Depends(get_post_repository)]
