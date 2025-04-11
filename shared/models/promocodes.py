"""Promo codes model"""
from typing import Optional

from pydantic import BaseModel


class PromoCodes(BaseModel):
    """
    PromoCodes model
    """
    promo_code: str
    usages: Optional[int] = None
    period: Optional[int] = None
