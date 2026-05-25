from django.db import models
from django.contrib.auth import get_user_model
from courses.models.base import GeneralTimeStamp
from courses.models.enrollment import Enrollment
from courses.models.instructor import Instructor

User = get_user_model()

class Certificate(GeneralTimeStamp):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='certificate')
    certificate_id = models.CharField(max_length=100, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    download_url = models.URLField(blank=True)
    pdf_file = models.FileField(upload_to='certificates/', null=True, blank=True)

    # GCC Compliance Fields
    expiry_date = models.DateField(null=True, blank=True)
    is_revoked = models.BooleanField(default=False)
    revocation_reason = models.TextField(blank=True, null=True)
    issued_by = models.ForeignKey('courses.RegulatoryAuthority', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Certificate {self.certificate_id} for {self.enrollment.student.username}"


class CertificateTemplate(GeneralTimeStamp):
    """A reusable PDF template a trainer uploads once and can then
    attach to any of their courses. When a learner completes the course
    we render this template (with the learner's name + course + date)
    and store the result on the Certificate row.

    For now the workflow is "manual" — the trainer uploads a PDF, sets
    it as the default for a course, and uses it via the issue flow.
    Later iterations can add per-field overlay positions.
    """
    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('published', 'Published'),
    ]

    instructor = models.ForeignKey(
        Instructor, on_delete=models.CASCADE,
        related_name='certificate_templates',
    )
    title    = models.CharField(max_length=200)
    file     = models.FileField(upload_to='certificate_templates/')
    preview  = models.ImageField(upload_to='certificate_templates/previews/', blank=True, null=True)
    status   = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_default = models.BooleanField(default=False, help_text="Use as default for new courses by this trainer")
    courses  = models.ManyToManyField('courses.Course', blank=True, related_name='certificate_templates')
    notes    = models.TextField(blank=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.title} ({self.instructor.user.username})"
