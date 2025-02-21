from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database import get_db
from ...models import Video, Category, User
from ...dependencies import get_current_user
from ..schemas import VideoBase, VideoResponse

router = APIRouter()

@router.put("/categories/{category_id}/videos/{video_id}", response_model=VideoResponse)
async def update_video(
    category_id: int,
    video_id: int,
    video_data: VideoBase,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.category_id == category_id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found in this category")
    
    if video.uploader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this video")
    
    # Ensure the new category exists if it's being changed
    if video_data.category_id != category_id:
        if not db.query(Category).filter(Category.id == video_data.category_id).first():
            raise HTTPException(status_code=404, detail="New category not found")
    
    for key, value in video_data.dict(exclude_unset=True).items():
        setattr(video, key, value)
    
    db.commit()
    db.refresh(video)
    return video 