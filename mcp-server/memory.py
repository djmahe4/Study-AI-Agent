from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import datetime
from config import settings

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True)  # session_id
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String)  # user or assistant
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class MemoryDB:
    def __init__(self, db_path: str = f"sqlite+aiosqlite:///{settings.DB_PATH}"):
        self.engine = create_async_engine(db_path)
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def add_message(self, session_id: str, role: str, content: str):
        async with self.async_session() as session:
            # Ensure conversation exists
            stmt = await session.get(Conversation, session_id)
            if not stmt:
                new_conv = Conversation(id=session_id)
                session.add(new_conv)
                await session.flush()
            
            new_msg = Message(session_id=session_id, role=role, content=content)
            session.add(new_msg)
            await session.commit()

    async def get_messages(self, session_id: str, limit: int = 20) -> list:
        async with self.async_session() as session:
            from sqlalchemy import select
            stmt = select(Message).where(Message.session_id == session_id).order_by(Message.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            messages = result.scalars().all()
            return [{"role": m.role, "content": m.content} for m in reversed(messages)]
