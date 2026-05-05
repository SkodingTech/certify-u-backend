from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from courses.models.enrollment import Enrollment

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
