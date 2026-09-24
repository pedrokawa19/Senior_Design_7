"""Storage for each user's saved MySQL settings.

Settings are encrypted before they are written and decrypted on read, so the
database never holds a usable credential.
"""

from ..credentials import (
    ConnectionNotConfigured,
    decrypt_connection,
    encrypt_connection,
)
from ..models import SavedConnection


def load_connection(user):
    """Return the user's decrypted settings, or None when nothing is saved."""
    saved = SavedConnection.objects.filter(user=user).first()
    if saved is None:
        return None
    return decrypt_connection(user.id, saved.encrypted_settings)


def require_connection(user):
    connection = load_connection(user)
    if connection is None:
        raise ConnectionNotConfigured("Save your database settings before loading this data.")
    return connection


def save_connection(user, submitted):
    """Store validated settings, returning None when no password is available.

    An empty password means "keep the one already saved", so an existing
    connection can be edited without retyping the credential.
    """
    password = submitted["password"] or (load_connection(user) or {}).get("password", "")
    if not password:
        return None

    settings = {
        "user": submitted["user"],
        "password": password,
        "host": submitted["host"],
        "port": submitted["port"],
        "database": submitted["database"],
    }
    SavedConnection.objects.update_or_create(
        user=user,
        defaults={"encrypted_settings": encrypt_connection(user.id, settings)},
    )
    return settings


def delete_connection(user):
    SavedConnection.objects.filter(user=user).delete()
