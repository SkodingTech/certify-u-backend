from django.db import models
from courses.models.base import GeneralTimeStamp

class RegulatoryAuthority(GeneralTimeStamp):
    name = models.CharField(max_length=200, help_text="e.g. KHDA, ADEK, CAA, MOE")
    country = models.CharField(max_length=100, default='UAE')
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    scope = models.TextField(blank=True, help_text="Scope of e-learning platforms authority")

    class Meta:
        verbose_name_plural = "Regulatory Authorities"

    def __str__(self):
        return f"{self.name} ({self.country})"

class RegulatoryCompliance(GeneralTimeStamp):
    """
    Model to track compliance with various regulations
    """
    REGULATION_TYPES = [
        ('PDPL', 'UAE Data Protection Law'),
        ('CDSL', 'UAE Child Digital Safety Law'),
        ('ECC', 'E-Commerce Law'),
        ('KSA_PDPL', 'Saudi Personal Data Protection Law'),
        ('BAHRAIN_PDPL', 'Bahrain PDPL'),
        ('QATAR_PDPL', 'Qatar PDPL'),
        ('OMAN_PDPL', 'Oman PDPL'),
        ('KUWAIT_DPPR', 'Kuwait DPPR'),
        ('GCC_SPECIFIC', 'GCC Specific Regulation'),
    ]

    title = models.CharField(max_length=200)
    regulation_type = models.CharField(max_length=50, choices=REGULATION_TYPES)
    description = models.TextField()
    is_mandatory = models.BooleanField(default=True)
    last_updated = models.DateField(auto_now=True)
    reference_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title

class RegulatoryReference(GeneralTimeStamp):
    """
    Model to store key reference sources from the GCC regulations guide.
    """
    source_name = models.CharField(max_length=200)
    url = models.URLField(unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.source_name

class ComplianceDocument(GeneralTimeStamp):
    """
    Model to track executable compliance documents like DPAs, 
    Breach Response Plans, and Audit Reports.
    """
    DOCUMENT_TYPES = [
        ('DPA', 'Data Processing Agreement'),
        ('BREACH_PLAN', 'Breach Response Plan'),
        ('COOKIE_POLICY', 'Cookie Policy'),
        ('PRIVACY_POLICY', 'Privacy Policy'),
        ('T_AND_C', 'Terms & Conditions'),
        ('AUDIT_REPORT', 'Security Audit Report'),
        ('PEN_TEST', 'Penetration Test Report'),
    ]
    
    organization = models.ForeignKey('courses.Organization', on_delete=models.CASCADE, related_name='compliance_documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='compliance_docs/')
    version = models.CharField(max_length=20, default='1.0')
    is_active = models.BooleanField(default=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.organization.name} - {self.get_document_type_display()} ({self.version})"
