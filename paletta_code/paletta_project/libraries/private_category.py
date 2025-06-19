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
    Only applies to custom libraries since Paletta-style libraries get private categories automatically.
    """
    if created and instance.category_source == 'custom':
        try:
            Category.objects.create(
                subject_area='private',
                library=instance,
                description='Your private videos. Only the library owner can see this category and its contents.',
                is_active=True
            )
            logger.info(f"Created default 'Private' category for custom library '{instance.name}' (ID: {instance.id})")
        except Exception as e:
            logger.error(f"Failed to create 'Private' category for library '{instance.name}': {e}")
    elif created and instance.category_source == 'paletta_style':
        logger.info(f"Paletta-style library '{instance.name}' will use PalettaCategory private category")
    elif not created:
        logger.debug(f"Library '{instance.name}' already exists, skipping private category creation") 