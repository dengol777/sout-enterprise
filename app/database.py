from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

# Создаем асинхронный движок
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # Проверка соединения перед использованием
)

# Фабрика сессий
async_session_factory = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def init_db():
    """Создание таблиц при старте (для dev). В prod используйте Alembic!"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    """Зависимость для инъекции сессии в эндпоинты"""
    async with async_session_factory() as session:
        yield session
