from typing import Annotated
from fastapi import Depends
from .repository import PostRepository, PostRepositoryDeps


def get_post_service(repo: PostRepositoryDeps):
    return PostService(repo)


class PostService:
    def __init__(self, repo: PostRepository):
        self.repo = repo

    def get_post_id(self, post_id: int):
        return self.repo.get_by_id(post_id)


PostServiceDeps = Annotated[PostService, Depends(get_post_service)]
