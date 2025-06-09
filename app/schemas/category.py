from typing import List

from pydantic import BaseModel


class CategoryRequest(BaseModel):
    id: int
    categories: List[str]
    priority: int
    callback_url: str
