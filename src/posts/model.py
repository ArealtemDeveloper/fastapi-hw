from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base

if TYPE_CHECKING:
    from users.model import User


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (Index("ix_posts_author_created_at", "author_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(String(280), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=func.now(),
    )
    likes_count: Mapped[int] = mapped_column(default=0, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("posts.id", name="fk_posts_parent_id_posts", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    user: Mapped[User | None] = relationship("User", back_populates="posts")
    parent: Mapped[Post | None] = relationship(
        "Post", back_populates="replies", remote_side=[id], lazy="raise"
    )
    replies: Mapped[list[Post]] = relationship(
        "Post", back_populates="parent", passive_deletes="all", lazy="raise"
    )
