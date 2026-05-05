from django.db import models
from django.contrib.auth import get_user_model
from courses.models.base import GeneralTimeStamp

User = get_user_model()

class Instructor(GeneralTimeStamp):
    VERIFICATION_STATUS = [
        ('unsubmitted', 'Unsubmitted'),
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('resubmit', 'Resubmission Requested'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    bio = models.TextField()
    profile_picture = models.ImageField(upload_to='instructors/', null=True, blank=True)
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    x_link = models.URLField(blank=True)
    verified = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Onboarding & verification workflow
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='unsubmitted')
    verification_notes = models.TextField(blank=True, help_text='Admin feedback / rejection reason')
    accreditation_summary = models.TextField(blank=True, help_text='Public summary of credentials shown on profile')

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"
    