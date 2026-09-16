from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PostPath(BaseModel):
    post_id: int


class GetAllPostsParams(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)


class CreatePostRequest(BaseModel):
    content: str = Field(max_length=280)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str):
        if not value.strip():
            raise ValueError("content should be valid string")
        return value


class UpdatePostRequest(BaseModel):
    content: str = Field(max_length=280)
    likes_count: int = Field(ge=0)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str):
        if not value.strip():
            raise ValueError("content should be valid string")
        return value


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    created_at: datetime
    updated_at: datetime
    likes_count: int
    is_deleted: bool
    author_id: int | None
    parent_id: int | None


class GetPostResponse(PostResponse):
    replies: list[PostResponse] = Field(default_factory=list)


class CreatePostResponse(PostResponse):
    pass


class UpdatePostResponse(PostResponse):
    pass


class GetAllPostsResponse(BaseModel):
    posts: list[PostResponse]
    total: int
    offset: int
    limit: int


class DeletePostResponse(BaseModel):
    removed_post_id: int
