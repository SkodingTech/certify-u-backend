"""
Django Signals for SCORM Module
Handles model events and side effects
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone

from scorm.models import ScormTracking, ScormAttempt


@receiver(post_save, sender=ScormTracking)
def update_tracking_completion(sender, instance, created, **kwargs):
    """
    Update tracking completion status
    Called when ScormTracking is saved
    """
    if not created:
        # Update last access time if tracking modified
        instance.save(update_fields=['updated_at'])


@receiver(post_save, sender=ScormAttempt)
def increment_package_attempts(sender, instance, created, **kwargs):
    """
    Increment attempt counter when new attempt created
    """
    if created:
        from scorm.models import ScormPackage

        try:
            package = instance.package
            # Count total attempts for this package
            total_attempts = ScormAttempt.objects.filter(
                package=package
            ).count()
            # Could store in package metadata if needed
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error incrementing package attempts: {str(e)}")
