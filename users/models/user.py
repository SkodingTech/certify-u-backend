import hashlib

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from users.models.base import GeneralTimeStamp
from django.contrib.auth import get_user_model

User = get_user_model()

from django.core.exceptions import ValidationError

def validate_image_size(image):
    file_size = image.size
    limit_mb = 2
    if file_size > limit_mb * 1024 * 1024:
        raise ValidationError(f"Max size of file is {limit_mb}MB")


def validate_document_size(document):
    file_size = document.size
    limit_mb = 5
    if file_size > limit_mb * 1024 * 1024:
        raise ValidationError(f"Max size of file is {limit_mb}MB")

class UserProfile(GeneralTimeStamp):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        ADMIN = "ADMIN", "Admin"
        TEAM_MANAGER = "TEAM_MANAGER", "Team Manager"
        INSTRUCTOR = "INSTRUCTOR", "Instructor"
        STUDENT = "STUDENT", "Student"
    base_role = Role.STUDENT
    role = models.CharField(max_length=50, choices=Role.choices)    
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    image = models.ImageField(upload_to='image/', blank=True, null=True, validators=[validate_image_size])
    banner = models.ImageField(upload_to='banners/', blank=True, null=True, validators=[validate_image_size])
    
    # GCC Compliance Fields
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True, null=True, help_text="User's country of residence")
    nationality = models.CharField(max_length=100, blank=True, null=True)
    identity_id = models.CharField(max_length=50, blank=True, null=True, help_text="Emirates ID or Passport Number")
    
    # PDPL Compliance
    data_processing_consent = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)
    
    # Child Safety Law Compliance (Federal Decree-Law No. 26 of 2025)
    parental_consent_given = models.BooleanField(default=False)
    guardian_name = models.CharField(max_length=200, blank=True, null=True)
    guardian_contact = models.CharField(max_length=100, blank=True, null=True)
    
    # Technical & Security (Section 7 & Privacy by Design)
    mfa_enabled = models.BooleanField(default=False, help_text="Multi-Factor Authentication status")
    high_privacy_enabled = models.BooleanField(default=True, help_text="Default privacy settings set to high (Privacy by Design)")
    exclude_from_advertising = models.BooleanField(default=True, help_text="No targeted advertising or profiling for this user")
    
    def save(self, *args, **kwargs):
        if not self.pk and not self.role:
            self.role = self.base_role
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} ({self.role})"


class InstructorProfile(GeneralTimeStamp):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    bio = models.TextField()
    profile_picture = models.ImageField(upload_to='instructors/', null=True, blank=True, validators=[validate_image_size])
    banner = models.ImageField(upload_to='instructor_banners/', null=True, blank=True, validators=[validate_image_size])
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    x_link = models.URLField(blank=True)

    # Trainer onboarding documents (company / compliance docs).
    vat_certificate = models.FileField(upload_to='instructor_docs/vat/', null=True, blank=True, validators=[validate_document_size])
    trade_license = models.FileField(upload_to='instructor_docs/trade_license/', null=True, blank=True, validators=[validate_document_size])
    trainer_eid = models.FileField(upload_to='instructor_docs/eid/', null=True, blank=True, validators=[validate_document_size])
    resume = models.FileField(upload_to='instructor_docs/resume/', null=True, blank=True, validators=[validate_document_size])
    qualification = models.FileField(upload_to='instructor_docs/qualification/', null=True, blank=True, validators=[validate_document_size])

    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Instructor: {self.user.username}"


class StudentProfile(GeneralTimeStamp):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    meta_data = models.JSONField(blank=True, null=True)
    banner = models.ImageField(upload_to='student_banners/', null=True, blank=True, validators=[validate_image_size])
    
    # GCC Data Categories (Employment, Accessibility, AI)
    job_title = models.CharField(max_length=200, blank=True, null=True)
    employer_name = models.CharField(max_length=200, blank=True, null=True)
    accessibility_requirements = models.TextField(blank=True, null=True, help_text="Health/Accessibility info for accommodations")
    ai_personalization_consent = models.BooleanField(default=False, help_text="Consent for AI/Adaptive learning personalization")
    def __str__(self):
        return f"Student: {self.user.username}"


class PasswordResetOTP(GeneralTimeStamp):
    """One-time code emailed to a user to reset a forgotten password.

    The plaintext OTP is NEVER stored — only a SHA-256 hash. Records are
    single-use and expire after a short TTL (see settings
    PASSWORD_RESET_OTP_TTL_MINUTES).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_otps')
    email = models.EmailField()
    otp_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['email', 'is_used']),
        ]

    @staticmethod
    def hash_otp(otp):
        return hashlib.sha256(str(otp).strip().encode('utf-8')).hexdigest()

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"PasswordResetOTP({self.email}, used={self.is_used})"
