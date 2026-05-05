"""
Base model for SCORM app following project conventions
"""
from django.db import models


class GeneralTimeStamp(models.Model):
    """Abstract base model with common timestamp and lifecycle fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
