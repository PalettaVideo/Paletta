import os
import logging
import boto3
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class AWSCloudStorageService:
    """
    BACKEND-READY: AWS S3 storage service for video file management.
    MAPPED TO: Internal service class
    USED BY: Video upload/download workflows, admin operations
    
    Handles S3 operations: upload, download link generation, streaming URLs, deletion.
    Required config: AWS_STORAGE_ENABLED, AWS credentials, bucket settings
    """
    
    def __init__(self):
        """
        BACKEND-READY: Initialize AWS S3 service with configuration validation.
        MAPPED TO: Service instantiation
        USED BY: All S3 operations throughout the system
        
        Validates AWS credentials and establishes S3 client connection.
        Auto-disables if credentials missing or connection fails.
        """
        # Get configuration from Django settings
        self.storage_enabled = getattr(settings, 'AWS_STORAGE_ENABLED', False)
        
        if self.storage_enabled:
            self.aws_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
            self.aws_secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            self.aws_region = getattr(settings, 'AWS_REGION', 'us-east-1')
            self.bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None) # the video bucket
            self.download_link_expiry = getattr(settings, 'DOWNLOAD_LINK_EXPIRY_HOURS', 24)
            
            # Initialize S3 client if credentials are available
            if self.aws_access_key and self.aws_secret_key and self.bucket_name:
                try:
                    self.s3_client = boto3.client(
                        's3',
                        aws_access_key_id=self.aws_access_key,
                        aws_secret_access_key=self.aws_secret_key,
                        region_name=self.aws_region
                    )
                    # Test connection
                    self.s3_client.list_buckets()
                    logger.info("Successfully connected to AWS S3")
                except Exception as e:
                    self.storage_enabled = False
                    logger.error(f"Failed to connect to AWS S3: {str(e)}")
            else:
                self.storage_enabled = False
                logger.warning("AWS storage is enabled but AWS credentials are missing")
    
    def upload_to_storage(self, video):
        """
        BACKEND-READY: Upload video file to AWS S3 with status tracking.
        MAPPED TO: Internal S3 upload operation
        USED BY: Video upload workflow, retry mechanisms
        
        Uploads video to S3, updates status, logs activities, optionally deletes local file.
        Required fields: video.video_file, video.uploader, video.id
        """
        if not self.storage_enabled:
            logger.warning("AWS S3 storage is not enabled")
            return False
            
        if not video.video_file:
            logger.error(f"No video file to upload for video ID {video.id}")
            old_status = video.storage_status
            video.storage_status = 'failed'
            video.save(update_fields=['storage_status'])
            
            # Log the status change
            from .services import VideoLogService
            VideoLogService.log_status_change(
                video=video,
                user=video.uploader,
                old_status=old_status,
                new_status='failed'
            )
            
            return False
            
        try:
            # Update status to uploading
            old_status = video.storage_status
            video.storage_status = 'uploading'
            video.save(update_fields=['storage_status'])
            
            # Log the status change
            from .services import VideoLogService
            VideoLogService.log_status_change(
                video=video,
                user=video.uploader,
                old_status=old_status,
                new_status='uploading'
            )
            
            # Generate a unique key for the video in S3
            file_name = os.path.basename(video.video_file.name)
            s3_key = f"videos/user_{video.uploader.id}/{video.id}/{file_name}"
            
            # Set appropriate content type based on file extension
            content_type = 'video/' + (video.get_file_extension() or 'mp4')
            
            # Upload the file to S3 with progress monitoring
            with video.video_file.open('rb') as file_data:
                self.s3_client.upload_fileobj(
                    file_data, 
                    self.bucket_name, 
                    s3_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'ACL': 'private'  # Ensure the file is private
                    }
                )
            
            # Update the video record with storage information
            video.storage_url = f"s3://{self.bucket_name}/{s3_key}"
            video.storage_reference_id = s3_key
            old_status = video.storage_status
            video.storage_status = 'stored'
            video.save(update_fields=['storage_url', 'storage_reference_id', 'storage_status'])
            
            # Log the status change
            VideoLogService.log_status_change(
                video=video,
                user=video.uploader,
                old_status=old_status,
                new_status='stored'
            )
            
            # Optionally delete the local file to save space
            if getattr(settings, 'DELETE_LOCAL_FILE_AFTER_UPLOAD', True):
                video.video_file.delete(save=False)
                logger.info(f"Deleted local file for video ID {video.id}")
            
            logger.info(f"Successfully uploaded video ID {video.id} to AWS storage")
            return True
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"AWS S3 error ({error_code}) uploading video ID {video.id}: {str(e)}")
            old_status = video.storage_status
            video.storage_status = 'failed'
            video.save(update_fields=['storage_status'])
            
            # Log the status change and error
            from .services import VideoLogService
            VideoLogService.log_status_change(
                video=video,
                user=video.uploader,
                old_status=old_status,
                new_status='failed'
            )
            VideoLogService.log_error(
                video=video,
                user=video.uploader,
                error_message=f"AWS S3 error ({error_code}): {str(e)}"
            )
            
            return False
        except Exception as e:
            logger.error(f"Error uploading video ID {video.id} to deep storage: {str(e)}")
            old_status = video.storage_status
            video.storage_status = 'failed'
            video.save(update_fields=['storage_status'])
            
            # Log the status change and error
            from .services import VideoLogService
            VideoLogService.log_status_change(
                video=video,
                user=video.uploader,
                old_status=old_status,
                new_status='failed'
            )
            VideoLogService.log_error(
                video=video,
                user=video.uploader,
                error_message=f"Error: {str(e)}"
            )
            
            return False
    
    def generate_download_link(self, video):
        """
        BACKEND-READY: Generate temporary S3 download link with expiry.
        MAPPED TO: Download request functionality
        USED BY: Download views, email notifications
        
        Creates presigned S3 URL for video download (24h default expiry).
        Updates video model with link and expiry timestamp.
        Required fields: video.storage_reference_id, storage_status='stored'
        """
        if not self.storage_enabled:
            logger.warning("Deep storage is not enabled")
            return None
            
        if not video.storage_reference_id or video.storage_status != 'stored':
            logger.error(f"Video ID {video.id} is not properly stored in deep storage")
            return None
            
        try:
            # Generate a presigned URL that expires after the configured time
            expiry = int(self.download_link_expiry * 3600)  # Convert hours to seconds
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': video.storage_reference_id,
                    'ResponseContentDisposition': f'attachment; filename="{os.path.basename(video.storage_reference_id)}"'
                },
                ExpiresIn=expiry
            )
            
            # Update the video with the download link and expiry time
            video.download_link = url
            video.download_link_expiry = timezone.now() + timedelta(hours=self.download_link_expiry)
            video.save(update_fields=['download_link', 'download_link_expiry'])
            
            logger.info(f"Generated download link for video ID {video.id}")
            return url
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"AWS S3 error ({error_code}) generating download link for video ID {video.id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error generating download link for video ID {video.id}: {str(e)}")
            return None
    
    def generate_streaming_url(self, video):
        """
        BACKEND/FRONTEND-READY: Generate temporary S3 streaming URL.
        MAPPED TO: Video playback functionality
        USED BY: Video templates, API responses, serializers
        
        Creates presigned S3 URL for video streaming (1h expiry).
        Used for in-browser video playback without downloads.
        Required fields: video.storage_reference_id, storage_status='stored'
        """
        if not self.storage_enabled:
            logger.warning("Deep storage is not enabled")
            return None
            
        if not video.storage_reference_id or video.storage_status != 'stored':
            logger.error(f"Video ID {video.id} is not properly stored in deep storage")
            return None
            
        try:
            # presigned URL that expires after a shorter time for streaming
            expiry = 3600  # 1 hour in seconds
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': video.storage_reference_id
                },
                ExpiresIn=expiry
            )
            
            return url
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"AWS S3 error ({error_code}) generating streaming URL for video ID {video.id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error generating streaming URL for video ID {video.id}: {str(e)}")
            return None
    
    def delete_from_storage(self, video):
        """
        BACKEND-READY: Delete video and thumbnail from S3 storage.
        MAPPED TO: Video deletion operations
        USED BY: Admin interface, cleanup operations
        
        Removes video from S3, clears storage metadata, resets status to pending.
        Handles both video files and associated thumbnails.
        Required fields: video.storage_reference_id
        """
        if not self.storage_enabled:
            logger.warning("Deep storage is not enabled")
            return False
            
        if not video.storage_reference_id:
            logger.warning(f"Video ID {video.id} has no storage reference ID")
            return False
            
        try:
            # Delete the object from S3
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=video.storage_reference_id
            )
            
            # Also delete the thumbnail if it exists in S3
            if video.thumbnail and hasattr(video, 'thumbnail_s3_key') and video.thumbnail_s3_key:
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=video.thumbnail_s3_key
                )
                logger.info(f"Deleted thumbnail for video ID {video.id} from S3")
            
            # Update the video model
            video.storage_url = None
            video.storage_reference_id = None
            video.storage_status = 'pending'  # Reset to pending
            
            # Clear any download links
            video.download_link = None
            video.download_link_expiry = None
            
            # Save changes
            video.save(update_fields=['storage_url', 'storage_reference_id', 
                                     'storage_status', 'download_link', 'download_link_expiry'])
            
            # Log the deletion from S3
            from .services import VideoLogService
            VideoLogService.log_status_change(
                video=video,
                user=video.uploader if hasattr(video, 'uploader') else None,
                old_status='stored',
                new_status='pending'
            )
            
            logger.info(f"Successfully deleted video ID {video.id} from S3")
            return True
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"AWS S3 error ({error_code}) deleting video ID {video.id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error deleting video ID {video.id} from S3: {str(e)}")
            return False

