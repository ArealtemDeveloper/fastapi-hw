from pydantic import BaseModel, field_validator

class PostPath(BaseModel):
    post_id: int

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

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str):
        if not value.strip():
            raise ValueError("content should be valid string")
        return value

class UpdatePostResponse(BaseModel):
    id: int
    content: str
