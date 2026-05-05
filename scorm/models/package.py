"""
SCORM Package, Module, and SCO (Sharable Content Object) Models
Represents the hierarchical structure and content of SCORM courses
"""
import json
from django.db import models
from django.core.validators import FileExtensionValidator
from .base import GeneralTimeStamp


class ScormPackage(GeneralTimeStamp):
    """
    Main SCORM package (course container)
    Represents an uploaded .zip file containing SCORM content
    """
    SCORM_VERSIONS = [
        ('1.2', 'SCORM 1.2'),
        ('2004', 'SCORM 2004 4th Edition'),
        ('unknown', 'Unknown Version'),
    ]

    STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('error', 'Error'),
        ('archived', 'Archived'),
    ]

    # Basic info
    title = models.CharField(max_length=255, help_text="SCORM package title")
    description = models.TextField(blank=True, null=True)
    version = models.CharField(
        max_length=10,
        choices=SCORM_VERSIONS,
        default='unknown',
        help_text="Detected SCORM version from manifest"
    )

    # Package metadata
    upload_file = models.FileField(
        upload_to='scorm_packages/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['zip'])],
        help_text="Original .zip file"
    )
    file_size = models.BigIntegerField(help_text="Size in bytes")

    # Structure & organization
    entry_point = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Launch URL from imsmanifest.xml"
    )
    structure_tree = models.JSONField(
        default=dict,
        help_text="Hierarchical organization structure"
    )
    manifest_data = models.JSONField(
        default=dict,
        help_text="Parsed imsmanifest.xml content"
    )

    # Status & processing
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploading'
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error details if processing failed"
    )
    processing_task_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Celery task ID for async processing"
    )

    # Statistics
    total_scos = models.IntegerField(
        default=0,
        help_text="Total SCOs (launchable units)"
    )
    total_modules = models.IntegerField(
        default=0,
        help_text="Total modules in organization"
    )
    language = models.CharField(
        max_length=10,
        default='en',
        help_text="Primary language of content"
    )

    # Publishing & control
    published_at = models.DateTimeField(blank=True, null=True)
    enrolled_users = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'SCORM Package'
        verbose_name_plural = 'SCORM Packages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['version']),
        ]

    def __str__(self):
        return f"{self.title} ({self.version})"

    def mark_ready(self):
        """Mark package as ready after successful processing"""
        self.status = 'ready'
        self.error_message = None
        self.published_at = models.functions.Now()
        self.save()

    def mark_error(self, error_msg):
        """Mark package with error"""
        self.status = 'error'
        self.error_message = error_msg
        self.save()


class ScormModule(GeneralTimeStamp):
    """
    Organization structure within SCORM package
    Represents modules/chapters in the course hierarchy
    """
    package = models.ForeignKey(
        ScormPackage,
        on_delete=models.CASCADE,
        related_name='modules'
    )

    # Hierarchy
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    # Content
    identifier = models.CharField(
        max_length=255,
        help_text="Unique identifier from manifest"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    # Order and visibility
    order = models.IntegerField(default=0)
    visible = models.BooleanField(default=True)

    # Metadata
    launch = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Launch URL for this module (if directly launchable)"
    )
    resource_ref = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Reference to resource in manifest"
    )

    class Meta:
        verbose_name = 'SCORM Module'
        verbose_name_plural = 'SCORM Modules'
        unique_together = [['package', 'identifier']]
        ordering = ['order']
        indexes = [
            models.Index(fields=['package', 'parent']),
            models.Index(fields=['package', 'order']),
        ]

    def __str__(self):
        return f"{self.title} ({self.package.title})"

    @property
    def depth(self):
        """Calculate depth in hierarchy"""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth


class ScormSco(GeneralTimeStamp):
    """
    Sharable Content Object - actual launchable learning content
    Represents the leaf nodes in SCORM hierarchy
    """
    package = models.ForeignKey(
        ScormPackage,
        on_delete=models.CASCADE,
        related_name='scos'
    )
    module = models.ForeignKey(
        ScormModule,
        on_delete=models.CASCADE,
        related_name='scos'
    )

    # Identity
    identifier = models.CharField(
        max_length=255,
        help_text="Unique identifier from manifest"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    # Launch configuration
    launch_url = models.CharField(
        max_length=1000,
        help_text="Relative path to launchable HTML/SCO"
    )
    resource_type = models.CharField(
        max_length=50,
        default='webcontent',
        help_text="Type of resource (webcontent, asset, etc.)"
    )

    # SCO type (SCORM distinguishes between SCO and Asset)
    is_asset = models.BooleanField(
        default=False,
        help_text="True if asset (no API), False if SCO (uses API)"
    )

    # Content specifications
    max_time_allowed = models.DurationField(
        null=True,
        blank=True,
        help_text="Max time allowed to complete"
    )
    score_max = models.IntegerField(
        default=100,
        help_text="Maximum achievable score"
    )
    score_min = models.IntegerField(
        default=0,
        help_text="Minimum score"
    )

    # Order and visibility
    order = models.IntegerField(default=0)
    visible = models.BooleanField(default=True)
    required = models.BooleanField(
        default=False,
        help_text="Must complete to finish module"
    )

    class Meta:
        verbose_name = 'SCORM SCO'
        verbose_name_plural = 'SCORM SCOs'
        unique_together = [['package', 'identifier']]
        ordering = ['order']
        indexes = [
            models.Index(fields=['package', 'module']),
            models.Index(fields=['module', 'order']),
        ]

    def __str__(self):
        return f"{self.title} ({self.package.title})"
