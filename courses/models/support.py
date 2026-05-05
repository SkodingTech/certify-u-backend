from django.db import models
from django.conf import settings
from courses.models.base import GeneralTimeStamp


class SupportChannel(GeneralTimeStamp):
    """Configurable customer-support channels (WhatsApp, phone, email, chatbot)."""
    CHANNEL_TYPES = [
        ('whatsapp', 'WhatsApp'),
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('chatbot', 'Chatbot'),
        ('telegram', 'Telegram'),
    ]
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    label = models.CharField(max_length=100)
    value = models.CharField(max_length=255, help_text='Phone number, email address, or URL')
    business_hours = models.CharField(max_length=200, blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['channel_type']

    def __str__(self):
        return f"{self.get_channel_type_display()}: {self.value}"


class SupportTicket(GeneralTimeStamp):
    """Inbound customer-support requests captured via WhatsApp webhook or web form."""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    SOURCE_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('web', 'Web Form'),
        ('email', 'Email'),
        ('chatbot', 'Chatbot'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='support_tickets',
    )
    name = models.CharField(max_length=200, blank=True)
    contact = models.CharField(max_length=200, help_text='Phone, email, or external user id')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='web')
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_tickets',
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.id} {self.subject or self.message[:40]}"
