import aiomysql
from contextlib import asynccontextmanager

# Налаштування підключення до бази даних
# DB_CONFIG = {
#     'host': 'srv1566.hstgr.io',   # або '82.197.82.52'
#     'port': 3306,                # за замовчуванням MySQL використовує порт 3306
#     'user': 'u988786009_test_python',
#     'password': '5NtXB@S[&',
#     'db': 'u988786009_test_python'
# }

# @asynccontextmanager
# async def get_db_connection():
#     """
#     Асинхронний контекстний менеджер для підключення до MySQL.
#     Створює пул з'єднань, який потім автоматично закривається.
#     """
#     pool = await aiomysql.create_pool(
#         host=DB_CONFIG['host'],
#         port=DB_CONFIG['port'],
#         user=DB_CONFIG['user'],
#         password=DB_CONFIG['password'],
#         db=DB_CONFIG['db'],
#         autocommit=True
#     )
#     try:
#         yield pool
#     finally:
#         pool.close()
#         await pool.wait_closed()


from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.settings import settings

engine = create_async_engine(settings.MYSQL_URI, echo=True)

async_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

@asynccontextmanager
async def get_mesql() -> AsyncIterator[AsyncSession]:
    """Асинхронний контекстний менеджер для сесії PostgreSQL"""
    session = async_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
