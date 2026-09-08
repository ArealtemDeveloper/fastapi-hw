from typing import Annotated
from fastapi import Depends


def get_post_repository():
    return PostRepository()


class PostRepository:
    def get_by_id(self, post_id: int):
        return post_id


PostRepositoryDeps = Annotated[PostRepository, Depends(get_post_repository)]
