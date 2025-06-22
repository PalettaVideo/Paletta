from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import HttpResponseForbidden
from ..models import Video
from ..tasks import generate_and_send_download_link
from ..services import VideoLogService, AWSCloudStorageService
import logging
from django.urls import reverse

logger = logging.getLogger(__name__)

class DownloadRequestView(View):
    """
    View for requesting a download link for a video.
    Provides a form for users to enter their email address and request a download link.
    """
    
    @method_decorator(login_required)
    def get(self, request, video_id):
        """
        Handle GET request to show download request form.
        
        Args:
            request: The HTTP request
            video_id: The ID of the video to download
            
        Returns:
            HttpResponse: The rendered download request form
        """
        try:
            video = get_object_or_404(Video, id=video_id)
            
            # Authorization check: only the uploader or staff can access non-published videos
            if video.uploader != request.user and not request.user.is_staff:
                messages.error(request, "You are not authorized to view this video.")
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
        Handle POST request to generate and send download link.
        
        Args:
            request: The HTTP request
            video_id: The ID of the video to download
            
        Returns:
            HttpResponse: Redirect to upload history page with status message
        """
        try:
            video = get_object_or_404(Video, id=video_id)
            
            # Authorization check: only the uploader or staff can access non-published videos
            if video.uploader != request.user and not request.user.is_staff:
                messages.error(request, "You are not authorized to download this video.")
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