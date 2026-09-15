from pydantic import BaseModel, field_validator


class UserRegisterRequest(BaseModel):
    name: str
    email: str
    password: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        if not value.strip():
            raise ValueError("name should be valid string")
        return value

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
    name: str


class TokenResponse(BaseModel):
    token: str
