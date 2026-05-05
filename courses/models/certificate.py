from django.db import models
from django.contrib.auth import get_user_model
from courses.models.base import GeneralTimeStamp
from courses.models.enrollment import Enrollment

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
    