from django.db import models
from django.contrib.auth import get_user_model
from courses.models.base import GeneralTimeStamp
from courses.models.course import Course
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Assessment(GeneralTimeStamp):
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='assessment')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    time_limit_minutes = models.PositiveIntegerField(help_text="Time limit in minutes", default=60)
    passing_score = models.PositiveIntegerField(help_text="Percentage required to pass", default=70, validators=[MinValueValidator(0), MaxValueValidator(100)])
    max_attempts = models.PositiveIntegerField(default=3) # 0 for unlimited
    encouragement_message = models.TextField(
        blank=True,
        default="Don't be discouraged — review the material and try again. You've got this!",
        help_text="Message shown to learners who fail an attempt",
    )

    def __str__(self):
        return f"Assessment: {self.course.title}"

class AssessmentQuestion(GeneralTimeStamp):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('tf', 'True/False'),
        ('text', 'Short Answer'), # Manual grading might be needed, or exact match
    ]

    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='mcq')
    options = models.JSONField(help_text="List of options for MCQ [{'id': 1, 'text': 'Option A'}, ...]", null=True, blank=True)
    correct_answer = models.JSONField(help_text="ID of correct option or list of IDs or text answer")
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.assessment.title} - Q{self.order}"

class AssessmentAttempt(GeneralTimeStamp):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessment_attempts')
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(default=0.0) # Percentage or raw score? Let's use Percentage for now based on max points.
    passed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.student.username} - {self.assessment.title} - {self.score}%"
