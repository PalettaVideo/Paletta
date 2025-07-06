import logging
import boto3
import uuid
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from botocore.exceptions import ClientError
from .models import DownloadRequest

logger = logging.getLogger(__name__)


class DownloadRequestService:
  """
  BACKEND-READY: Service for managing video download requests with S3 integration.
  MAPPED TO: Download request system
  USED BY: Download request API, Celery tasks, admin operations
  
  Handles S3 presigned URL generation (48h expiry), email automation, and request tracking.
  Integrates with AWS S3 for secure file access and SES for email delivery.
  Required config: AWS credentials, S3 bucket settings, email configuration
  """
  
  def __init__(self):
    """
    BACKEND-READY: Initialize AWS S3 and email services.
    MAPPED TO: Service instantiation
    USED BY: All download request operations
    
    Sets up S3 client for presigned URL generation and validates configuration.
    Auto-disables features if credentials missing or connection fails.
    """
    # Load AWS configuration
    self.storage_enabled = getattr(settings, 'AWS_STORAGE_ENABLED', False)
    
    if self.storage_enabled:
      self.aws_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
      self.aws_secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
      self.aws_region = getattr(settings, 'AWS_REGION', 'us-east-1')
      self.bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
      
      # Initialize S3 client
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
              logger.info("Successfully connected to AWS S3 for download requests")
          except Exception as e:
              self.storage_enabled = False
              logger.error(f"Failed to connect to AWS S3: {str(e)}")
      else:
          self.storage_enabled = False
          logger.warning("AWS storage is enabled but credentials are missing")
    
    # Email configuration
    self.ses_enabled = getattr(settings, 'AWS_SES_ENABLED', False)
    self.sender_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'automatic-video-request@paletta.io')
  
  def create_download_request(self, user, video, email=None):
    """
    BACKEND-READY: Create a new download request with validation.
    MAPPED TO: POST /request-download endpoint
    USED BY: Download request API views
    
    Creates DownloadRequest record, validates user permissions, checks video availability.
    Sets up 48-hour expiry and initializes request status tracking.
    Required fields: user (User), video (Video), email (str, optional)
    """
    if not email:
      email = user.email
    
    # Validate video is available for download
    if video.storage_status != 'stored':
      raise ValueError(f"Video '{video.title}' is not available for download (status: {video.storage_status})")
    
    if not video.storage_reference_id:
      raise ValueError(f"Video '{video.title}' has no storage reference")
    
    # Check for existing pending request (prevent duplicates)
    existing_request = DownloadRequest.objects.filter(
      user=user,
      video=video,
      email=email,
      status__in=['pending', 'completed'],
      expiry_date__gt=timezone.now()
    ).first()
    
    if existing_request:
      logger.info(f"Found existing download request {existing_request.id} for user {user.email}")
      return existing_request
    
    # Create new download request
    download_request = DownloadRequest.objects.create(
      user=user,
      video=video,
      email=email,
      s3_key=video.storage_reference_id,
      status='pending'
    )
    
    logger.info(f"Created download request {download_request.id} for video '{video.title}' by user {user.email}")
    return download_request
  
  def generate_presigned_url(self, download_request):
    """
    BACKEND-READY: Generate S3 presigned URL with 48-hour expiry.
    MAPPED TO: Download link generation
    USED BY: Process download request workflow
    
    Creates secure S3 GET URL valid for exactly 48 hours (172800 seconds).
    Updates DownloadRequest with URL and AWS metadata for tracking.
    Required fields: download_request.s3_key, download_request.video
    """
    if not self.storage_enabled:
      logger.error("AWS storage is not enabled")
      return None
    
    if not download_request.s3_key:
      logger.error(f"Download request {download_request.id} has no S3 key")
      return None
  
    try:
      # Extract bucket name from video's storage URL if available
      bucket_name = self.bucket_name  # Default to configured bucket
      
      if download_request.video.storage_url:
        # Parse bucket name from storage URL (e.g., s3://paletta-videos/...)
        storage_url = download_request.video.storage_url
        if storage_url.startswith('s3://'):
          bucket_name = storage_url.split('/')[2]
          logger.info(f"Using bucket '{bucket_name}' from video storage URL")
      
      # Generate AWS request ID for tracking
      aws_request_id = str(uuid.uuid4())
      
      # Generate presigned URL with exactly 48 hours expiry
      expiry_seconds = 172800  # 48 * 60 * 60 = 172800 seconds
      
      presigned_url = self.s3_client.generate_presigned_url(
        'get_object',
        Params={
          'Bucket': bucket_name,
          'Key': download_request.s3_key,
          'ResponseContentDisposition': f'attachment; filename="{download_request.video.title}"'
        },
        ExpiresIn=expiry_seconds
      )
      
      # Update download request with URL and metadata
      download_request.download_url = presigned_url
      download_request.aws_request_id = aws_request_id
      download_request.save(update_fields=['download_url', 'aws_request_id'])
      
      logger.info(f"Generated presigned URL for download request {download_request.id} (AWS ID: {aws_request_id})")
      return presigned_url
        
    except ClientError as e:
      error_code = e.response.get('Error', {}).get('Code', 'Unknown')
      error_message = f"AWS S3 error ({error_code}): {str(e)}"
      logger.error(f"Failed to generate presigned URL for download request {download_request.id}: {error_message}")
      
      # Update request status
      download_request.status = 'failed'
      download_request.email_error = error_message
      download_request.save(update_fields=['status', 'email_error'])
      
      return None
    except Exception as e:
      error_message = f"Unexpected error: {str(e)}"
      logger.error(f"Failed to generate presigned URL for download request {download_request.id}: {error_message}")
      
      # Update request status
      download_request.status = 'failed'
      download_request.email_error = error_message
      download_request.save(update_fields=['status', 'email_error'])
      
      return None
  
  def send_download_email(self, download_request):
    """
    BACKEND-READY: Send download link email with SES integration.
    MAPPED TO: Email automation system
    USED BY: Download request processing, email resend functionality
    
    Sends templated email with download link and 48-hour expiry notice.
    Updates DownloadRequest with email delivery status and error tracking.
    Required fields: download_request.email, download_request.download_url
    """
    if not download_request.download_url:
      logger.error(f"Download request {download_request.id} has no download URL")
      return False
    
    try:
      # Prepare email context
      context = {
        'user_name': download_request.user.get_full_name() or download_request.user.email.split('@')[0],
        'video_title': download_request.video.title,
        'download_url': download_request.download_url,
        'expiry_date': download_request.expiry_date,
        'expiry_hours': 48,
        'library_name': download_request.video.library.name if download_request.video.library else 'Paletta',
        'support_email': 'support@paletta.io'
      }
      
      # Render email templates
      subject = f"Download link for {download_request.video.title} - Valid for 48 hours"
      html_message = render_to_string('emails/download_link.html', context)
      plain_message = strip_tags(html_message)
      
      # Send email
      send_mail(
        subject=subject,
        message=plain_message,
        from_email=self.sender_email,
        recipient_list=[download_request.email],
        html_message=html_message,
        fail_silently=False
      )
      
      # Update download request
      download_request.email_sent = True
      download_request.email_sent_at = timezone.now()
      download_request.status = 'completed'
      download_request.save(update_fields=['email_sent', 'email_sent_at', 'status'])
      
      logger.info(f"Successfully sent download email for request {download_request.id} to {download_request.email}")
      return True
      
    except Exception as e:
      error_message = str(e)
      logger.error(f"Failed to send download email for request {download_request.id}: {error_message}")
      
      # Update request with error
      download_request.status = 'failed'
      download_request.email_error = error_message
      download_request.save(update_fields=['status', 'email_error'])
      
      return False

  def process_download_request(self, download_request):
    """
    BACKEND-READY: Complete download request processing workflow.
    MAPPED TO: Main request processing pipeline
    USED BY: API endpoints, Celery tasks, admin actions
    
    Orchestrates full download request: URL generation → email sending → status tracking.
    Handles errors at each step and updates request status accordingly.
    Required fields: download_request (DownloadRequest instance)
    """
    logger.info(f"Processing download request {download_request.id} for video '{download_request.video.title}'")
    
    try:
      # Step 1: Generate presigned URL
      presigned_url = self.generate_presigned_url(download_request)
      if not presigned_url:
        logger.error(f"Failed to generate presigned URL for download request {download_request.id}")
        return False
      
      # Step 2: Send email
      email_sent = self.send_download_email(download_request)
      if not email_sent:
        logger.error(f"Failed to send email for download request {download_request.id}")
        return False
      
      logger.info(f"Successfully processed download request {download_request.id}")
      return True
        
    except Exception as e:
      error_message = str(e)
      logger.error(f"Failed to process download request {download_request.id}: {error_message}")
      
      # Update request status
      download_request.status = 'failed'
      download_request.email_error = error_message
      download_request.save(update_fields=['status', 'email_error'])
      
      return False
  
  def cleanup_expired_requests(self):
    """
    BACKEND-READY: Clean up expired download requests and update status.
    MAPPED TO: Scheduled cleanup tasks
    USED BY: Management commands, cron jobs, admin maintenance
    
    Marks expired requests as 'expired' and logs cleanup activity.
    Returns count of expired requests for monitoring and reporting.
    Used in conjunction with background cleanup Lambda/tasks.
    """
    now = timezone.now()
    expired_requests = DownloadRequest.objects.filter(
      expiry_date__lt=now,
      status__in=['pending', 'completed']
    )
    
    expired_count = expired_requests.count()
    if expired_count > 0:
      # Update all expired requests
      expired_requests.update(status='expired')
      logger.info(f"Marked {expired_count} download requests as expired")
    
    return expired_count
  
  def get_user_request_history(self, user, limit=10):
    """
    BACKEND-READY: Get download request history for a user.
    MAPPED TO: User dashboard, request history API
    USED BY: User profile pages, API endpoints
    
    Returns recent download requests with status and expiry information.
    Useful for showing users their download history and current valid links.
    Required fields: user (User instance), limit (int, optional)
    """
    return DownloadRequest.objects.filter(user=user).order_by('-request_date')[:limit] 