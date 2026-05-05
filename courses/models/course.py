from django.db import models
from django.contrib.auth import get_user_model
from courses.models.base import GeneralTimeStamp
from courses.models.instructor import Instructor
from courses.models.organizer import Organization
from courses.models.category import Category
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from ckeditor_uploader.fields import RichTextUploadingField

from courses.models.regulatory import RegulatoryAuthority

User = get_user_model()

class Course(GeneralTimeStamp):
    # GCC Regulatory Compliance
    regulatory_authority = models.ForeignKey(RegulatoryAuthority, on_delete=models.SET_NULL, null=True, blank=True)
    license_required = models.CharField(max_length=200, blank=True, null=True, help_text="Specific license needed (e.g., KHDA App, Training & Consultancy)")
    data_residency_region = models.CharField(max_length=100, default='UAE', help_text="Region where learner data is hosted (e.g. UAE Region, Microsoft Azure UAE North)")
    is_child_safe = models.BooleanField(default=False, help_text="Compliant with UAE Child Digital Safety Law")
    min_age_requirement = models.PositiveIntegerField(default=0, help_text="Minimum age to enroll in this course")
    is_pdpl_compliant = models.BooleanField(default=True, help_text="Individual course compliance with UAE Data Protection Law")
    
    # Platform & Content Safety (Section 4 & 7)
    content_safety_checked = models.BooleanField(default=False, help_text="Proactively reviewed for harmful content")
    classification_tier = models.CharField(max_length=50, blank=True, null=True, help_text="National risk-based classification tier")
    drm_enabled = models.BooleanField(default=False, help_text="Digital Rights Management for premium content")
    watermarking_enabled = models.BooleanField(default=False, help_text="Visual watermarking for certificate fraud prevention")
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('mixed', 'Mixed'), ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),]

    TYPE_CHOICES = [
        ('training', 'Training'),
        ('accreditation', 'Accreditation'),
    ]

    MODE_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('hybrid', 'Hybrid'),
    ]
    
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    content = RichTextUploadingField(blank=True, null=True,)
    short_description = models.CharField(max_length=500)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    promo_video = models.URLField(blank=True)  # YouTube/Vimeo URL
    
    instructors = models.ManyToManyField(Instructor, related_name='courses')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='courses', null=True, blank=True)
    categories = models.ManyToManyField(Category, related_name='courses')
    
    course_type = models.CharField(max_length=20, null=True, blank=True, choices=TYPE_CHOICES, default='accreditation')
    delivery_mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='online')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    language = models.CharField(max_length=50, default='English')
    duration_weeks = models.PositiveIntegerField(help_text="Estimated duration in weeks", default=4)
    weekly_hours = models.PositiveIntegerField(help_text="Hours per week", default=5)
    
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='USD')
    has_certificate = models.BooleanField(default=True)
    
    is_approved = models.BooleanField(default=False)
    
    enrolled_students = models.PositiveIntegerField(default=0)
    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    review_count = models.PositiveIntegerField(default=0)
    
    featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Career Info (basic — richer data lives in JobRole M2M, see courses.models.job_role)
    job_opportunity = models.TextField(blank=True, null=True, help_text="Free-text job opportunity description")
    salary_range = models.CharField(max_length=100, blank=True, null=True, help_text="Headline salary range, e.g. $50k - $80k")

    # Compliance gating — when true, certificate issuance requires student docs to be approved
    require_student_compliance = models.BooleanField(default=False, help_text="Block certificate until student compliance docs are approved")

    # Certificate SLA in days post-completion (used for status reporting)
    certificate_sla_days = models.PositiveIntegerField(default=7)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
 
class Module(GeneralTimeStamp):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    content = RichTextUploadingField(blank=True, null=True,)
    order = models.PositiveIntegerField(default=0)
    duration_hours = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['order']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(GeneralTimeStamp):
    LESSON_TYPES = [
        ('video', 'Video'),
        ('reading', 'Reading'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('discussion', 'Discussion'),
    ]
    
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES)
    content = RichTextUploadingField(blank=True, null=True,)
    video_url = models.URLField(blank=True)
    video_duration = models.PositiveIntegerField(default=0, help_text="Duration in seconds")
    order = models.PositiveIntegerField(default=0)
    is_free = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order']
        unique_together = ['module', 'order']
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"


class CourseResource(GeneralTimeStamp):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='course_resources/')
    description = models.TextField(blank=True)
    content = RichTextUploadingField(blank=True, null=True,)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Discussion(GeneralTimeStamp):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='discussions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussions')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.student.username}"


class DiscussionReply(GeneralTimeStamp):
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name='replies')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Reply by {self.student.username} on {self.discussion.title}"