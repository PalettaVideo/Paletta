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
  
  Handles download request notifications to managers for monetization decisions.
  Integrates with AWS SES for email delivery to Paletta management.
  Required config: AWS credentials, email configuration
  """
  
  def __init__(self):
    """
    BACKEND-READY: Initialize AWS S3 and email services.
    MAPPED TO: Service instantiation
    USED BY: All download request operations
    
    Sets up email service for manager notifications.
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
    self.sender_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'niklaas@filmbright.com')
    self.manager_email = getattr(settings, 'MANAGER_EMAIL', 'info@filmbright.com')
  
  def create_download_request(self, user, video, email=None):
    """
    BACKEND-READY: Create a new download request with validation.
    MAPPED TO: POST /request-download endpoint
    USED BY: Download request API views
    
    Creates DownloadRequest record, validates user permissions, checks video availability.
    Sets up request status tracking for manager review.
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
    
    # Create new download request (no expiry for manager review process)
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
    USED BY: Manager-initiated download link generation
    
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
      
      logger.info(f"Generated presigned URL for download request {download_request.id}")
      return presigned_url
      
    except ClientError as e:
      error_code = e.response['Error']['Code']
      logger.error(f"AWS S3 error generating presigned URL for request {download_request.id}: {error_code}")
      return None
    except Exception as e:
      logger.error(f"Failed to generate presigned URL for request {download_request.id}: {str(e)}")
      return None
  
  def send_manager_notification(self, download_requests):
    """
    BACKEND-READY: Send notification to manager for download request review.
    MAPPED TO: Manager notification system for monetization review
    USED BY: process_download_request, bulk processing
    
    Sends notification email to manager with customer details and video list.
    No download links are generated or sent to customers.
    Required fields: download_requests (list of DownloadRequest instances)
    """
    if not download_requests:
      logger.error("No download requests provided for manager notification")
      return False
    
    # Handle single request or list of requests
    if not isinstance(download_requests, list):
      download_requests = [download_requests]
    
    try:
      # Get the first request for customer info (assuming same customer for bulk)
      first_request = download_requests[0]
      
      # Simple text cleaning for email compatibility
      def clean_text(text):
          if text is None:
              return ""
          if not isinstance(text, str):
              text = str(text)
          
          # encode to ASCII and replace errors
          try:
              # First pass: replace common problematic characters
              text = text.replace('\u201c', '"').replace('\u201d', '"')  # Smart quotes
              text = text.replace('\u2018', "'").replace('\u2019', "'")  # Smart quotes
              text = text.replace('\u2013', '-').replace('\u2014', '-')  # Dashes
              text = text.replace('\u2026', '...')  # Ellipsis
              
              # encode to ASCII, replace errors, then back to UTF-8
              # This will replace ANY problematic character with a safe placeholder
              ascii_safe = text.encode('ascii', 'replace').decode('ascii')
              return ascii_safe
          except Exception as e:
              logger.warning(f"Text cleaning failed for: {repr(text[:30])}... Error: {str(e)}")
              # Ultimate fallback: return only printable ASCII characters
              return ''.join(char for char in text if ord(char) < 128 and char.isprintable() or char.isspace())
      
      # Clean all text fields that might contain problematic characters
      customer_name = clean_text(first_request.user.get_full_name() or first_request.user.email.split('@')[0])
      customer_email = clean_text(first_request.user.email)
      sender_email = clean_text(self.sender_email)
      manager_email = clean_text(self.manager_email)
      
      logger.debug(f"Manager notification emails - From: {repr(sender_email)}, To: {repr(manager_email)}")
      
      # Clean library name
      library_name = None
      if download_requests[0].video.library:
          library_name = clean_text(download_requests[0].video.library.name)
      
      # Template-level robustness: Clean video objects before passing to template
      cleaned_videos = []
      for req in download_requests:
          # Create a cleaned representation of each video
          video_data = {
              'id': req.video.id,
              'title': clean_text(req.video.title),
              'description': clean_text(req.video.description or ""),
              'duration_formatted': clean_text(req.video.duration_formatted),
              'file_size': req.video.file_size, 
              'format': clean_text(req.video.format or ""),
              'download_url': req.download_url,
              'content_type': None
          }
          
          # Safely handle content_type
          if req.video.content_type:
              try:
                  video_data['content_type'] = {
                      'display_name': clean_text(req.video.content_type.display_name)
                  }
              except Exception as e:
                  logger.warning(f"Could not clean content_type for video {req.video.id}: {str(e)}")
                  video_data['content_type'] = {'display_name': 'Unknown'}
          
          cleaned_videos.append(video_data)
      
      # Prepare email context with cleaned data
      context = {
        'customer_name': customer_name,
        'customer_email': customer_email,
        'customer_id': first_request.user.id,
        'request_date': timezone.now(),
        'video_count': len(download_requests),
        'videos': cleaned_videos,  # Use cleaned video data
        'customer_library': library_name,
        'request_id': download_requests[0].id if len(download_requests) == 1 else 'Multiple requests'
      }
      
      # Create and validate subject with header injection protection
      subject = clean_text(f"New Video Download Request from {customer_email} ({len(download_requests)} video{'s' if len(download_requests) > 1 else ''})")
      
      # Header injection protection
      if any('\n' in x or '\r' in x for x in [subject, sender_email, manager_email]):
          logger.error("Header injection detected in email fields")
          raise ValueError("Header injection detected in email headers")
      
      try:
          html_message = render_to_string('emails/manager_download_request.html', context)
          html_message = clean_text(html_message)
          
          # Don't escape HTML for email templates - they need to remain as valid HTML
          # The clean_text function already handles problematic characters
          
      except Exception as e:
          logger.error(f"Error rendering HTML template: {str(e)}")
          # Enhanced error logging for template rendering
          try:
              if hasattr(e, 'object') and hasattr(e, 'start'):
                  snippet = repr(e.object[e.start:e.start+10])
                  logger.error(f"Template rendering failed at: {snippet}")
          except:
              pass
              
          # Fallback to plain text formatted as simple HTML
          html_message = f"""
          <!DOCTYPE html>
          <html>
          <body>
          <h2>New Video Download Request</h2>
          <p><strong>Customer:</strong> {customer_name} ({customer_email})</p>
          <p><strong>Videos requested:</strong> {len(download_requests)}</p>
          <p><strong>Request ID:</strong> {context['request_id']}</p>
          <p>Please review this request in the admin panel.</p>
          </body>
          </html>
          """
          html_message = clean_text(html_message)
      
      try:
          plain_message = strip_tags(html_message)
          plain_message = clean_text(plain_message)
      except Exception as e:
          logger.error(f"Error creating plain message: {str(e)}")
          # Fallback to simple plain text
          plain_message = f"""
