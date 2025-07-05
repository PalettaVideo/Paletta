from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from ..models import Video
from ..tasks import generate_and_send_download_link
from ..services import VideoLogService
import logging
from django.urls import reverse

logger = logging.getLogger(__name__)

class DownloadRequestView(View):
    """
    FRONTEND VIEW: Video download request form and processing.
    MAPPED TO: /download/request/<video_id>/
    TEMPLATE: download_request.html
    
    Provides a form for users to enter their email and request a download link.
    All authenticated users can request downloads for non-private videos.
    Private videos can only be downloaded by library owners.
    Videos must have storage_status='stored' to be downloadable.
    
    GET: Shows download request form
    POST: Processes form and queues download link generation
    """
    
    @method_decorator(login_required)
    def get(self, request, video_id):
        """
        GET HANDLER: Display download request form for stored videos.
        
        Authorization:
        - All authenticated users can download non-private videos
        - Private videos: Only library owners can download
        - Video must have storage_status='stored'
        
        Args:
            request (HttpRequest): HTTP request object
            video_id (int): Video ID from URL parameter
            
        Returns:
            HttpResponse: Rendered download form or redirect with error
        """
        try:
            video = get_object_or_404(Video, id=video_id)
            
            # Check if this is a private video and user has permission
            if video.is_private:
                if video.library.owner != request.user:
                    messages.error(request, "You are not authorized to download this private video.")
                    return redirect(reverse('video_detail', args=[video_id]))
            
            # Check if the video is stored in AWS S3 storage
            if video.storage_status != 'stored':
                messages.warning(request, "This video is not available for download yet.")
                return redirect('upload_history')
            
            return render(request, 'download_request.html', {
                'video': video
            })
            
        except Exception as e:
            logger.error(f"Error in RequestDownloadView.get: {str(e)}")
            messages.error(request, "An error occurred while processing your request.")
            return redirect('upload_history')
    
    @method_decorator(login_required)
    def post(self, request, video_id):
        """
        POST HANDLER: Process download request and queue link generation.
        
        Form processing:
        1. Validates user authorization (authenticated + private video check)
        2. Checks video storage status (must be 'stored')
        3. Gets email from form or uses user's default email
        4. Queues background task to generate download link
        5. Logs the download request activity
        
        Args:
            request (HttpRequest): HTTP request with form data
            video_id (int): Video ID from URL parameter
            
        Returns:
            HttpResponse: Redirect to upload history with success/error message
        """
        try:
            video = get_object_or_404(Video, id=video_id)
            
            # Check if this is a private video and user has permission
            if video.is_private:
                if video.library.owner != request.user:
                    messages.error(request, "You are not authorized to download this private video.")
                    return redirect(reverse('video_detail', args=[video_id]))
            
            # Check if the video is stored in AWS S3 storage
            if video.storage_status != 'stored':
                messages.warning(request, "This video is not available for download yet.")
                return redirect('upload_history')
            
            # Get the email address from the form or use the user's email
            email = request.POST.get('email', request.user.email)
            if not email:
                messages.error(request, "Please provide an email address to receive the download link.")
                return render(request, 'download_request.html', {'video': video})
            
            # Queue task to generate and send download link
            generate_and_send_download_link.delay(video.id, email)
            
            # Log the download request
            VideoLogService.log_download(video, request.user, request)
            
            messages.success(
                request, 
                f"Download link will be sent to {email} shortly. "
                f"Please check your email."
            )
            
            # Log the download request
            logger.info(f"User {request.user.username} requested download link for video ID {video_id} to {email}")
            
            return redirect('upload_history')
            
        except Exception as e:
            logger.error(f"Error in RequestDownloadView.post: {str(e)}")
            messages.error(request, "An error occurred while processing your request.")
            return redirect('upload_history') 