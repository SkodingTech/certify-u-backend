from courses.models.enrollment import Enrollment
from courses.models.course import Course
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum

def GetDashboardStats(request):
    user = request.user
    
    # 1. Active Courses (Student Enrolled + Active)
    active_courses = Enrollment.objects.filter(student=user, status='active').count()
    
    # 2. Enrolled Courses (All)
    total_enrolled = Enrollment.objects.filter(student=user).count()
    
    # 3. Completed Courses
    completed_courses = Enrollment.objects.filter(student=user, status='completed').count()
    
    # 4. Total Students (Instructor view)
    # Count distinct students enrolled in courses taught by this user (Instructor)
    # Assuming user.instructorprofile exists or user is linked to courses directly via 'instructors' M2M
    # Course model has: instructors = models.ManyToManyField(Instructor, related_name='courses')
    # Instructor model has OneToOne with User
    total_students = 0
    total_courses_created = 0
    total_earnings = 0
    review_count = 0
    
    instructor = None
    if hasattr(user, 'instructor'):
        instructor = user.instructor
    else:
        from courses.models.instructor import Instructor
        instructor = Instructor.objects.filter(user=user).first()

    if instructor:
        instructor_courses = Course.objects.filter(instructors=instructor)
        total_courses_created = instructor_courses.count()
        total_students = Enrollment.objects.filter(course__in=instructor_courses).values('student').distinct().count()
        from courses.models.review import Review
        review_count = Review.objects.filter(course__in=instructor_courses).count()
        # total_earnings = ... would be calculated here if payments were linked
        
    data = {
        "active_courses": active_courses,
        "enrolled_courses": total_enrolled,
        "completed_courses": completed_courses,
        "total_students": total_students,
        "total_courses": total_courses_created,
        "total_earnings": total_earnings,
        "review_count": review_count
    }
    
    return Response(data, status=status.HTTP_200_OK)
