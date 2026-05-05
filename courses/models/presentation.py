from django.db import models
from django.contrib.auth import get_user_model
from courses.models.base import GeneralTimeStamp
from courses.models.course import Module

User = get_user_model()

class Presentation(GeneralTimeStamp):
    FILE_TYPES = [
        ('pdf', 'PDF'),
        ('ppt', 'PowerPoint'),
    ]

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='presentations')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='course_presentations/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPES, default='pdf')
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_mandatory = models.BooleanField(default=True)
    download_enabled = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']
        unique_together = ['module', 'order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"

class PresentationProgress(GeneralTimeStamp):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='presentation_progress')
    presentation = models.ForeignKey(Presentation, on_delete=models.CASCADE, related_name='progress')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    current_page = models.PositiveIntegerField(default=0)
    total_pages = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['student', 'presentation']

    def __str__(self):
        return f"{self.student.username} - {self.presentation.title}"
