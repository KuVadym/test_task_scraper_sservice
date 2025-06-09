from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.endpoints import router

# Створюємо тестовий додаток
app = FastAPI()
app.include_router(router)
client = TestClient(app)

# Тестовий приклад категорій
TEST_CATEGORIES = ["electronics", "books", "clothing"]
TEST_CALLBACK_URL = "http://example.com/callback"
TEST_PRIORITY = 1


@pytest.fixture
def mock_celery():
    with patch("shared.celery_app.celery_app") as mock:
        yield mock


@pytest.fixture
def mock_background_tasks():
    with patch("fastapi.BackgroundTasks") as mock:
        mock.return_value.add_task = MagicMock()
        yield mock


def test_process_categories_success(mock_celery, mock_background_tasks):
    # Підготовка тестових даних
    request_data = {"categories": TEST_CATEGORIES, "callback_url": TEST_CALLBACK_URL, "priority": TEST_PRIORITY}

    # Мокуємо current_task
    mock_celery.current_task = MagicMock()
    mock_celery.current_task.request = MagicMock()
    mock_celery.current_task.request.id = "test-task-id"

    # Викликаємо ендпоінт
    response = client.post("/process/process-categories", json=request_data)

    # Перевіряємо результати
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert response.json()["message"] == f"{len(TEST_CATEGORIES)} categories sent for processing"

    # Перевіряємо, що background_tasks.add_task викликано правильно
    assert mock_background_tasks.return_value.add_task.call_count == len(TEST_CATEGORIES)

    # Перевіряємо аргументи для першого виклику (можна перевірити всі, якщо потрібно)
    first_call_args = mock_background_tasks.return_value.add_task.call_args_list[0][1]
    assert first_call_args["category"] == TEST_CATEGORIES[0]
    assert first_call_args["priority"] == TEST_PRIORITY
    assert first_call_args["callback_url"] == TEST_CALLBACK_URL


def test_process_categories_empty_list(mock_celery, mock_background_tasks):
    # Підготовка тестових даних з порожнім списком категорій
    request_data = {"categories": [], "callback_url": TEST_CALLBACK_URL, "priority": TEST_PRIORITY}

    # Викликаємо ендпоінт
    response = client.post("/process/process-categories", json=request_data)

    # Перевіряємо результати
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert response.json()["message"] == "0 categories sent for processing"
    assert mock_background_tasks.return_value.add_task.call_count == 0


def test_process_categories_error_handling(mock_celery, mock_background_tasks):
    # Підготовка тестових даних
    request_data = {"categories": TEST_CATEGORIES, "callback_url": TEST_CALLBACK_URL, "priority": TEST_PRIORITY}

    # Симулюємо помилку при додаванні задачі
    mock_background_tasks.return_value.add_task.side_effect = Exception("Test error")

    # Викликаємо ендпоінт
    response = client.post("/process/process-categories", json=request_data)

    # Перевіряємо, що повертається помилка 500
    assert response.status_code == 500
    assert "Test error" in response.json()["detail"]

    # Перевіряємо, що помилка залогувана
    # (Це може потребувати додаткового мокування logger, якщо потрібно перевірити конкретно)


def test_process_categories_without_callback(mock_celery, mock_background_tasks):
    # Підготовка тестових даних без callback_url
    request_data = {"categories": TEST_CATEGORIES, "priority": TEST_PRIORITY}

    # Викликаємо ендпоінт
    response = client.post("/process/process-categories", json=request_data)

    # Перевіряємо результати
    assert response.status_code == 200
    assert mock_background_tasks.return_value.add_task.call_count == len(TEST_CATEGORIES)

    # Перевіряємо, що callback_url=None передано в задачу
    first_call_args = mock_background_tasks.return_value.add_task.call_args_list[0][1]
    assert first_call_args["callback_url"] is None


def test_process_categories_default_priority(mock_celery, mock_background_tasks):
    # Підготовка тестових даних без пріоритету
    request_data = {"categories": TEST_CATEGORIES, "callback_url": TEST_CALLBACK_URL}

    # Викликаємо ендпоінт
    response = client.post("/process/process-categories", json=request_data)

    # Перевіряємо результати
    assert response.status_code == 200

    # Перевіряємо, що використано default значення для priority (якщо воно є в схемі)
    # Якщо в схемі немає default, цей тест може бути зайвим
    first_call_args = mock_background_tasks.return_value.add_task.call_args_list[0][1]
    assert "priority" in first_call_args
