from typing import AsyncGenerator, Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase

from core.settings import Settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

settings = Settings() # type: ignore[call-arg]

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True
)

async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

async def check_db(session: AsyncSession) -> int:
    result = await session.execute(select(1))
    return result.scalar_one()

class Base(DeclarativeBase):
    pass

DbSessionDeps = Annotated[
    AsyncSession,
    Depends(get_session)
]
