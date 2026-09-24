"""Shared test values. Every credential here is synthetic and unroutable."""

from cryptography.fernet import Fernet

TEST_ENCRYPTION_KEY = Fernet.generate_key().decode()
ACCOUNT_PASSWORD = "SyntheticPass123"

SYNTHETIC_CONNECTION = {
    "user": "synthetic_reader",
    "password": "SyntheticDatabasePass1",
    "host": "database.synthetic.invalid",
    "port": 3306,
    "database": "synthetic_catalog",
}

NAV_TABS = ["dashboard", "auction", "history", "inventory", "model", "profile"]
PROTECTED_PAGES = NAV_TABS + ["history-purchases", "history-sales"]
