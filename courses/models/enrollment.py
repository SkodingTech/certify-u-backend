from django.db import models
from django.contrib.auth import get_user_model
from courses.models.base import GeneralTimeStamp
from courses.models.course import Course, Lesson, Module
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Enrollment(GeneralTimeStamp):
    ENROLLMENT_STATUS = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ENROLLMENT_STATUS, default='active')
    progress = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])    
    class Meta:
        unique_together = ['student', 'course']
    def __str__(self):
        return f"{self.student.username} - {self.course.title}"

class LessonProgress(GeneralTimeStamp):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent = models.PositiveIntegerField(default=0, help_text="Time spent in seconds")    
    class Meta:
        unique_together = ['enrollment', 'lesson']
    def __str__(self):
        return f"{self.enrollment.student.username} - {self.lesson.title}"

class ModuleProgress(GeneralTimeStamp):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='module_progress')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='progress')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['enrollment', 'module']
    
    def __str__(self):
        return f"{self.enrollment.student.username} - {self.module.title} (Module)"