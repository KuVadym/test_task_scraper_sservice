from pydantic import BaseModel
from typing import Dict, List, Union

class UserCreateRequest(BaseModel):
    store_url: str
    username: str
    proxy: str
    cookies: List[Dict[str, str]]

class UserResponse(BaseModel):
    id: int
    proxy: str
    cookies: Union[Dict, List]

class User(BaseModel):
    id: int
    username: str
    proxy: str
    cookies: Union[Dict, List]
