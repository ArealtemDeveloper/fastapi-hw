from datetime import UTC, datetime, timedelta

import jwt

from core.settings import Settings

settings = Settings()  # type: ignore[call-arg]
ALGORITHM = "HS256"


def create_access_token(user_id: int) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.auth.token_ttl)
    payload: dict[str, str | datetime] = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.auth.secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token,
            settings.auth.secret,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
        user_id = int(payload["sub"])
        return user_id if user_id > 0 else None
    except jwt.PyJWTError, ValueError, KeyError, TypeError:
        return None