New Video Download Request

Customer: {customer_name} ({customer_email})
Videos requested: {len(download_requests)}
Request ID: {context['request_id']}

Please review this request in the admin panel.
          """.strip()
          plain_message = clean_text(plain_message)
      
      # Final encoding validation before sending
      try:
          subject.encode('utf-8')
          html_message.encode('utf-8')
          plain_message.encode('utf-8')
          sender_email.encode('utf-8')
          manager_email.encode('utf-8')
      except UnicodeError as e:
          logger.error(f"Final encoding validation failed: {str(e)}")
          return False
      
      # Send email to manager
      send_mail(
        subject=subject,
        message=plain_message,
        from_email=sender_email,
        recipient_list=[manager_email],
        html_message=html_message,
        fail_silently=False
      )
      
      # Update download requests status
      for download_request in download_requests:
        download_request.email_sent = True
        download_request.email_sent_at = timezone.now()
        download_request.status = 'completed'  # Completed means notification sent to manager
        download_request.save(update_fields=['email_sent', 'email_sent_at', 'status'])
      
      logger.info(f"Successfully sent manager notification for {len(download_requests)} download request(s) from {customer_email}")
      return True
      
    except Exception as e:
      error_message = str(e)
      logger.error(f"Failed to send manager notification: {error_message}")
      
      # Update requests with error
      for download_request in download_requests:
        download_request.status = 'failed'
        download_request.email_error = error_message
        download_request.save(update_fields=['status', 'email_error'])
      
      return False

  def send_download_email(self, download_request):
    """
    DEPRECATED: This method has been replaced by send_manager_notification.
    BACKEND-READY: Send download link email with SES integration.
    MAPPED TO: Email automation system
    USED BY: Download request processing, email resend functionality
    
    This method is kept for compatibility but redirects to manager notification.
    """
    logger.warning(f"send_download_email called for request {download_request.id} - redirecting to manager notification")
    return self.send_manager_notification(download_request)

  def send_bulk_download_email(self, download_requests):
    """
    BACKEND-READY: Send bulk download email with multiple presigned URLs to user.
    MAPPED TO: Bulk download request email automation
    USED BY: Cart checkout flow, bulk download operations
    
    Sends email with multiple 48-hour download links and instructions.
    Includes video metadata and expiry information for all videos.
    Required fields: download_requests (list of DownloadRequest instances)
    """
    try:
      from django.core.mail import send_mail
      from django.template.loader import render_to_string
      from django.utils.html import strip_tags
      
      # Prepare email context with multiple videos
      context = {
        'user_name': download_requests[0].user.get_full_name() or download_requests[0].user.email,
        'videos': [],
        'total_videos': len(download_requests),
        'expiry_hours': 48,  # Fixed 48-hour expiry
        'support_email': 'support@paletta.io',
        'request_date': timezone.now(),
      }
      
      # Add each video's information
      for download_request in download_requests:
        video_info = {
          'title': download_request.video.title,
          'download_url': download_request.download_url,
          'expiry_date': download_request.video.download_link_expiry,  # Use video's download link expiry
          'library_name': download_request.video.library.name if download_request.video.library else None,
          'duration': download_request.video.duration_formatted if hasattr(download_request.video, 'duration_formatted') else 'Unknown',
          'file_size': download_request.video.file_size,
        }
        context['videos'].append(video_info)
      
      # Render email templates using the existing manager template
      html_message = render_to_string('emails/manager_download_request.html', context)
      plain_message = strip_tags(html_message)
      
      # Send email to manager with download links
      send_mail(
        subject=f'Download Links Generated - {len(download_requests)} Videos from {download_requests[0].user.email}',
        message=plain_message,
        from_email=self.sender_email,
        recipient_list=[self.manager_email],
        html_message=html_message,
        fail_silently=False,
      )
      
      logger.info(f"Bulk download email sent successfully for {len(download_requests)} videos")
      return True
      
    except Exception as e:
      error_message = str(e)
      logger.error(f"Failed to send bulk download email for {len(download_requests)} videos: {error_message}")
      return False

  def process_download_request(self, download_request):
    """
    BACKEND-READY: Complete download request processing workflow.
    MAPPED TO: Main request processing pipeline
    USED BY: API endpoints, Celery tasks, admin actions
    
    Orchestrates download request: manager notification → status tracking.
    No download links are generated for customers - manager handles monetization.
    Required fields: download_request (DownloadRequest instance)
    """
    logger.info(f"Processing download request {download_request.id} for video '{download_request.video.title}'")
    
    try:
      # Send manager notification instead of generating download links
      notification_sent = self.send_manager_notification(download_request)
      if not notification_sent:
        logger.error(f"Failed to send manager notification for download request {download_request.id}")
        return False
      
      logger.info(f"Successfully processed download request {download_request.id} - manager notified")
      return True
        
    except Exception as e:
      error_message = str(e)
      logger.error(f"Failed to process download request {download_request.id}: {error_message}")
      
      # Update request status
      download_request.status = 'failed'
      download_request.email_error = error_message
      download_request.save(update_fields=['status', 'email_error'])
      
      return False

  def process_bulk_download_request(self, download_requests):
    """
    BACKEND-READY: Process multiple download requests with download links.
    MAPPED TO: Bulk download request processing
    USED BY: Cart checkout flow, bulk download operations
    
    Generates download links for all requests and sends them to the user.
    Also sends manager notification for review.
    Required fields: download_requests (list of DownloadRequest instances)
    """
    if not download_requests:
      logger.error("No download requests provided for bulk processing")
      return False
    
    logger.info(f"Processing bulk download request with {len(download_requests)} videos")
    
    try:
      # Import the AWS storage service for download link generation
      from videos.services import AWSCloudStorageService
      storage_service = AWSCloudStorageService()
      
      # Generate download links for all requests
      successful_requests = []
      failed_requests = []
      
      for download_request in download_requests:
        try:
          # Generate download link using the existing AWS service
          logger.info(f"Generating download link for video {download_request.video.id} (title: {download_request.video.title})")
          download_url = storage_service.generate_download_link(download_request.video)
          if download_url:
            logger.info(f"Successfully generated download URL for video {download_request.video.id}: {download_url[:50]}...")
            # Update request with download URL
            download_request.download_url = download_url
            download_request.status = 'completed'
            download_request.email_sent = True
            download_request.email_sent_at = timezone.now()
            download_request.save(update_fields=['download_url', 'status', 'email_sent', 'email_sent_at'])
            
            successful_requests.append(download_request)
          else:
            logger.error(f"Failed to generate download URL for video {download_request.video.id}")
            failed_requests.append(download_request)
        except Exception as e:
          logger.error(f"Failed to generate download link for request {download_request.id}: {str(e)}")
          failed_requests.append(download_request)
      
      # Send manager notification with download links for all requests
      logger.info(f"Sending manager notification for {len(download_requests)} requests")
      notification_sent = self.send_manager_notification(download_requests)
      if not notification_sent:
        logger.error(f"Failed to send manager notification for {len(download_requests)} requests")
        # Mark all as failed
        for download_request in download_requests:
          download_request.status = 'failed'
          download_request.email_error = 'Failed to notify manager'
          download_request.save(update_fields=['status', 'email_error'])
        return False
      else:
        logger.info(f"Successfully sent manager notification for {len(download_requests)} requests")
      
      logger.info(f"Successfully processed bulk download request: {len(successful_requests)} successful, {len(failed_requests)} failed")
      return len(successful_requests) > 0
        
    except Exception as e:
      error_message = str(e)
      logger.error(f"Failed to process bulk download request: {error_message}")
      
      # Update all request statuses
      for download_request in download_requests:
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