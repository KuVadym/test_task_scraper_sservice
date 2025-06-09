from datetime import datetime
from typing import Dict

from pydantic import BaseModel


class CurrencyData(BaseModel):
    code: str
    value: float


class ExchangeRates(BaseModel):
    meta: Dict[str, datetime]
    data: Dict[str, CurrencyData]
