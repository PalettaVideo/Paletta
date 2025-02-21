from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database import get_db
from ...models import Video, User
from ...dependencies import get_current_user

router = APIRouter()

@router.delete("/categories/{category_id}/videos/{video_id}")
async def delete_video(
    category_id: int,
    video_id: int,
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
        raise HTTPException(status_code=403, detail="Not authorized to delete this video")
    
    db.delete(video)
    db.commit()
    return {"message": "Video deleted successfully"} 