# TODO: on deployment to AWS cloud, the email functionality will be handled some AWS service.

import logging
import os
import subprocess
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import boto3
from botocore.exceptions import ClientError
from celery import shared_task
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import Video
from .services import AWSCloudStorageService, VideoLogService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60 * 5)
def process_video_from_s3(self, video_id):
    """
    Celery task to process a video after it has been uploaded to S3.
    - Fetches video metadata using ffprobe.
    - Generates a thumbnail using ffmpeg.
    - Updates the Video model with the new data.
    """
    try:
        video = Video.objects.get(id=video_id)
    except Video.DoesNotExist:
        logger.error(f"Video with ID {video_id} not found for processing.")
        return

    video.storage_status = 'processing'
    video.save(update_fields=['storage_status'])

    storage_service = AWSCloudStorageService()
    s3_client = storage_service.s3_client
    video_bucket_name = storage_service.bucket_name
    # Thumbnails should go to the public media/static bucket
    thumbnail_bucket_name = settings.AWS_STATIC_BUCKET_NAME

    s3_key = video.storage_reference_id

    with TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        local_video_path = temp_path / Path(s3_key).name
        local_thumbnail_path = temp_path / f"thumb_{Path(s3_key).stem}.jpg"

        try:
            # 1. Download video from S3
            logger.info(f"Downloading s3://{video_bucket_name}/{s3_key} to {local_video_path}")
            s3_client.download_file(video_bucket_name, s3_key, str(local_video_path))

            # 2. Extract metadata with ffprobe
            logger.info(f"Extracting metadata from {local_video_path}")
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(local_video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            metadata = json.loads(result.stdout)

            video_stream = next((s for s in metadata['streams'] if s['codec_type'] == 'video'), None)
            if not video_stream:
                raise ValueError("No video stream found in the file.")

            video.duration = int(float(metadata['format']['duration']))
            video.file_size = int(metadata['format']['size'])
            video.resolution = f"{video_stream['width']}x{video_stream['height']}"
            
            if 'avg_frame_rate' in video_stream and '/' in video_stream['avg_frame_rate']:
                num, den = video_stream['avg_frame_rate'].split('/')
                video.frame_rate = round(int(num) / int(den), 2) if den != '0' else 0.0
            else:
                 video.frame_rate = 0.0


            # 3. Generate thumbnail with ffmpeg (from the middle of the video)
            thumbnail_time = video.duration / 2
            logger.info(f"Generating thumbnail at {thumbnail_time}s for {local_video_path}")
            cmd_thumb = [
                'ffmpeg',
                '-i', str(local_video_path),
                '-ss', str(thumbnail_time),
                '-vframes', '1',
                '-q:v', '2',  # High quality
                str(local_thumbnail_path)
            ]
            subprocess.run(cmd_thumb, check=True, capture_output=True)

            # 4. Upload thumbnail to media S3 bucket
            thumbnail_s3_key = f"thumbnails/video_{video.id}/{local_thumbnail_path.name}"
            logger.info(f"Uploading thumbnail to s3://{thumbnail_bucket_name}/{thumbnail_s3_key}")
            s3_client.upload_file(
                str(local_thumbnail_path),
                thumbnail_bucket_name,
                thumbnail_s3_key,
                ExtraArgs={'ContentType': 'image/jpeg', 'ACL': 'public-read'}
            )
            
            # Use the FileField's name attribute to store the S3 key
            video.thumbnail.name = thumbnail_s3_key

            video.storage_status = 'stored'
            logger.info(f"Successfully processed video {video.id}. Metadata and thumbnail updated.")

        except (subprocess.CalledProcessError, ClientError, ValueError) as e:
            logger.error(f"Error processing video {video_id}: {e}")
            video.storage_status = 'processing_failed'
            # Log the error to the video log
            VideoLogService.log_error(
                video=video,
                user=video.uploader,
                error_message=f"Processing failed: {str(e)}"
            )
            try:
                self.retry(exc=e)
            except self.MaxRetriesExceededError:
                logger.error(f"Max retries exceeded for video {video_id}.")
        finally:
            # Save all changes to the video object
            video.save()


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
            process_video_from_s3.delay(video.id)
            count += 1
        
        if count > 0:
            logger.info(f"Queued {count} failed videos for upload retry")
        
    except Exception as e:
        logger.error(f"Error in retry_failed_uploads task: {str(e)}") 