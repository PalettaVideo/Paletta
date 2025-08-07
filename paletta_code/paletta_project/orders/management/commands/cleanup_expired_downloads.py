from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from orders.services import DownloadRequestService
from orders.models import DownloadRequest
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
  """
  BACKEND-READY: Management command for cleaning up expired download requests.
  MAPPED TO: python manage.py cleanup_expired_downloads
  USED BY: Scheduled tasks, cron jobs, admin maintenance operations
  
  Marks expired download requests as 'expired' and provides cleanup statistics.
  Designed to run regularly (hourly/daily) to maintain database hygiene.
  Supports dry-run mode for testing and verbose output for monitoring.
  """
  
  help = 'Clean up expired download requests and update their status'
  
  def add_arguments(self, parser):
    """Add command line arguments."""
    parser.add_argument(
      '--dry-run',
      action='store_true',
      help='Show what would be cleaned up without making changes',
    )
    parser.add_argument(
      '--verbose',
      action='store_true',
      help='Show detailed output of cleanup operations',
    )
    parser.add_argument(
      '--older-than-hours',
      type=int,
      default=0,
      help='Only clean requests older than this many hours (default: 0 = all expired)',
    )
  
  def handle(self, *args, **options):
    """Execute the cleanup command."""
    dry_run = options['dry_run']
    verbose = options['verbose']
    older_than_hours = options['older_than_hours']
    
    self.stdout.write(
      self.style.SUCCESS(
        'Starting download request cleanup...'
      )
    )
    
    if dry_run:
      self.stdout.write(
        self.style.WARNING('DRY RUN MODE - No changes will be made')
      )
  
    try:
      with transaction.atomic():
        # Get current time for comparison
        now = timezone.now()
        
        # Build query for expired requests
        query = DownloadRequest.objects.filter(
            expiry_date__lt=now,
            status__in=['pending', 'completed']
        )
        
        # Apply older-than filter if specified
        if older_than_hours > 0:
            cutoff_time = now - timezone.timedelta(hours=older_than_hours)
            query = query.filter(expiry_date__lt=cutoff_time)
        
        expired_requests = list(query.select_related('user', 'video'))
        expired_count = len(expired_requests)
        
        if expired_count == 0:
          self.stdout.write(
            self.style.SUCCESS('No expired download requests found.')
          )
          return
        
        # Show what will be cleaned up
        if verbose:
          self.stdout.write(
            self.style.HTTP_INFO(f'\nFound {expired_count} expired requests:')
          )
          for req in expired_requests[:10]:  # Show first 10
            expiry_ago = now - req.expiry_date
            self.stdout.write(
              f'  • ID {req.id}: "{req.video.title}" '
              f'(expired {expiry_ago.days}d {expiry_ago.seconds//3600}h ago)'
            )
          if expired_count > 10:
            self.stdout.write(f'  ... and {expired_count - 10} more')
        
        # Perform cleanup
        if not dry_run:
          # Use the service method for consistent cleanup
          download_service = DownloadRequestService()
          cleaned_count = download_service.cleanup_expired_requests()
          
          if cleaned_count != expired_count:
            self.stdout.write(
              self.style.WARNING(
                f'Expected to clean {expired_count} requests, '
                f'but cleaned {cleaned_count}. This may indicate '
                f'concurrent modifications.'
              )
            )
          
          # Log cleanup statistics
          self.stdout.write(
            self.style.SUCCESS(
              f'Successfully marked {cleaned_count} download requests as expired'
            )
          )
          
          # Additional statistics
          if verbose:
            self._show_cleanup_statistics()
          
          logger.info(f"Cleanup completed: {cleaned_count} expired download requests processed")
            
        else:
          # Dry run - just report what would be done
          self.stdout.write(
            self.style.HTTP_INFO(
              f'DRY RUN: Would mark {expired_count} requests as expired'
            )
          )
            
    except Exception as e:
      error_message = f"Error during cleanup: {str(e)}"
      logger.error(error_message)
      raise CommandError(error_message)
  
  def _show_cleanup_statistics(self):
    """Show detailed cleanup statistics.""" 
    now = timezone.now()
    
    # Get status distribution
    status_counts = {}
    for status_choice in DownloadRequest.REQUEST_STATUS_CHOICES:
      status = status_choice[0]
      count = DownloadRequest.objects.filter(status=status).count()
      if count > 0:
        status_counts[status_choice[1]] = count
    
    # Show current status distribution
    self.stdout.write('\nCurrent download request status distribution:')
    for status_display, count in status_counts.items():
      self.stdout.write(f'  • {status_display}: {count} requests')
    
    # Show recent activity (last 24 hours)
    recent_cutoff = now - timezone.timedelta(hours=24)
    recent_requests = DownloadRequest.objects.filter(
      request_date__gte=recent_cutoff
    ).count()
    
    self.stdout.write(f'\nRecent activity (last 24 hours): {recent_requests} new requests')
    
    # Show upcoming expirations (next 24 hours)
    upcoming_cutoff = now + timezone.timedelta(hours=24)
    upcoming_expirations = DownloadRequest.objects.filter(
      expiry_date__range=(now, upcoming_cutoff),
      status__in=['pending', 'completed']
    ).count()
    
    if upcoming_expirations > 0:
      self.stdout.write(
        self.style.WARNING(
          f'Upcoming expirations (next 24 hours): {upcoming_expirations} requests'
        )
      ) 