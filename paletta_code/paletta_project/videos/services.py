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
    Service for handling storage operations with AWS S3.
    Provides methods for uploading videos to S3, generating temporary download links,
    and managing video storage lifecycle.
    """
    
    def __init__(self):
        """Initialize the storage service with AWS S3 configuration."""
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
        Upload a video file to AWS S3 storage.
        
        Args:
            video: The Video model instance
            
        Returns:
            bool: True if successful, False otherwise
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
        Generate a temporary download link for a video stored in S3.
        
        Args:
            video: The Video model instance
            
        Returns:
            str: The download URL or None if failed
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
        Generate a temporary streaming URL for a video stored in S3.
        
        Args:
            video: The Video model instance
            
        Returns:
            str: The streaming URL or None if failed
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
        Delete a video from S3 storage.
        
        Args:
            video: The Video model instance
            
        Returns:
            bool: True if successful, False otherwise
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
    Service for logging video-related activities.
    Provides methods for creating log entries for different types of activities.
    """
    
    @staticmethod
    def log_activity(video, user, log_type, message, request=None, **kwargs):
        """
        Create a log entry for a video activity.
        
        Args:
            video: The Video model instance
            user: The User model instance
            log_type: The type of log entry (from VideoLog.LOG_TYPE_CHOICES)
            message: The log message
            request: Optional HTTP request object to extract IP and user agent
            **kwargs: Additional metadata to store in the log
            
        Returns:
            VideoLog: The created log entry
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
        """Extract the client IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip 