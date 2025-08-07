import os
import logging
import boto3
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class AWSCloudStorageService:
    """
    AWS S3 storage service for video file management.
    Handles S3 operations: multipart upload, download link generation, streaming URLs, deletion.
    """
    
    def __init__(self):
        """
        Initialize AWS S3 service with configuration validation.
        """
        # Get configuration from Django settings
        self.storage_enabled = getattr(settings, 'AWS_STORAGE_ENABLED', False)
        
        if self.storage_enabled:
            self.aws_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
            self.aws_secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            self.aws_region = getattr(settings, 'AWS_REGION', 'us-east-1')
            self.bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
            self.download_link_expiry = getattr(settings, 'DOWNLOAD_LINK_EXPIRY_HOURS', 24)
            
            # Multipart upload configuration from settings
            self.multipart_threshold = getattr(settings, 'S3_MULTIPART_THRESHOLD', 5 * 1024 * 1024)  # 5MB default
            self.multipart_chunk_size = getattr(settings, 'S3_MULTIPART_CHUNK_SIZE', 10 * 1024 * 1024)  # 10MB default
            self.max_concurrent_parts = getattr(settings, 'S3_MAX_CONCURRENT_PARTS', 10)  # 10 concurrent parts default
            
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
    
    def _multipart_upload(self, video, s3_key, content_type):
        """
        Multipart upload with parallel processing for large files.
        Implements multipart upload with concurrent part uploads for better performance.
        Supports files up to 10GB with 100MB chunks and 100 concurrent parts.
        """
        try:
            file_size = video.video_file.size
            chunk_size = self.multipart_chunk_size
            
            # Calculate number of parts
            num_parts = math.ceil(file_size / chunk_size)
            
            # Validate file size limits (S3 supports up to 5TB with multipart)
            max_file_size = 10 * 1024 * 1024 * 1024  # 10GB limit
            if file_size > max_file_size:
                logger.error(f"File size {file_size} bytes exceeds maximum allowed size of {max_file_size} bytes")
                return False
            
            # Log upload details for large files
            file_size_gb = file_size / (1024 * 1024 * 1024)
            logger.info(f"Starting multipart upload for video ID {video.id}: {file_size_gb:.2f}GB, {num_parts} parts, {chunk_size / (1024*1024):.0f}MB chunks")
            
            # Initiate multipart upload
            response = self.s3_client.create_multipart_upload(
                Bucket=self.bucket_name,
                Key=s3_key,
                ContentType=content_type,
                ACL='private'
            )
            
            upload_id = response['UploadId']
            parts = []
            
            # Upload parts in parallel with adaptive concurrency
            max_workers = min(self.max_concurrent_parts, num_parts)
            logger.info(f"Using {max_workers} concurrent workers for {num_parts} parts")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all part upload tasks
                future_to_part = {}
                
                for part_number in range(1, num_parts + 1):
                    start_byte = (part_number - 1) * chunk_size
                    end_byte = min(start_byte + chunk_size, file_size)
                    
                    future = executor.submit(
                        self._upload_part,
                        video,
                        upload_id,
                        part_number,
                        start_byte,
                        end_byte
                    )
                    future_to_part[future] = part_number
                
                # Collect results as they complete
                completed_parts = 0
                for future in as_completed(future_to_part):
                    part_number = future_to_part[future]
                    try:
                        etag = future.result()
                        parts.append({
                            'ETag': etag,
                            'PartNumber': part_number
                        })
                        completed_parts += 1
                        
                        # Log progress for large uploads
                        if num_parts > 10:  # Only log progress for large files
                            progress = (completed_parts / num_parts) * 100
                            logger.info(f"Upload progress: {progress:.1f}% ({completed_parts}/{num_parts} parts completed)")
                        else:
                            logger.info(f"Completed part {part_number}/{num_parts} for video ID {video.id}")
                            
                    except Exception as e:
                        logger.error(f"Part {part_number} upload failed for video ID {video.id}: {str(e)}")
                        # Abort multipart upload on failure
                        self.s3_client.abort_multipart_upload(
                            Bucket=self.bucket_name,
                            Key=s3_key,
                            UploadId=upload_id
                        )
                        return False
            
            # Complete multipart upload
            logger.info(f"Completing multipart upload for video ID {video.id} with {len(parts)} parts")
            self.s3_client.complete_multipart_upload(
                Bucket=self.bucket_name,
                Key=s3_key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            
            logger.info(f"Successfully completed multipart upload for video ID {video.id}: {file_size_gb:.2f}GB")
            return True
            
        except Exception as e:
            logger.error(f"Multipart upload failed for video ID {video.id}: {str(e)}")
            # Attempt to abort multipart upload
            try:
                self.s3_client.abort_multipart_upload(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    UploadId=upload_id
                )
            except:
                pass
            return False
    
    def _upload_part(self, video, upload_id, part_number, start_byte, end_byte):
        """
        Upload a single part of a multipart upload.
        Uploads a specific byte range of the file as a multipart part.
        """
        try:
            with video.video_file.open('rb') as file_data:
                # Seek to the start position
                file_data.seek(start_byte)
                
                # Read the chunk
                chunk = file_data.read(end_byte - start_byte)
                
                # Upload the part
                response = self.s3_client.upload_part(
                    Bucket=self.bucket_name,
                    Key=video.storage_reference_id or f"videos/user_{video.uploader.id}/{video.id}/{os.path.basename(video.video_file.name)}",
                    PartNumber=part_number,
                    UploadId=upload_id,
                    Body=chunk
                )
                
                return response['ETag']
                
        except Exception as e:
            logger.error(f"Part {part_number} upload failed: {str(e)}")
            raise e
    
    def generate_download_link(self, video):
        """
        Generate temporary S3 download link with expiry.
        Creates presigned S3 URL for video download (24h default expiry).
        Updates video model with link and expiry timestamp.
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
        Generate temporary S3 streaming URL.
        Creates presigned S3 URL for video streaming (1h expiry).
        Used for in-browser video playback without downloads.
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
        Delete video and thumbnail from S3 storage.
        Removes video from S3, clears storage metadata, resets status to pending.
        Handles both video files and associated thumbnails.
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
    Comprehensive video activity logging service.
    Creates structured logs for uploads, downloads, errors, status changes.
    Captures IP addresses, user agents, and metadata for admin tracking.
    """
    
    @staticmethod
    def log_activity(video, user, log_type, message, request=None, **kwargs):
        """
        Core logging method for all video activities.
        Creates VideoLog entries with metadata extraction from requests.
        Supports IP tracking and user agent capture for security auditing.
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
        Extract client IP from HTTP request headers.
        Handles X-Forwarded-For headers for proxy/load balancer setups.
        Falls back to REMOTE_ADDR if forwarded headers unavailable.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip 