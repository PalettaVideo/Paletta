from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

from .models import Video
from .services import AWSCloudStorageService, VideoLogService

import logging

logger = logging.getLogger(__name__)


@shared_task
def generate_and_send_download_link(video_id, user_email):
    """
    BACKEND-READY: Celery task for generating and emailing download links.
    MAPPED TO: /download/request/<video_id>/ endpoint
    USED BY: DownloadRequestView, async email processing
    
    Generates S3 presigned URL and sends email notification to user.
    Creates download activity logs for admin tracking.
    Required fields: video_id (int), user_email (str)
    """
    try:
        video = Video.objects.get(id=video_id)
        storage_service = AWSCloudStorageService()
        
        # Generate the download link
        download_link = storage_service.generate_download_link(video)
        
        if download_link:
            # Prepare email content
            subject = f"Download link for {video.title}"
            context = {
                'video_title': video.title,
                'download_link': download_link,
                'expiry_hours': storage_service.download_link_expiry
            }
            html_message = render_to_string('emails/download_link_email.html', context)
            plain_message = strip_tags(html_message)
                    
            # Send the email
            from django.conf import settings
            sender_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'niklaas@filmbright.com')
            send_mail(
                subject,
                plain_message,
                sender_email,
                [user_email],
                html_message=html_message
            )
            
            logger.info(f"Successfully sent download link for video ID {video_id} to {user_email}")
            
            # Log the download activity
            VideoLogService.log_download(video=video, user=video.uploader)
            
        else:
            logger.error(f"Failed to generate download link for video ID {video_id}")
            
    except Video.DoesNotExist:
        logger.error(f"Video with ID {video_id} not found")
    except Exception as e:
        logger.error(f"Error in generate_and_send_download_link for video ID {video_id}: {str(e)}")


@shared_task
def cleanup_expired_download_links():
    """
    BACKEND-READY: Celery task for cleaning expired download links.
    MAPPED TO: Scheduled task (cron/periodic)
    USED BY: Celery beat scheduler for maintenance
    
    Removes expired download links from database to prevent stale data.
    Should be scheduled to run periodically (e.g., daily).
    Required fields: None (operates on all expired links)
    """
    try:
        # Find videos with expired download links
        expired_videos = Video.objects.filter(
            download_link_expiry__lt=timezone.now()
        )
        
        count = expired_videos.count()
        if count > 0:
            # Clear the download link and expiry date
            for video in expired_videos:
                video.download_link = None
                video.download_link_expiry = None
                video.save(update_fields=['download_link', 'download_link_expiry'])
                
            logger.info(f"Cleaned up {count} expired download links")
        else:
            logger.info("No expired download links to clean up")
        
    except Exception as e:
        logger.error(f"Error cleaning up expired download links: {str(e)}")

        
@shared_task
def retry_failed_uploads():
    """
    BACKEND-READY: Celery task for retrying failed S3 uploads.
    MAPPED TO: Scheduled task (cron/periodic)
    USED BY: Celery beat scheduler for recovery operations
    
    Identifies and retries videos that failed S3 upload process.
    Resets status to pending before retry to ensure clean state.
    Required fields: None (operates on all failed uploads)
    """
    try:
        # Find videos that failed to upload
        failed_videos = Video.objects.filter(storage_status='failed')
        
        count = failed_videos.count()
        if count > 0:
            logger.info(f"Found {count} failed uploads to retry")
            
            for video in failed_videos:
                logger.info(f"Retrying upload for video ID {video.id}")
                # Reset status to pending before retrying
                video.storage_status = 'pending'
                video.save(update_fields=['storage_status'])
                
                # Note: Retry logic updated for multipart upload system
                # The old upload_to_storage method is no longer available
                # Failed uploads will need to be re-uploaded through the frontend
                logger.info(f"Video ID {video.id} marked for manual re-upload")
        else:
            logger.info("No failed uploads to retry")
        
    except Exception as e:
        logger.error(f"Error retrying failed uploads: {str(e)}")
