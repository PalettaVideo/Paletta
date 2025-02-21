from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session

from ...database import get_db
from ...models import Video, Category, Tag, Upload, User
from ...dependencies import get_current_user
from ..schemas import VideoCreate, VideoResponse

router = APIRouter()

@router.post("/categories/{category_id}/videos/", response_model=VideoResponse)
async def create_video(
    category_id: int,
    video_data: VideoCreate,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify category exists
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Verify user has permission to upload
    if current_user.role == "customer":
        raise HTTPException(
            status_code=403,
            detail="Only contributors and admins can upload videos"
        )

    # Validate file type
    if not file.filename.endswith('.mp4'):
        raise HTTPException(
            status_code=400,
            detail="Only MP4 files are allowed"
        )

    try:
        # Create video entry
        db_video = Video(
            title=video_data.title,
            description=video_data.description,
            category_id=category_id,
            uploader_id=current_user.id
        )
        db.add(db_video)
        db.commit()
        db.refresh(db_video)

        # Create upload entry
        upload = Upload(
            video_id=db_video.id,
            uploader_id=current_user.id,
            status="pending"
        )
        db.add(upload)

        # Handle tags
        if video_data.tags:
            for tag_name in video_data.tags:
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.add(tag)
                db_video.tags.append(tag)

        # Save file
        file_location = f"temp/videos/{db_video.id}_{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())

        # Update status
        upload.status = "processing"
        db.commit()

        return db_video

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while uploading the video: {str(e)}"
        ) 