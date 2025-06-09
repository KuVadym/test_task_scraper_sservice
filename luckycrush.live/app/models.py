from pydantic import BaseModel
from typing import Optional


class UserActivity(BaseModel):
    id: str
    username: str
    first_activity: Optional[str] = None
    last_activity: Optional[str] = None
    time_online: int = 0

class ApiResponse(BaseModel):
    status: str
    message: str
    processed: int = 0
    success: int = 0
    errors: list = []