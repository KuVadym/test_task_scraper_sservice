from shared.celery_app import celery_app


async def send_screenshot_request(url: str, result_id: str) -> str:
    """Відправляє запит на створення скріншоту"""
    task = celery_app.send_task("publisher.capture_screenshot", args=[url, result_id], queue="screenshots_queue")
    return task.id


async def notify_external_service(url: str, data: dict):
    """Відправляє дані на зовнішній сервіс"""
    # async with httpx.AsyncClient() as client:
    #     await client.post(url, json=data)
    raise NotImplementedError


async def update_publication_status():
    raise NotImplementedError
