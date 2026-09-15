from pydantic import BaseModel, field_validator


class UserRegisterRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str):
        if not value.strip():
            raise ValueError("email should be valid string")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):
        if not value.strip():
            raise ValueError("password should be valid string")
        return value


class UserLoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str):
        if not value.strip():
            raise ValueError("email should be valid string")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):
        if not value.strip():
            raise ValueError("password should be valid string")
        return value


class GetUserResponse(BaseModel):
    id: int
    email: str


class TokenResponse(BaseModel):
    token: str
