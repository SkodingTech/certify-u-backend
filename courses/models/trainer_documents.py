from django.db import models
from django.conf import settings
from courses.models.base import GeneralTimeStamp
from courses.models.instructor import Instructor


class TrainerDocument(GeneralTimeStamp):
    """Onboarding documents uploaded by a trainer/institution for verification."""
    DOCUMENT_TYPES = [
        ('trade_license', 'Trade License'),
        ('vat_certificate', 'VAT Certificate'),
        ('accreditation', 'Accreditation Certificate'),
        ('id_proof', 'ID Proof'),
        ('cv', 'Curriculum Vitae'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('resubmit', 'Resubmission Requested'),
        ('expired', 'Expired'),
    ]

    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='trainer_docs/')
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    review_notes = models.TextField(blank=True, help_text='Reviewer notes / rejection reason')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_trainer_docs',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.instructor} - {self.get_document_type_display()} ({self.status})"


class StudentDocument(GeneralTimeStamp):
    """Identity / compliance documents uploaded by a learner."""
    DOCUMENT_TYPES = [
        ('id_proof', 'ID Proof'),
        ('passport', 'Passport'),
        ('emirates_id', 'Emirates ID'),
        ('photo', 'Photograph'),
        ('parental_consent', 'Parental Consent'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('resubmit', 'Resubmission Requested'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='compliance_documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to='student_docs/')
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_student_docs',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student} - {self.get_document_type_display()} ({self.status})"
