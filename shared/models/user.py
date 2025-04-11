"""User database model"""
from typing import Union, Optional

from pydantic import BaseModel, Field


class MessageIds(BaseModel):
    """
    Content message id
    """
    message_id: Union[int, None] = None


class User(BaseModel):
    """
    User model
    """
    id: int
    role: str = 'user'
    personal_month: Optional[int] = None
    personal_three_month: Optional[int] = None
    personal_half_year: Optional[int] = None
    personal_year: Optional[int] = None
    is_bot: bool
    message_ids: Optional[list] = Field(default_factory=list)
    refer_id: Union[int, None] = None
    subscribed: bool = False
    subscribed_date: Union[float, None] = None
    subscribed_period: Union[int, None] = None
    first_name: str
    last_name: Union[str, None] = None
    username: Union[str, None] = None
    language_code: Union[str, None] = None
    is_premium: Union[bool, None] = None
    added_to_attachment_menu: Union[bool, None] = None
    can_join_groups: Union[bool, None] = None
    can_read_all_group_messages: Union[bool, None] = None
    supports_inline_queries: Union[bool, None] = None
    created_at: int = 0
    updated_at: int = 0
    blocked_at: Union[int, None] = None
