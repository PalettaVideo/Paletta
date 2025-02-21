from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None = None

    class Config:
        from_attributes = True

class VideoBase(BaseModel):
    title: str
    description: str | None = None
    category_id: int
    tags: List[str] | None = None

class VideoCreate(VideoBase):
    pass

class VideoResponse(VideoBase):
    id: int
    upload_date: datetime
    uploader_id: int
    category: CategoryResponse

    class Config:
        from_attributes = True 