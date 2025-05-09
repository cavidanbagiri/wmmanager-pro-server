
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

# Define the base model (if not already in models.py)

# Connection string (use `postgresql+asyncpg` instead of `postgres+asyncpg`)
connection_string = "postgresql+asyncpg://postgres:cavidan1@localhost/wmdatabase"

# Create async engine with pool_pre_ping to handle connection drops
engine = create_async_engine(
    connection_string,
    echo=True,  # Log SQL queries (disable in production)
    pool_pre_ping=True,  # Checks connection health before use
    pool_size=20,  # Adjust based on your needs
    max_overflow=10,
)

# Session factory with expire_on_commit=False for async safety
SessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()