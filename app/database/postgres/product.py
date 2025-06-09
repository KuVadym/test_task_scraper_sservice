from typing import Dict, Optional, Union

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from app.database.postgres import get_postgres
from app.models.product import ProductDB


async def get_product(product_id: str) -> Optional[ProductDB]:
    """Отримання продукту за ID."""
    try:
        async with get_postgres() as client:
            product = await client.get(ProductDB, product_id)
            if product:
                return product
            logger.warning(f"Product {product_id} not found.")
            return None
    except SQLAlchemyError as e:
        logger.error(f"Error fetching product {product_id}: {e}")
        return None


async def create_product(product: ProductDB) -> bool:
    """Створення нового продукту."""
    try:
        async with get_postgres() as client:
            client.add(product)
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error creating product: {e}")
        return False


async def update_product(product_id: str, updated_data: Dict) -> Union[bool, str]:
    """Оновлення даних продукту."""
    try:
        async with get_postgres() as client:
            product = await client.get(ProductDB, product_id)
            if not product:
                logger.warning(f"Product {product_id} not found for update.")
                return "Product not found"

            for key, value in updated_data.items():
                setattr(product, key, value)
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error updating product {product_id}: {e}")
        return False


async def delete_product(product_id: str) -> Union[bool, str]:
    """Видалення продукту за ID."""
    try:
        async with get_postgres() as client:
            product = await client.get(ProductDB, product_id)
            if not product:
                logger.warning(f"Product {product_id} not found for deletion.")
                return "Product not found"

            await client.delete(product)
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error deleting product {product_id}: {e}")
        return False
