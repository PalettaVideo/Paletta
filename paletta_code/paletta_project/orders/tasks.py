from celery import shared_task
from django.utils import timezone
from .services import DownloadRequestService
from .models import DownloadRequest
from videos.models import Video
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_download_requests():
  """
  BACKEND-READY: Celery task for cleaning up expired download requests.
  MAPPED TO: Scheduled background task (every 30 minutes)
  USED BY: Celery Beat scheduler, admin maintenance operations
  
  Automatically marks expired download requests as 'expired' status.
  Runs periodically to maintain database hygiene and prevent storage bloat.
  Returns count of cleaned requests for monitoring and logging.
  """
  try:
    download_service = DownloadRequestService()
    cleaned_count = download_service.cleanup_expired_requests()
    
    if cleaned_count > 0:
      logger.info(f"Cleanup task completed: {cleaned_count} expired download requests processed")
    
    return {
      'success': True,
      'cleaned_count': cleaned_count,
      'timestamp': timezone.now().isoformat()
    }
      
  except Exception as e:
    error_message = f"Error in cleanup_expired_download_requests task: {str(e)}"
    logger.error(error_message)
    return {
      'success': False,
      'error': error_message,
      'timestamp': timezone.now().isoformat()
    }


@shared_task
def process_download_request_async(download_request_id):
  """
  BACKEND-READY: Async task for processing download requests.
  MAPPED TO: Download request processing pipeline
  USED BY: Download request API when async processing is preferred
  
  Generates S3 presigned URL and sends email notification asynchronously.
  Useful for handling high-volume download requests without blocking API response.
  Required fields: download_request_id (int)
  """
  try:
    download_request = DownloadRequest.objects.get(id=download_request_id)
    download_service = DownloadRequestService()
    
    success = download_service.process_download_request(download_request)
    
    if success:
      logger.info(f"Successfully processed download request {download_request_id} asynchronously")
      return {
        'success': True,
        'download_request_id': download_request_id,
        'video_title': download_request.video.title,
        'email': download_request.email,
        'timestamp': timezone.now().isoformat()
      }
    else:
      logger.error(f"Failed to process download request {download_request_id} asynchronously")
      return {
        'success': False,
        'download_request_id': download_request_id,
        'error': 'Processing failed',
        'timestamp': timezone.now().isoformat()
      }
            
  except DownloadRequest.DoesNotExist:
    error_message = f"Download request {download_request_id} not found"
    logger.error(error_message)
    return {
      'success': False,
      'error': error_message,
      'timestamp': timezone.now().isoformat()
    }
  except Exception as e:
    error_message = f"Error processing download request {download_request_id}: {str(e)}"
    logger.error(error_message)
    return {
      'success': False,
      'error': error_message,
      'timestamp': timezone.now().isoformat()
    }


@shared_task
def resend_failed_download_emails():
  """
  BACKEND-READY: Retry failed download email notifications.
  MAPPED TO: Scheduled background task for error recovery
  USED BY: Celery Beat scheduler, admin retry operations
  
  Attempts to resend emails for download requests that failed email delivery.
  Only retries recent failures (within 24 hours) to avoid spam.
  Returns statistics for monitoring and alerting.
  """
  try:
    # Find failed requests from the last 24 hours
    cutoff_time = timezone.now() - timezone.timedelta(hours=24)
    
    failed_requests = DownloadRequest.objects.filter(
      status='failed',
      request_date__gte=cutoff_time,
      download_url__isnull=False  # Only retry if URL was generated
    ).select_related('user', 'video')
    
    if not failed_requests.exists():
      return {
        'success': True,
        'message': 'No failed requests to retry',
        'retried_count': 0,
        'timestamp': timezone.now().isoformat()
      }
    
    download_service = DownloadRequestService()
    success_count = 0
    total_count = failed_requests.count()
    
    for download_request in failed_requests:
      # Check if still within expiry period
      if download_request.is_expired():
        continue
          
      # Attempt to resend email
      email_success = download_service.send_download_email(download_request)
      if email_success:
        success_count += 1
    
    logger.info(f"Email retry task completed: {success_count}/{total_count} emails resent successfully")
    
    return {
      'success': True,
      'retried_count': success_count,
      'total_failed': total_count,
      'timestamp': timezone.now().isoformat()
    }
      
  except Exception as e:
    error_message = f"Error in resend_failed_download_emails task: {str(e)}"
    logger.error(error_message)
    return {
      'success': False,
      'error': error_message,
      'timestamp': timezone.now().isoformat()
    }


@shared_task
def bulk_process_download_requests(video_ids, user_id, email):
  """
  BACKEND-READY: Bulk process multiple download requests asynchronously.
  MAPPED TO: Bulk download request processing
  USED BY: Cart checkout flow, bulk download operations
  
  Processes multiple video download requests in the background.
  Useful for large cart operations that might timeout in synchronous processing.
  Required fields: video_ids (list), user_id (int), email (str)
  """
  try:
    from accounts.models import User
    
    user = User.objects.get(id=user_id)
    download_service = DownloadRequestService()
    
    results = []
    successful_requests = 0
    
    for video_id in video_ids:
      try:
        video = Video.objects.get(id=video_id)
        
        # Create and process download request
        download_request = download_service.create_download_request(
          user=user,
          video=video,
          email=email
        )
        
        success = download_service.process_download_request(download_request)
        
        if success:
          successful_requests += 1
          results.append({
              'video_id': video_id,
              'video_title': video.title,
              'success': True,
              'request_id': download_request.id
          })
        else:
          results.append({
              'video_id': video_id,
              'video_title': video.title,
              'success': False,
              'error': 'Processing failed'
          })
              
      except Video.DoesNotExist:
        results.append({
          'video_id': video_id,
          'success': False,
          'error': 'Video not found'
        })
      except Exception as e:
        logger.error(f"Error processing bulk download for video {video_id}: {str(e)}")
        results.append({
          'video_id': video_id,
          'success': False,
          'error': str(e)
        })
    
    logger.info(f"Bulk download task completed: {successful_requests}/{len(video_ids)} requests processed successfully")
    
    return {
      'success': successful_requests > 0,
      'successful_count': successful_requests,
      'total_count': len(video_ids),
      'results': results,
      'email': email,
      'timestamp': timezone.now().isoformat()
    }
      
  except User.DoesNotExist:
    error_message = f"User {user_id} not found"
    logger.error(error_message)
    return {
      'success': False,
      'error': error_message,
      'timestamp': timezone.now().isoformat()
    }
  except Exception as e:
    error_message = f"Error in bulk_process_download_requests task: {str(e)}"
    logger.error(error_message)
    return {
      'success': False,
      'error': error_message,
      'timestamp': timezone.now().isoformat()
    } 