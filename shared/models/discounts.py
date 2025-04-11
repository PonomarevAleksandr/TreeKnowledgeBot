"""Discounts model"""
from typing import Optional

from pydantic import BaseModel


class Discounts(BaseModel):
    """
    PromoCodes model
    """
    promo_code: str
    created_at: Optional[float] = 0.0
    discount_amount: Optional[int] = 0
    period: Optional[int] = None
    to_period: Optional[int] = None
    price: Optional[float] = None
