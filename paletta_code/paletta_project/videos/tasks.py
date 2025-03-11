# TODO: on deployment to AWS cloud, the email functionality will be handled some AWS service.

import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Video
from .services import AWSCloudStorageService, VideoLogService

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=300)  # 5 minutes retry delay
def upload_video_to_storage(self, video_id):
    """
    Task to upload a video to AWS S3 storage.
    
    Args:
        video_id: The ID of the Video model instance
    """
    try:
        video = Video.objects.get(id=video_id)
        storage_service = AWSCloudStorageService()
        
        # Log the processing start
        VideoLogService.log_processing(
            video=video,
            user=video.uploader,
            message=f"Started uploading video '{video.title}' to AWS S3 storage"
        )
        
        success = storage_service.upload_to_storage(video)
        
        if success:
            logger.info(f"Successfully uploaded video ID {video_id} to AWS S3 storage")
            
            # Log the successful storage
            VideoLogService.log_storage(
                video=video,
                user=video.uploader,
                message=f"Successfully stored video '{video.title}' in AWS S3 storage"
            )
            
            # Notify the uploader
            # TODO: change this to a simple log system accessible by the contributor, admin and owner roles --- no need to send emails. Keep the email functionality for now.
            # TODO: add a log system for the admin to view the upload history and status of the video.
            # TODO: notify the contributor via a popup on the upload page.
            if getattr(settings, 'SEND_UPLOAD_CONFIRMATION_EMAIL', True) and video.uploader.email:
                try:
                    # Create HTML email
                    html_message = render_to_string('emails/upload_success.html', {
                        'video': video,
                        'user': video.uploader,
                    })
                    plain_message = strip_tags(html_message)
                    
                    send_mail(
                        subject=f"Your video '{video.title}' has been stored successfully",
                        message=plain_message,
                        html_message=html_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[video.uploader.email],
                        fail_silently=True,
                    )
                    logger.info(f"Sent upload confirmation email for video ID {video_id}")
                except Exception as e:
                    logger.error(f"Failed to send upload confirmation email for video ID {video_id}: {str(e)}")
        else:
            logger.error(f"Failed to upload video ID {video_id} to AWS S3 storage")
            
            # Log the error
            VideoLogService.log_error(
                video=video,
                user=video.uploader,
                error_message=f"Failed to upload video to AWS S3 storage"
            )
            
            # Retry the task if it failed
            raise self.retry(exc=Exception(f"Upload failed for video ID {video_id}"))
            
    except Video.DoesNotExist:
        logger.error(f"Video with ID {video_id} does not exist")
    except self.MaxRetriesExceededError:
        logger.error(f"Max retries exceeded for uploading video ID {video_id}")
        # Update video status to failed after max retries
        try:
            video = Video.objects.get(id=video_id)
            old_status = video.storage_status
            video.storage_status = 'failed'
            video.save(update_fields=['storage_status'])
            
            # Log the status change
            VideoLogService.log_status_change(
                video=video,
                user=video.uploader,
                old_status=old_status,
                new_status='failed'
            )
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error in upload_video_to_storage task for video ID {video_id}: {str(e)}")
        
        try:
            video = Video.objects.get(id=video_id)
            # Log the error
            VideoLogService.log_error(
                video=video,
                user=video.uploader,
                error_message=f"Error uploading to AWS S3: {str(e)}"
            )
        except Exception:
            pass
            
        # Retry the task
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)  # 1 minute retry delay
def generate_and_send_download_link(self, video_id, recipient_email):
    """
    Task to generate a download link and send it to the user.
    
    Args:
        video_id: The ID of the Video model instance
        recipient_email: Email address to send the download link to
    """
    try:
        video = Video.objects.get(id=video_id)
        storage_service = AWSCloudStorageService()
        
        # Generate a download link
        download_url = storage_service.generate_download_link(video)
        
        if download_url:
            try:
                # Create HTML email
                html_message = render_to_string('emails/download_link.html', {
                    'video': video,
                    'download_url': download_url,
                    'expiry_hours': storage_service.download_link_expiry,
                })
                plain_message = strip_tags(html_message)
                
                # Send the download link via email
                send_mail(
                    subject=f"Download link for '{video.title}'",
                    message=plain_message,
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient_email],
                    fail_silently=False,
                )
                
                logger.info(f"Download link for video ID {video_id} sent to {recipient_email}")
                return True
            except Exception as e:
                logger.error(f"Failed to send email with download link for video ID {video_id}: {str(e)}")
                raise self.retry(exc=e)
        else:
            logger.error(f"Failed to generate download link for video ID {video_id}")
            raise self.retry(exc=Exception("Failed to generate download link"))
            
    except Video.DoesNotExist:
        logger.error(f"Video with ID {video_id} does not exist")
        return False
    except self.MaxRetriesExceededError:
        logger.error(f"Max retries exceeded for generating download link for video ID {video_id}")
        return False
    except Exception as e:
        logger.error(f"Error in generate_and_send_download_link task for video ID {video_id}: {str(e)}")
        raise self.retry(exc=e)

@shared_task
def cleanup_expired_download_links():
    """
    Task to clean up expired download links.
    This should be scheduled to run periodically.
    """
    from django.utils import timezone
    
    try:
        # Find videos with expired download links
        expired_videos = Video.objects.filter(
            download_link_expiry__lt=timezone.now(),
            download_link__isnull=False
        )
        
        # Clear the download links
        count = expired_videos.count()
        if count > 0:
            expired_videos.update(download_link=None, download_link_expiry=None)
            logger.info(f"Cleaned up {count} expired download links")
        
    except Exception as e:
        logger.error(f"Error in cleanup_expired_download_links task: {str(e)}")
        
@shared_task
def retry_failed_uploads():
    """
    Task to retry failed uploads.
    This should be scheduled to run periodically.
    """
    try:
        # Find videos with failed uploads
        failed_videos = Video.objects.filter(storage_status='failed')
        
        count = 0
        for video in failed_videos:
            # Queue the video for upload again
            upload_video_to_storage.delay(video.id)
            count += 1
        
        if count > 0:
            logger.info(f"Queued {count} failed videos for upload retry")
        
    except Exception as e:
        logger.error(f"Error in retry_failed_uploads task: {str(e)}") 