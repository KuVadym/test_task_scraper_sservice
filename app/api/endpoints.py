from fastapi import APIRouter, BackgroundTasks, HTTPException
from loguru import logger

from app.celery.parser_tasks import send_category_to_parser
from app.schemas.category import CategoryRequest
from shared.celery_app import celery_app

router = APIRouter(prefix="/process")


@router.post("/process-categories")
async def process_categories(request: CategoryRequest, background_tasks: BackgroundTasks):
    """
    Обробка категорій з відправкою через Celery
    """
    try:
        logger.info(f"Received {len(request.categories)} categories for processing")

        # Відправляємо кожну категорію окремою Celery задачею
        for category in request.categories:
            background_tasks.add_task(
                send_category_to_parser,
                category=category,
                priority=request.priority,
                callback_url=request.callback_url,
            )

        return {
            "status": "queued",
            "message": f"{len(request.categories)} categories sent for processing",
            "task_ids": [str(celery_app.current_task.request.id) if celery_app.current_task else "background"],
        }

    except Exception as e:
        logger.error(f"Error processing categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))
