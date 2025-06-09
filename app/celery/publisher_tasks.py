from loguru import logger

from app.celery.shared_tasks import (
    update_publication_status,
)
from app.schemas.product.parse import ProductsResponse
from app.schemas.product.publish import PublishProduct, PublishRequest, SizeInfo
from app.utils.currency import get_currency_coefficient
from shared.celery_app import celery_app


async def send_to_publisher(result_data: ProductsResponse, priority: int = 1, callback_url: str = None) -> str:
    """
    Відправляє результати парсингу на публікацію з валідацією через Pydantic модель

    Args:
        result_data: Дані для публікації (результати парсингу) ProductsResponse
        priority: Пріоритет завдання (1-10)
        callback_url: URL для колбеку після публікації

    Returns:
        ID завдання Celery

    Raises:
        ValueError: Якщо дані не відповідають моделі PublishProduct
    """
    try:
        # Валідація та перетворення даних
        currency_coef = await get_currency_coefficient()
        validated_products: list[PublishProduct] = []
        metadata = result_data.metadata
        for product_url, product in result_data.products.items():
            validated_product = PublishProduct(
                images=product.images,
                name=product.name,
                description=product.product_details.description_full_text_html,
                category=metadata.source_category_name,
                sizes=[
                    SizeInfo(
                        size=size.name,
                        id=size.id,
                        stock_status=size.stock_status,
                        available=size.available,
                        shipping_info=size.shipping_info,
                    )
                    for size in product.variations.sizes
                ],
                price=int(float(product.price.replace("£", "")) * currency_coef),
            )
            validated_products.append(validated_product)

        # Відправка завдання Celery з валідованими даними
        task = celery_app.send_task(
            "publisher.publish_result",
            args=[PublishRequest(data=validated_products).model_dump(mode="json")],
            kwargs={"callback_url": callback_url},
            queue="publishing_queue",
            priority=priority,
        )

        logger.info(f"Sent validated data to publisher (task_id: {task.id})")
        return task.id

    except Exception as e:
        logger.error(f"Validation or publishing failed: {str(e)}")
        raise ValueError(f"Data validation error: {str(e)}")


async def handle_publisher_callback(task_id: str, result: dict):
    """
    Обробляє результати публікації

    Args:
        task_id: ID завершеної задачі
        result: Результати публікації
    """
    try:
        logger.info(f"Handling publisher callback for task {task_id}")

        # 1. Оновлюємо запис в БД
        await update_publication_status(
            # result_id=result["result_id"], published_url=result["published_url"]
        )

        # # 2. Якщо потрібен скріншот
        # if result.get("need_screenshot"):
        #     screenshot_task_id = await send_screenshot_request(
        #         url=result["published_url"], result_id=result["result_id"]
        #     )
        #     logger.info(f"Screenshot task started: {screenshot_task_id}")

        # # 3. Колбек зовнішньому сервісу
        # if result.get("callback_url"):
        #     await notify_external_service(
        #         url=result["callback_url"],
        #         data={
        #             "status": "published",
        #             "task_id": task_id,
        #             "published_url": result["published_url"],
        #         },
        #     )

    except Exception as e:
        logger.error(f"Failed to handle publisher callback: {e}")
        raise
