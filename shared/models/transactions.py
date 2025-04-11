"""Transactions model"""

from pydantic import BaseModel


class Transactions(BaseModel):
    """
    Transactions model
    """
    order_id: int
    user_id: int
    period: int
    message_id: int
    created_at: float
