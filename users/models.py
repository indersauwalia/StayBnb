from django.conf import settings
from django.db import models


class Profile(models.Model):
    GUEST = "guest"
    HOST = "host"
    ROLE_CHOICES = [(GUEST, "Guest"), (HOST, "Host")]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=GUEST)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
