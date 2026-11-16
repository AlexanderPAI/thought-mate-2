from uuid import UUID

from openrouter.components.chatmessages import ChatMessagesTypedDict
from sqlalchemy import Uuid, insert, select, update
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative Base for all tables"""


class Session(Base):
    """Session class"""

    __tablename__ = "session"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    messages: Mapped[list[ChatMessagesTypedDict]] = mapped_column(JSONB)


async def load_history(
    session_factory: async_sessionmaker[AsyncSession],
    session_id: UUID,
) -> list[ChatMessagesTypedDict] | None:
    """Load history from session by id"""
    statement = select(Session.messages).where(Session.id == session_id)
    async with session_factory() as db:
        return await db.scalar(statement)


async def save_history(
    session_factory: async_sessionmaker[AsyncSession],
    session_id: UUID,
    messages: list[ChatMessagesTypedDict],
    *,
    create: bool,
) -> bool:
    """Save history from session by id"""
    if create:
        statement = insert(Session).values(id=session_id, messages=messages)
    else:
        statement = (
            update(Session).where(Session.id == session_id).values(messages=messages)
        )

    async with session_factory() as db:
        saved_id = await db.scalar(statement.returning(Session.id))

    return saved_id is not None
