from django.conf import settings
from django.db import models


class SavedConnection(models.Model):
    """Per-user MySQL connection settings, encrypted at rest."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_connection",
    )
    encrypted_settings = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Saved connection for {self.user.username}"
