from django.conf import settings
from django.db import models

class Event(models.Model):
    VISIBILITY_CHOICES = [
        ("public", "Public"),
        ("friends", "Friends"),
        ("private", "Private"),
    ]

    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    location = models.CharField(max_length=140, blank=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default="public")

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start"]

    def __str__(self):
        return f"{self.title} ({self.start} → {self.end})"
