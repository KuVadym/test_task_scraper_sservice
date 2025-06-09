import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.database.postgres.product import (
    create_product,
    delete_product,
    get_product,
    update_product,
)
from app.models.product import Base, ProductDB

# Створюємо тестову БД у пам'яті (SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


# Фікстура для тестової БД
@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# Фікстура для сесії
@pytest.fixture(scope="function")
async def session():
    async with TestingSessionLocal() as session:
        yield session


# Патчимо get_postgres, щоб використовував тестову БД
@pytest.fixture(scope="function", autouse=True)
async def override_get_postgres(mocker, session):
    mocker.patch("app.database.postgres.get_postgres", return_value=session)


# 📌 Тест: Створення продукту
@pytest.mark.asyncio
async def test_create_product(session):
    product = ProductDB(
        id="123",
        name="Test Boot",
        price="99.99",
        brand="Test Brand",
        number="TB123",
        product_details={},
        shipping_returns={},
        images=[],
        variations_data_json={},
    )
    result = await create_product(product)
    assert result is True

    product_in_db = await session.get(ProductDB, "123")
    assert product_in_db is not None
    assert product_in_db.name == "Test Boot"


# 📌 Тест: Отримання продукту
@pytest.mark.asyncio
async def test_get_product(session):
    product = ProductDB(
        id="456",
        name="Another Boot",
        price="129.99",
        brand="BrandX",
        number="BX456",
        product_details={},
        shipping_returns={},
        images=[],
        variations_data_json={},
    )
    await create_product(product)

    fetched_product = await get_product("456")
    assert fetched_product is not None
    assert fetched_product.name == "Another Boot"


# 📌 Тест: Оновлення продукту
@pytest.mark.asyncio
async def test_update_product(session):
    product = ProductDB(
        id="789",
        name="Old Name",
        price="150.00",
        brand="Old Brand",
        number="OLD789",
        product_details={},
        shipping_returns={},
        images=[],
        variations_data_json={},
    )
    await create_product(product)

    update_data = {"name": "New Name", "brand": "New Brand"}
    result = await update_product("789", update_data)

    assert result is True

    updated_product = await get_product("789")
    assert updated_product is not None
    assert updated_product.name == "New Name"
    assert updated_product.brand == "New Brand"


# 📌 Тест: Видалення продукту
@pytest.mark.asyncio
async def test_delete_product(session):
    product = ProductDB(
        id="999",
        name="To Be Deleted",
        price="50.00",
        brand="Unknown",
        number="DEL999",
        product_details={},
        shipping_returns={},
        images=[],
        variations_data_json={},
    )
    await create_product(product)

    result = await delete_product("999")
    assert result is True

    deleted_product = await get_product("999")
    assert deleted_product is None


# 📌 Тест: Видалення неіснуючого продукту
@pytest.mark.asyncio
async def test_delete_nonexistent_product():
    result = await delete_product("000")
    assert result == "Product not found"


# 📌 Тест: Оновлення неіснуючого продукту
@pytest.mark.asyncio
async def test_update_nonexistent_product():
    update_data = {"name": "New Name"}
    result = await update_product("000", update_data)
    assert result == "Product not found"


# 📌 Тест: Отримання неіснуючого продукту
@pytest.mark.asyncio
async def test_get_nonexistent_product():
    product = await get_product("000")
    assert product is None
