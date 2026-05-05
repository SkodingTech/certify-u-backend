from django.db import models
from django.contrib.auth import get_user_model
from courses.models.base import GeneralTimeStamp
from django.utils.text import slugify

User = get_user_model()

class Category(GeneralTimeStamp):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    icon = models.CharField(max_length=50, blank=True)  # For icon class names
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name