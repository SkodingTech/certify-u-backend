"""
SCORM Tracking and Runtime Data Models
Tracks user progress, CMI data, and session state
"""
from django.db import models
from django.contrib.auth.models import User
from .base import GeneralTimeStamp
from .package import ScormPackage, ScormSco


class ScormTracking(GeneralTimeStamp):
    """
    Main tracking record for user progress through a SCORM package
    Stores aggregated completion status and scores
    """
    LESSON_STATUS_CHOICES = [
        ('passed', 'Passed'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('incomplete', 'Incomplete'),
        ('browsed', 'Browsed'),
        ('not attempted', 'Not Attempted'),
    ]

    # User and content references
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey(ScormPackage, on_delete=models.CASCADE)
    sco = models.ForeignKey(
        ScormSco,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Current SCO being tracked"
    )

    # Session management
    session_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique session identifier"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of learner"
    )

    # Completion tracking
    lesson_status = models.CharField(
        max_length=20,
        choices=LESSON_STATUS_CHOICES,
        default='not attempted'
    )
    entry_status = models.CharField(
        max_length=20,
        choices=[('ab-initio', 'First attempt'), ('resume', 'Resumed')],
        default='ab-initio'
    )

    # Scoring
    score_raw = models.IntegerField(
        null=True,
        blank=True,
        help_text="Actual score achieved"
    )
    score_scaled = models.FloatField(
        null=True,
        blank=True,
        help_text="Normalized score (0-1)"
    )
    score_min = models.IntegerField(default=0)
    score_max = models.IntegerField(default=100)

    # Time tracking
    time_spent = models.DurationField(
        null=True,
        blank=True,
        help_text="Total time spent in ISO 8601 format"
    )
    first_access = models.DateTimeField(auto_now_add=True)
    last_access = models.DateTimeField(auto_now=True)
    completion_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user marked as complete"
    )

    # Resume point
    suspend_data = models.TextField(
        blank=True,
        null=True,
        help_text="Serialized state for resume (JSON)"
    )
    bookmark = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Lesson location/bookmark for resume"
    )

    # Metadata
    attempt_number = models.IntegerField(default=1)
    is_passed = models.BooleanField(default=False)
    total_attempts = models.IntegerField(default=1)

    # Platform info
    launch_data = models.JSONField(
        default=dict,
        help_text="Initialization data passed to SCO"
    )

    class Meta:
        verbose_name = 'SCORM Tracking'
        verbose_name_plural = 'SCORM Tracking Records'
        unique_together = [['user', 'package', 'sco', 'attempt_number']]
        ordering = ['-last_access']
        indexes = [
            models.Index(fields=['user', 'package']),
            models.Index(fields=['user', 'lesson_status']),
            models.Index(fields=['session_id']),
            models.Index(fields=['-last_access']),
        ]

    def __str__(self):
        return f"{self.user} → {self.package.title} ({self.lesson_status})"

    def mark_complete(self, score=None):
        """Mark tracking record as completed"""
        self.lesson_status = 'completed'
        self.is_passed = True
        if score is not None:
            self.score_raw = score
        self.completion_date = models.functions.Now()
        self.save()

    def mark_failed(self, score=None):
        """Mark tracking record as failed"""
        self.lesson_status = 'failed'
        self.is_passed = False
        if score is not None:
            self.score_raw = score
        self.completion_date = models.functions.Now()
        self.save()

    def get_suspend_data(self):
        """Get suspend data as Python object"""
        if self.suspend_data:
            import json
            try:
                return json.loads(self.suspend_data)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_suspend_data(self, data):
        """Set suspend data from Python object"""
        import json
        self.suspend_data = json.dumps(data)


class ScormRuntimeData(GeneralTimeStamp):
    """
    Key-value store for CMI (Computer Managed Instruction) data
    Flexible storage for all SCORM CMI elements during runtime
    """
    tracking = models.ForeignKey(
        ScormTracking,
        on_delete=models.CASCADE,
        related_name='runtime_data'
    )

    # CMI element path and value
    element = models.CharField(
        max_length=500,
        help_text="CMI element path (e.g., 'cmi.score.raw')"
    )
    value = models.TextField(
        help_text="Element value (can be JSON for complex types)"
    )

    # Tracking change
    commit_count = models.IntegerField(
        default=0,
        help_text="Number of commits for this element"
    )
    last_committed = models.DateTimeField(
        auto_now=True,
        help_text="Last time this element was committed"
    )

    class Meta:
        verbose_name = 'SCORM Runtime Data'
        verbose_name_plural = 'SCORM Runtime Data'
        unique_together = [['tracking', 'element']]
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['tracking', 'element']),
            models.Index(fields=['tracking', '-updated_at']),
        ]

    def __str__(self):
        return f"{self.tracking.session_id} → {self.element}"

    @staticmethod
    def set_value(tracking, element, value):
        """Create or update CMI element value"""
        obj, created = ScormRuntimeData.objects.update_or_create(
            tracking=tracking,
            element=element,
            defaults={'value': str(value)}
        )
        return obj

    @staticmethod
    def get_value(tracking, element):
        """Get CMI element value"""
        try:
            obj = ScormRuntimeData.objects.get(
                tracking=tracking,
                element=element
            )
            return obj.value
        except ScormRuntimeData.DoesNotExist:
            return None

    @staticmethod
    def get_all_values(tracking):
        """Get all CMI values for a tracking record as dict"""
        data = {}
        for item in ScormRuntimeData.objects.filter(tracking=tracking):
            data[item.element] = item.value
        return data


class ScormAttempt(GeneralTimeStamp):
    """
    Individual attempt record for a SCORM package by a user
    Tracks multiple attempts and their outcomes
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey(ScormPackage, on_delete=models.CASCADE)

    # Attempt info
    attempt_number = models.IntegerField()
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(
        null=True,
        blank=True,
        help_text="Total duration of attempt"
    )

    # Results
    completion_status = models.CharField(
        max_length=20,
        choices=[
            ('completed', 'Completed'),
            ('incomplete', 'Incomplete'),
            ('not_attempted', 'Not Attempted'),
        ],
        default='not_attempted'
    )
    success_status = models.CharField(
        max_length=20,
        choices=[
            ('passed', 'Passed'),
            ('failed', 'Failed'),
            ('unknown', 'Unknown'),
        ],
        default='unknown'
    )
    score_scaled = models.FloatField(null=True, blank=True)
    total_time = models.CharField(
        max_length=50,
        blank=True,
        help_text="ISO 8601 total time"
    )

    # Session reference
    session_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Links to ScormTracking.session_id"
    )

    class Meta:
        verbose_name = 'SCORM Attempt'
        verbose_name_plural = 'SCORM Attempts'
        unique_together = [['user', 'package', 'attempt_number']]
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['user', 'package']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"{self.user} - Attempt {self.attempt_number} ({self.success_status})"
