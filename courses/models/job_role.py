from django.db import models
from courses.models.base import GeneralTimeStamp
from courses.models.course import Course


class JobRole(GeneralTimeStamp):
    """Job roles that a course prepares learners for, with indicative salary info."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='USD')
    salary_period = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')],
        default='yearly',
    )
    region = models.CharField(max_length=100, blank=True, help_text='Region this salary range applies to')
    courses = models.ManyToManyField(Course, related_name='job_roles', blank=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

    @property
    def salary_range_display(self):
        if self.salary_min and self.salary_max:
            return f"{self.salary_currency} {self.salary_min:,.0f} – {self.salary_max:,.0f} / {self.salary_period}"
        return ""
