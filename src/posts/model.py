from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base

if TYPE_CHECKING:
    from users.model import User

class Post(Base):
    __tablename__ = "posts"

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
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, default=1)

    user: Mapped["User"] = relationship(
        "User",
        back_populates="posts"
    )

    def __init__(self, content: str):
        self.content = content
