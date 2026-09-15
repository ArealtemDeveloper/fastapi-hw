from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class PostPath(BaseModel):
    post_id: int


class GetAllPostsParams(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(20, ge=1)


class CreatePostRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str):
        if not value.strip():
            raise ValueError("content should be valid string")
        return value


class UpdatePostRequest(BaseModel):
    content: str
    likes_count: int

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str):
        if not value.strip():
            raise ValueError("content should be valid string")
        return value


class GetPostResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    updated_at: datetime
    likes_count: int
    is_deleted: bool


class CreatePostResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    updated_at: datetime
    likes_count: int
    is_deleted: bool


class UpdatePostResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    updated_at: datetime
    likes_count: int
    is_deleted: bool


class GetAllPostsResponse(BaseModel):
    posts: list[GetPostResponse]
    total: int
    offset: int
    limit: int


class DeletePostResponse(BaseModel):
    removed_post_id: int
