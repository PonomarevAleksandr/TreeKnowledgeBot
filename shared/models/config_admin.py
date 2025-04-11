"""Admin config in bot"""
from typing import Optional

from pydantic import BaseModel


class ConfigAdmin(BaseModel):
    """
    ConfigAdmin model
    """
    id: int = 1
    one_month: Optional[float] = 1.00
    three_month: Optional[float] = 1.00
    half_year: Optional[float] = 1.00
    year: Optional[float] = 1.00
