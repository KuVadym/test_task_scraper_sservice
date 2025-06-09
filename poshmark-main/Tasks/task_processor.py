import requests
import json
from typing import Dict, Callable, Any, Optional
from poshmark.logger import Loger


class TaskProcessor:
    """
    Класс TaskProcessor отвечает за взаимодействие с API, получение задач из пула, определение
    типа задачи на основе события и выполнение соответствующих действий.
    Основной функционал включает получение задачи, выполнение и отправку результата обратно в API.

    Данный класс легко расширяется, позволяя добавлять новые типы событий и их обработку.
    Логирование происходит через переданный логгер.

    Атрибуты:
    ----------
    base_url: str
        URL для взаимодействия с API.
    headers: dict
        Заголовки, необходимые для авторизации при запросах к API.
    logger: logging.Logger
        Экземпляр логгера для записи событий и ошибок.
    event_map: dict
        Словарь, где ключом является событие, а значением - соответствующая функция.
    """

    def __init__(self, base_url: str, auth_token: str, logger):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        self.logger = logger

    def __validate_event_map(self):
        """
        Проверяет, инициализирована ли карта событий.
        Вызывает ошибку, если карта событий не инициализирована.
        """
        if self.event_map is None:
            self.logger.critical("Event map is not initialized. Please initialize event_map in the derived class.")
            raise ValueError("Event map is not initialized. Please initialize event_map in the derived class.")

    def get_task(self, event: str = None, platform: str = None) -> Dict[str, Any]:
        """
        Получает задачу из API с фильтрацией по событию.

        Аргументы:
        ----------
        event : str
            Тип события для фильтрации задачи.

        Возвращает:
        ----------
        Dict[str, Any]
            JSON с информацией о задаче.
        """
        self.__validate_event_map()
        try:
            url = f"{self.base_url}/tasks/get"
            payload = {}
            if platform is not None:
                payload["platform"] = platform
            if event is not None:
                payload["event"] = event
            response = requests.post(url, headers=self.headers, data=json.dumps(payload))
            response.raise_for_status()  # Поднимет исключение в случае неудачи
            task = response.json()
            self.logger.info(f"Task received successfully: {task}")
            return task
        except requests.RequestException as e:
            self.logger.error(f"Error receiving task: {e}")
            return {}

    def process_task(self, task: Dict[str, Any]):
        """
        Обрабатывает задачу, вызывает соответствующий метод для выполнения задачи на основе события.

        Аргументы:
        ----------
        task : dict
            JSON с данными задачи.
        """

        event = task.get("event")
        if event and event in self.event_map:
            try:
                data = self.event_map[event](task)
            except Exception as e:
                self.logger.error(f"Task completion error {event}: {e}")
                self.complete_task(task["id"], f"Error: {str(e)}")
            else:
                self.complete_task(task["id"], data)
        else:
            self.logger.error(f"Unknown event: {event}")

    def complete_task(self, task_id: str, result_message: str):
        """
        Завершает задачу и отправляет результат обратно в API.

        Аргументы:
        ----------
        task_id : str
            Уникальный идентификатор задачи.
        result_message : str
            Сообщение с результатом выполнения задачи.
        success : bool
            Флаг, указывающий, успешное ли выполнение задачи.
        """
        try:
            url = f"{self.base_url}/tasks/complete/{task_id}"
            payload = {"result_message": result_message}
            response = requests.post(url, headers=self.headers, data=json.dumps(payload))
            response.raise_for_status()
            self.logger.info(f"Task {task_id} successfully completed.")
        except requests.RequestException as e:
            self.logger.error(f"Task completion error {task_id}: {e}")
