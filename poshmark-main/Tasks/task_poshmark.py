from typing import Dict, Any
from Tasks.task_processor import TaskProcessor


class TaskPoshmark(TaskProcessor):

    def __init__(self, base_url: str, auth_token: str, logger):
        super().__init__(base_url, auth_token, logger)
        self.event_map = {
            "LISTING": self.listing,
        }

    def listing(self, task_data: Dict[str, Any]):
        try:
            print(task_data.get('event'))
            print(task_data.get('data'))
            return "Task completion OK"
        except Exception as e:
            self.logger.error(f"Task completion error {task_data.get('id')}: {e}")
