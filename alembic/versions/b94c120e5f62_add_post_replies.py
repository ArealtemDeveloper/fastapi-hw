"""Add post replies and index for author publication history.

Revision ID: b94c120e5f62
Revises: f02000f0bc17
"""

import sqlalchemy as sa

from alembic import op

revision = "b94c120e5f62"
down_revision = "f02000f0bc17"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("posts", sa.Column("parent_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_posts_parent_id_posts",
        "posts",
        "posts",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_posts_parent_id", "posts", ["parent_id"])
    op.create_index("ix_posts_author_created_at", "posts", ["author_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_posts_author_created_at", table_name="posts")
    op.drop_index("ix_posts_parent_id", table_name="posts")
    op.drop_constraint("fk_posts_parent_id_posts", "posts", type_="foreignkey")
    op.drop_column("posts", "parent_id")
