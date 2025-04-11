"""Category database model"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ContentItem(BaseModel):
    """
    Content in the category
    """
    type: Optional[str] = None
    file_id: List[str] = Field(default_factory=list)

class CategoryModel(BaseModel):
    """
    Category model
    """
    id: Optional[str] = None
    name: Optional[str] = "Название"
    type: Optional[str] = None
    photos: List[ContentItem] = Field(default_factory=list)
    videos: List[ContentItem] = Field(default_factory=list)
    audios: List[ContentItem] = Field(default_factory=list)
    documents: List[ContentItem] = Field(default_factory=list)
    voices: List[ContentItem] = Field(default_factory=list)
    video_notes: List[ContentItem] = Field(default_factory=list)
    messages: List[ContentItem] = Field(default_factory=list)
    parent_id: Optional[str] = None
    caption: Optional[str] = None
    created_at: float = 0.0
    updated_at: float = 0.0
