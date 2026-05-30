from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from users.models.user import UserProfile, StudentProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Create UserProfile with default role='STUDENT'
        UserProfile.objects.create(user=instance, role=UserProfile.Role.STUDENT)
        # Create StudentProfile
        StudentProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Ensure they exist before saving to avoid errors if they were manually deleted
    if hasattr(instance, 'user_profile'):
        instance.user_profile.save()
    if hasattr(instance, 'student_profile'):
        instance.student_profile.save()


@receiver(post_save, sender=User)
def notify_admin_on_new_user(sender, instance, created, **kwargs):
    """Alert platform admins whenever a new user account is created."""
    if not created:
        return
    try:
        from courses.services import notifications as _notify
        _notify.notify_admin_new_user(instance)
    except Exception:
        # Never let an email failure break account creation.
        pass
