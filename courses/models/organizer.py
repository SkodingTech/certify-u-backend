from django.db import models
from django.contrib.auth import get_user_model
from courses.models.base import GeneralTimeStamp

User = get_user_model()

class Organization(GeneralTimeStamp):
    name = models.CharField(max_length=200)
    description = models.TextField()
    logo = models.ImageField(upload_to='organizations/', null=True, blank=True)
    website = models.URLField(blank=True)
    established_date = models.DateField(null=True, blank=True)
    
    # GCC & PDPL Compliance
    dpo_name = models.CharField(max_length=200, blank=True, null=True, help_text="Data Protection Officer Name")
    dpo_contact = models.EmailField(blank=True, null=True, help_text="DPO Contact Email")
    license_number = models.CharField(max_length=200, blank=True, null=True, help_text="E-Commerce / Training License Number")
    regulatory_body = models.ForeignKey('courses.RegulatoryAuthority', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
    
    def __str__(self):
        return self.name
    