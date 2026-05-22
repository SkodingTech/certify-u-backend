from django.contrib.auth import get_user_model
from django.db.models import Avg
from rest_framework import status
from rest_framework.response import Response

from courses.models.course import Course
from courses.models.enrollment import Enrollment
from courses.models.instructor import Instructor
from courses.models.review import Review


def _is_admin(user):
    """Treat Django staff/superuser or profile role ADMIN/SUPER_ADMIN as platform admin."""
    if not (user and user.is_authenticated):
        return False
    if user.is_staff or user.is_superuser:
        return True
    prof = getattr(user, 'user_profile', None) or getattr(user, 'userprofile', None)
    return bool(prof and getattr(prof, 'role', None) in ('ADMIN', 'SUPER_ADMIN'))


def GetDashboardStats(request):
    user = request.user

    # ── Admin view: platform-wide totals ─────────────────────────────────────
    if _is_admin(user):
        User = get_user_model()
        total_courses = Course.objects.filter(is_deleted=False).count()
        total_active = Enrollment.objects.filter(status='active').count()
        total_completed = Enrollment.objects.filter(status='completed').count()
        total_enrolled = Enrollment.objects.count()
        total_students = User.objects.filter(enrollments__isnull=False).distinct().count()
        total_instructors = Instructor.objects.filter(is_deleted=False).count()
        review_count = Review.objects.filter(is_deleted=False).count()
        avg_rating = Review.objects.filter(is_deleted=False).aggregate(a=Avg('rating'))['a'] or 0

        return Response({
            "view": "admin",
            "active_courses": total_courses,           # surface as "Active Courses" tile
            "total_courses": total_courses,
            "total_students": total_students,
            "total_instructors": total_instructors,
            "total_enrollments": total_enrolled,
            "active_enrollments": total_active,
            "completed_enrollments": total_completed,
            "review_count": review_count,
            "average_rating": round(avg_rating, 2),
            "total_earnings": 0,                       # placeholder until payments wired
        }, status=status.HTTP_200_OK)

    # ── Instructor view ──────────────────────────────────────────────────────
    instructor = getattr(user, 'instructor', None) or Instructor.objects.filter(user=user).first()
    if instructor:
        instr_courses = Course.objects.filter(instructors=instructor, is_deleted=False)
        total_courses_created = instr_courses.count()
        total_students = Enrollment.objects.filter(course__in=instr_courses).values('student').distinct().count()
        review_count = Review.objects.filter(course__in=instr_courses).count()
        avg_rating = Review.objects.filter(course__in=instr_courses).aggregate(a=Avg('rating'))['a'] or 0
        return Response({
            "view": "instructor",
            "active_courses": Enrollment.objects.filter(student=user, status='active').count(),
            "enrolled_courses": Enrollment.objects.filter(student=user).count(),
            "completed_courses": Enrollment.objects.filter(student=user, status='completed').count(),
            "total_students": total_students,
            "total_courses": total_courses_created,
            "total_earnings": 0,
            "review_count": review_count,
            "average_rating": round(avg_rating, 2),
        }, status=status.HTTP_200_OK)

    # ── Student view ─────────────────────────────────────────────────────────
    return Response({
        "view": "student",
        "active_courses": Enrollment.objects.filter(student=user, status='active').count(),
        "enrolled_courses": Enrollment.objects.filter(student=user).count(),
        "completed_courses": Enrollment.objects.filter(student=user, status='completed').count(),
        "total_students": 0,
        "total_courses": 0,
        "total_earnings": 0,
        "review_count": 0,
        "average_rating": 0,
    }, status=status.HTTP_200_OK)
