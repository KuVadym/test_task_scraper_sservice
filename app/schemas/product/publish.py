from typing import List

from pydantic import BaseModel, HttpUrl


class SizeInfo(BaseModel):
    name: str
    id: str
    available: bool
    stock_status: str
    shipping_info: str


class PublishProduct(BaseModel):
    images: List[HttpUrl]
    name: str
    description: str
    category: str
    sizes: List[SizeInfo]
    price: int


class PublishRequest(BaseModel):
    data: List[PublishProduct]
