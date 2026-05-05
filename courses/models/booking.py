from django.db import models
from django.conf import settings
from courses.models.base import GeneralTimeStamp
from courses.models.course import Course
from courses.models.instructor import Instructor


class TrainerAvailability(GeneralTimeStamp):
    """Recurring weekly availability windows for a trainer."""
    DAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='availability_windows')
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    timezone = models.CharField(max_length=50, default='UTC')

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.instructor} {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class Slot(GeneralTimeStamp):
    """A concrete bookable time slot for a course session."""
    MODE_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('one_on_one', 'One-on-One'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('full', 'Full'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='slots')
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='slots')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='offline')
    location = models.CharField(max_length=255, blank=True, help_text='Physical address (offline) or meeting link (online)')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=1)
    seats_taken = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['start_time']

    @property
    def seats_remaining(self):
        return max(self.capacity - self.seats_taken, 0)

    def __str__(self):
        return f"{self.course.title} @ {self.start_time:%Y-%m-%d %H:%M} ({self.mode})"


class Booking(GeneralTimeStamp):
    """A learner's reservation against a Slot."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('attended', 'Attended'),
        ('no_show', 'No Show'),
        ('cancelled', 'Cancelled'),
    ]

    slot = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name='bookings')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    booked_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        unique_together = ['slot', 'student']
        ordering = ['-booked_at']

    def __str__(self):
        return f"{self.student} -> {self.slot}"
