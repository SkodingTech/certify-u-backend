from django.db import models
from django.conf import settings
from courses.models.base import GeneralTimeStamp
from courses.models.course import Course
from courses.models.instructor import Instructor

class LiveSession(GeneralTimeStamp):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('live', 'Live'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    SESSION_TYPE_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='live_sessions')
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='live_sessions')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, default='online')
    location = models.CharField(max_length=255, blank=True, help_text="Physical location for offline sessions")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    meeting_link = models.URLField(blank=True, help_text="Link for the video call (Online only)")
    attendees = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='booked_sessions', blank=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.title} - {self.course.title}"

class LiveSessionRequest(GeneralTimeStamp):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='live_requests')
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='live_requests')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='live_requests', null=True, blank=True)
    request_message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Request by {self.student} to {self.instructor}"
