from django.db import transaction
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from courses.models.enrollment import Enrollment
from courses.models.course import Course

@receiver(post_save, sender=Enrollment)
def update_course_enrollment_count_on_save(sender, instance, created, **kwargs):
    if created:
        course = instance.course
        course.enrolled_students = course.enrollments.count()
        course.save()

@receiver(post_delete, sender=Enrollment)
def update_course_enrollment_count_on_delete(sender, instance, **kwargs):
    course = instance.course
    course.enrolled_students = course.enrollments.count()
    course.save()


# ─────────────────────────────────────────────────────────────────────────────
# Admin notifications: new enrolment ("payment"), new course, course updates.
# ─────────────────────────────────────────────────────────────────────────────

@receiver(post_save, sender=Enrollment)
def notify_admin_on_new_enrollment(sender, instance, created, **kwargs):
    """Alert admins on a new enrolment — the platform's checkout/payment event."""
    if not created:
        return
    try:
        from courses.services import notifications as _notify
        _notify.notify_admin_new_payment(instance)
    except Exception:
        pass


# Editable fields that constitute a meaningful "course updated" event. Counter
# fields (enrolled_students, rating, review_count) are deliberately excluded so
# internal recomputes / enrolment saves never trigger admin spam.
_COURSE_TRACKED_FIELDS = [
    'title', 'subtitle', 'slug', 'description', 'short_description',
    'thumbnail', 'promo_video', 'price', 'currency', 'status', 'is_approved',
    'level', 'delivery_mode', 'course_type', 'language',
    'duration_weeks', 'weekly_hours', 'has_certificate',
]


@receiver(pre_save, sender=Course)
def _capture_course_changes(sender, instance, **kwargs):
    """Diff tracked fields against the stored row so post_save knows what changed."""
    if not instance.pk:
        instance._notify_changed_fields = None
        return
    try:
        old = Course.objects.get(pk=instance.pk)
    except Course.DoesNotExist:
        instance._notify_changed_fields = None
        return
    changed = [
        f for f in _COURSE_TRACKED_FIELDS
        if getattr(old, f, None) != getattr(instance, f, None)
    ]
    instance._notify_changed_fields = changed


@receiver(post_save, sender=Course)
def notify_on_course_change(sender, instance, created, **kwargs):
    """Alert admins on create/update, and the instructor(s) when a course is
    created. Deferred to transaction commit so M2M instructor links (added after
    the initial save in CreateCourseView) are visible when the email is built."""
    changed = getattr(instance, '_notify_changed_fields', None)
    course_pk = instance.pk

    def _dispatch():
        try:
            from courses.services import notifications as _notify
            course = Course.objects.filter(pk=course_pk).first()
            if course is None:
                return
            if created:
                _notify.notify_admin_new_course(course)
                for instructor in course.instructors.all():
                    _notify.notify_trainer_course_added(course, instructor)
            elif changed:
                _notify.notify_admin_course_updated(course, changed)
        except Exception:
            pass

    transaction.on_commit(_dispatch)
