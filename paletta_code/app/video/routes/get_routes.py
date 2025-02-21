from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...database import get_db
from ...models import Video, Category, Tag
from ..schemas import CategoryResponse, VideoResponse

router = APIRouter()

@router.get("/categories/", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@router.get("/categories/{category_id}/videos", response_model=List[VideoResponse])
async def get_videos_by_category(
    category_id: int,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(Video).filter(Video.category_id == category_id)
    
    if tag:
        query = query.join(Video.tags).filter(Tag.name == tag)
    
    if search:
        query = query.filter(Video.title.ilike(f"%{search}%"))
    
    total_count = query.count()
    videos = query.offset(skip).limit(limit).all()
    
    if not videos and not skip:
        raise HTTPException(status_code=404, detail="No videos found in this category")
    
    return videos

@router.get("/categories/{category_id}/videos/{video_id}", response_model=VideoResponse)
async def get_video(
    category_id: int,
    video_id: int,
    db: Session = Depends(get_db)
):
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.category_id == category_id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found in this category")
    return video 