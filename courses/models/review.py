from django.db import models
from django.contrib.auth import get_user_model
from courses.models.base import GeneralTimeStamp
from courses.models.course import Course

User = get_user_model()

class Review(GeneralTimeStamp):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    helpful_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title} - {self.rating} stars"