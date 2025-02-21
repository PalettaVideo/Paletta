# this file serves as the main entry point for video-related functionality
from .video.routes import video_router

# re-export the router
__all__ = ["video_router"] 