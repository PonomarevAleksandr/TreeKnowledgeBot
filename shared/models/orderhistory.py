"""History of order ids,
 because Robokassa API let create only unique invoices
 (and after pay too)"""
from typing import Union

from pydantic import BaseModel


class OrderHistory(BaseModel):
    """
    OrderHistory model
    """
    order_id: Union[int, None] = None
    created_at: float
