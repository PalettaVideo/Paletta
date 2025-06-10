from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Library
from videos.models import Category
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Library)
def create_default_private_category(sender, instance, created, **kwargs):
  """
  Create a default 'Private' category when a new library is created.
  """
  if created:
    try:
      Category.objects.create(
          name='Private',
          library=instance,
          description='Your private videos. Only the library owner can see this category and its contents.'
      )
      logger.info(f"Created default 'Private' category for library '{instance.name}' (ID: {instance.id})")
    except Exception as e:
      logger.error(f"Failed to create 'Private' category for library '{instance.name}': {e}") 