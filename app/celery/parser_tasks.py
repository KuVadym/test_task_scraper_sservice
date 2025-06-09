from loguru import logger

from app.celery.publisher_tasks import send_to_publisher
from app.celery.shared_tasks import notify_external_service
from app.database.postgres.product import save_parsing_result
from shared.celery_app import celery_app


def send_category_to_parser(category: str, priority: int, callback_url: str = None):
    """
    Допоміжна функція для відправки категорії через Celery
    """
    try:
        # Відправляємо задачу в чергу парсингу
        task = celery_app.send_task(
            "parser.parse_category",
            args=[category],
            kwargs={"callback_url": callback_url},
            queue="parsing_queue",
            priority=priority,
        )
        logger.info(f"Sent category '{category}' to Celery (task_id: {task.id})")
        return task.id
    except Exception as e:
        logger.error(f"Failed to send category '{category}': {e}")
        raise


async def handle_parser_callback(task_id: str, result: dict):
    """
    Обробляє результати парсингу після завершення задачі

    Args:
        task_id: ID завершеної задачі
        result: Результати парсингу
    """
    try:
        logger.info(f"Handling parser callback for task {task_id}")

        # 1. Зберігаємо результати в БД
        saved_data = await save_parsing_result(result)

        # 2. Відправляємо на публікацію
        publish_task_id = await send_to_publisher(
            result_data=saved_data, priority=5, callback_url=result.get("callback_url")
        )

        logger.success(f"Parser results processed. Publish task: {publish_task_id}")

        # 3. Якщо є callback_url - повідомляємо зовнішній сервіс
        if result.get("callback_url"):
            await notify_external_service(
                url=result["callback_url"],
                data={
                    "status": "published",
                    "parser_task_id": task_id,
                    "publish_task_id": publish_task_id,
                },
            )

    except Exception as e:
        logger.error(f"Failed to handle parser callback: {e}")
        raise
