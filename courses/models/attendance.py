from django.db import models
from django.conf import settings
from courses.models.base import GeneralTimeStamp
from courses.models.live_session import LiveSession

class SessionAttendance(GeneralTimeStamp):
    session = models.ForeignKey(LiveSession, on_delete=models.CASCADE, null=True, blank=True, related_name='attendance_records')
    slot = models.ForeignKey('courses.Slot', on_delete=models.CASCADE, null=True, blank=True, related_name='attendance_records')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='session_attendance')
    join_time = models.DateTimeField(auto_now_add=True)
    leave_time = models.DateTimeField(null=True, blank=True)

    # Offline attendance fields
    check_in_time = models.DateTimeField(null=True, blank=True, help_text='Physical check-in for offline sessions')
    check_out_time = models.DateTimeField(null=True, blank=True)
    marked_by_instructor = models.BooleanField(default=False, help_text='True when an instructor manually marked attendance')

    is_present = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-join_time']

    def __str__(self):
        target = self.session or self.slot
        return f"{self.student} - {target}"
