import jwt
from datetime import datetime, timezone, timedelta


from core.settings import Settings

settings = Settings()  # type: ignore[call-arg]
ALGORITHM = "HS256"


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.auth.token_ttl)
    payload: dict[str, str | datetime] = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.auth.secret, ALGORITHM)


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.auth.secret, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        return None
