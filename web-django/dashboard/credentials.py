import json

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


class CredentialStorageUnavailable(Exception):
    """Raised when saved credentials cannot be encrypted or decrypted."""


class ConnectionNotConfigured(Exception):
    """Raised when the signed-in user has not saved a database connection."""


def _cipher() -> Fernet:
    key = settings.CREDENTIAL_ENCRYPTION_KEY
    if not key:
        raise CredentialStorageUnavailable(
            "Database settings are unavailable until CREDENTIAL_ENCRYPTION_KEY is configured."
        )
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError):
        raise CredentialStorageUnavailable(
            "Database settings are unavailable because CREDENTIAL_ENCRYPTION_KEY is invalid."
        ) from None


def encrypt_connection(user_id: int, connection: dict) -> str:
    payload = json.dumps({"user_id": user_id, "connection": connection})
    return _cipher().encrypt(payload.encode()).decode()


def decrypt_connection(user_id: int, token: str) -> dict:
    try:
        payload = json.loads(_cipher().decrypt(token.encode()))
    except (InvalidToken, ValueError, TypeError):
        raise CredentialStorageUnavailable(
            "The saved connection could not be unlocked with the current server key."
        ) from None

    # Reject ciphertext copied from another account.
    if payload.get("user_id") != user_id:
        raise CredentialStorageUnavailable("The saved connection does not belong to this account.")

    return payload["connection"]


def public_connection(connection: dict | None) -> dict | None:
    if connection is None:
        return None
    return {
        "host": connection["host"],
        "port": connection["port"],
        "database": connection["database"],
        "user": connection["user"],
        "has_password": True,
    }