class VideoLogService:
    """
    BACKEND-READY: Comprehensive video activity logging service.
    MAPPED TO: Internal logging system
    USED BY: All video operations for audit trail
    
    Creates structured logs for uploads, downloads, errors, status changes.
    Captures IP addresses, user agents, and metadata for admin tracking.
    """
    
    @staticmethod
    def log_activity(video, user, log_type, message, request=None, **kwargs):
        """
        BACKEND-READY: Core logging method for all video activities.
        MAPPED TO: Internal logging function
        USED BY: All specific log methods (upload, download, error, etc.)
        
        Creates VideoLog entries with metadata extraction from requests.
        Supports IP tracking and user agent capture for security auditing.
        Required fields: video, user, log_type, message
        """
        from .models import VideoLog
        
        # Create log entry
        log_entry = VideoLog(
            video=video,
            user=user,
            log_type=log_type,
            message=message,
            storage_status=video.storage_status,
            file_size=video.file_size,
            duration=video.duration,
            **{k: v for k, v in kwargs.items() if k in [f.name for f in VideoLog._meta.get_fields()]}
        )
        
        # Extract IP and user agent from request if provided
        if request:
            log_entry.ip_address = VideoLogService.get_client_ip(request)
            log_entry.user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        log_entry.save()
        return log_entry
    
    @staticmethod
    def log_upload(video, user, request=None):
        """Log a video upload activity."""
        return VideoLogService.log_activity(
            video=video,
            user=user,
            log_type='upload',
            message=f"Video '{video.title}' uploaded by {user.username}",
            request=request
        )
    
    @staticmethod
    def log_processing(video, user, message):
        """Log a video processing activity."""
        return VideoLogService.log_activity(
            video=video,
            user=user,
            log_type='process',
            message=message
        )
    
    @staticmethod
    def log_storage(video, user, message):
        """Log a video storage activity."""
        return VideoLogService.log_activity(
            video=video,
            user=user,
            log_type='store',
            message=message
        )
    
    @staticmethod
    def log_download(video, user, request=None):
        """Log a video download request."""
        return VideoLogService.log_activity(
            video=video,
            user=user,
            log_type='download',
            message=f"Download requested for video '{video.title}' by {user.username}",
            request=request
        )
    
    @staticmethod
    def log_error(video, user, error_message):
        """Log an error related to a video."""
        return VideoLogService.log_activity(
            video=video,
            user=user,
            log_type='error',
            message=f"Error: {error_message}"
        )
    
    @staticmethod
    def log_status_change(video, user, old_status, new_status):
        """Log a video status change."""
        return VideoLogService.log_activity(
            video=video,
            user=user,
            log_type='status_change',
            message=f"Status changed from '{old_status}' to '{new_status}'"
        )
    
    @staticmethod
    def get_client_ip(request):
        """
        BACKEND-READY: Extract client IP from HTTP request headers.
        MAPPED TO: Internal utility function
        USED BY: log_activity method for IP tracking
        
        Handles X-Forwarded-For headers for proxy/load balancer setups.
        Falls back to REMOTE_ADDR if forwarded headers unavailable.
        Required fields: request (HttpRequest object)
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip 