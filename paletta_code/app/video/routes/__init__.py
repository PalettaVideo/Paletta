from fastapi import APIRouter
from .get_routes import router as get_router
from .post_routes import router as post_router
from .put_routes import router as put_router
from .delete_routes import router as delete_router

video_router = APIRouter()
video_router.include_router(get_router)
video_router.include_router(post_router)
video_router.include_router(put_router)
video_router.include_router(delete_router) 