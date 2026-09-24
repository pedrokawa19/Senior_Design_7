"""Saved database settings: encryption, per-user isolation, and reuse."""

import json

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..credentials import decrypt_connection
from ..models import SavedConnection
from ..views.api import REVEAL_MAX_ATTEMPTS
from .support import ACCOUNT_PASSWORD, SYNTHETIC_CONNECTION, TEST_ENCRYPTION_KEY


@override_settings(CREDENTIAL_ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class SavedConnectionTests(TestCase):
    def setUp(self):
        # The reveal limiter uses a shared on-disk cache, so state must not leak.
        cache.clear()
        self.addCleanup(cache.clear)
        self.owner = User.objects.create_user("buyer-one", password=ACCOUNT_PASSWORD)
        self.other = User.objects.create_user("buyer-two", password=ACCOUNT_PASSWORD)
        self.client.force_login(self.owner)

    def save_connection(self, client=None, **overrides):
        payload = {**SYNTHETIC_CONNECTION, **overrides}
        return (client or self.client).post(
            reverse("connection"),
            data=json.dumps(payload),
            content_type="application/json",
        )

    def read_connection(self, client=None):
        return (client or self.client).get(reverse("connection")).json()["connection"]

    def test_credentials_are_encrypted_and_never_returned(self):
        response = self.save_connection()

        self.assertEqual(response.status_code, 200)
        body = response.json()["connection"]
        self.assertNotIn("password", body)
        self.assertTrue(body["has_password"])
        self.assertNotIn(SYNTHETIC_CONNECTION["password"], response.content.decode())

        stored = SavedConnection.objects.get(user=self.owner).encrypted_settings
        for secret in SYNTHETIC_CONNECTION.values():
            self.assertNotIn(str(secret), stored)

    def test_settings_stay_with_the_same_user_across_logout_and_login(self):
        self.save_connection()

        self.client.post(reverse("logout"))
        self.assertEqual(self.client.get(reverse("connection")).status_code, 401)

        self.client.login(username="buyer-one", password=ACCOUNT_PASSWORD)
        connection = self.read_connection()
        self.assertEqual(connection["database"], SYNTHETIC_CONNECTION["database"])
        self.assertEqual(connection["host"], SYNTHETIC_CONNECTION["host"])
        self.assertNotIn("password", connection)

    def test_one_user_cannot_read_overwrite_or_delete_another_users_settings(self):
        self.save_connection()

        intruder = Client()
        intruder.force_login(self.other)
        self.assertIsNone(self.read_connection(intruder))

        self.save_connection(client=intruder, database="second_catalog")
        self.assertEqual(self.read_connection()["database"], SYNTHETIC_CONNECTION["database"])

        intruder.delete(reverse("connection"))
        self.assertIsNotNone(self.read_connection())
        self.assertEqual(SavedConnection.objects.filter(user=self.owner).count(), 1)

    def test_ciphertext_copied_from_another_account_is_rejected(self):
        self.save_connection()
        stolen = SavedConnection.objects.get(user=self.owner).encrypted_settings
        SavedConnection.objects.create(user=self.other, encrypted_settings=stolen)

        intruder = Client()
        intruder.force_login(self.other)

        self.assertEqual(intruder.get(reverse("connection")).status_code, 503)

    def test_saving_without_a_password_reuses_the_stored_password(self):
        self.save_connection()

        response = self.client.post(
            reverse("connection"),
            data=json.dumps(
                {
                    "user": SYNTHETIC_CONNECTION["user"],
                    "host": "updated.synthetic.invalid",
                    "port": SYNTHETIC_CONNECTION["port"],
                    "database": SYNTHETIC_CONNECTION["database"],
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        stored = decrypt_connection(
            self.owner.id, SavedConnection.objects.get(user=self.owner).encrypted_settings
        )
        self.assertEqual(stored["password"], SYNTHETIC_CONNECTION["password"])
        self.assertEqual(stored["host"], "updated.synthetic.invalid")

    def test_a_new_connection_requires_a_password(self):
        response = self.client.post(
            reverse("connection"),
            data=json.dumps(
                {
                    "user": SYNTHETIC_CONNECTION["user"],
                    "host": SYNTHETIC_CONNECTION["host"],
                    "port": SYNTHETIC_CONNECTION["port"],
                    "database": SYNTHETIC_CONNECTION["database"],
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(SavedConnection.objects.filter(user=self.owner).exists())

    def test_invalid_settings_do_not_echo_the_password(self):
        response = self.save_connection(port=0)

        self.assertEqual(response.status_code, 400)
        self.assertNotIn(SYNTHETIC_CONNECTION["password"], response.content.decode())

    def test_removing_the_connection_clears_stored_credentials(self):
        self.save_connection()

        response = self.client.delete(reverse("connection"))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["connection"])
        self.assertFalse(SavedConnection.objects.filter(user=self.owner).exists())

    def test_profitability_requires_a_saved_connection(self):
        response = self.client.get(reverse("profitable-products"))

        self.assertEqual(response.status_code, 409)

    def test_api_endpoints_require_authentication(self):
        anonymous = Client()

        self.assertEqual(anonymous.get(reverse("connection")).status_code, 401)
        self.assertEqual(anonymous.delete(reverse("connection")).status_code, 401)
        self.assertEqual(anonymous.post(reverse("verify-database")).status_code, 401)
        self.assertEqual(anonymous.post(reverse("connection-password")).status_code, 401)
        self.assertEqual(anonymous.get(reverse("profitable-products")).status_code, 401)
        self.assertEqual(anonymous.get(reverse("index-performance")).status_code, 401)

    def reveal_password(self, account_password, client=None):
        return (client or self.client).post(
            reverse("connection-password"),
            data=json.dumps({"account_password": account_password}),
            content_type="application/json",
        )

    def test_revealing_the_database_password_requires_the_account_password(self):
        self.save_connection()

        response = self.reveal_password(ACCOUNT_PASSWORD)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["password"], SYNTHETIC_CONNECTION["password"])
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_a_wrong_account_password_does_not_reveal_anything(self):
        self.save_connection()

        response = self.reveal_password("WrongPassword789")

        self.assertEqual(response.status_code, 403)
        self.assertNotIn(SYNTHETIC_CONNECTION["password"], response.content.decode())

    def test_an_empty_account_password_does_not_reveal_anything(self):
        self.save_connection()

        response = self.reveal_password("")

        self.assertEqual(response.status_code, 403)
        self.assertNotIn(SYNTHETIC_CONNECTION["password"], response.content.decode())

    def test_another_user_cannot_reveal_the_owners_database_password(self):
        self.save_connection()

        intruder = Client()
        intruder.force_login(self.other)
        response = self.reveal_password(ACCOUNT_PASSWORD, client=intruder)

        self.assertEqual(response.status_code, 409)
        self.assertNotIn(SYNTHETIC_CONNECTION["password"], response.content.decode())

    @override_settings(CREDENTIAL_ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
    def test_reveal_requires_a_saved_connection(self):
        response = self.reveal_password(ACCOUNT_PASSWORD)

        self.assertEqual(response.status_code, 409)

    def test_repeated_wrong_passwords_lock_out_the_reveal(self):
        self.save_connection()

        for _ in range(REVEAL_MAX_ATTEMPTS):
            self.assertEqual(self.reveal_password("WrongPassword789").status_code, 403)

        locked_out = self.reveal_password("WrongPassword789")
        self.assertEqual(locked_out.status_code, 429)

        # The correct password is refused too, so guessing cannot be outlasted.
        still_locked = self.reveal_password(ACCOUNT_PASSWORD)
        self.assertEqual(still_locked.status_code, 429)
        self.assertNotIn(SYNTHETIC_CONNECTION["password"], still_locked.content.decode())

    def test_a_successful_reveal_clears_earlier_failures(self):
        self.save_connection()

        self.assertEqual(self.reveal_password("WrongPassword789").status_code, 403)
        self.assertEqual(self.reveal_password(ACCOUNT_PASSWORD).status_code, 200)

        for _ in range(REVEAL_MAX_ATTEMPTS):
            self.assertEqual(self.reveal_password("WrongPassword789").status_code, 403)

    def test_one_users_lockout_does_not_affect_another(self):
        self.save_connection()
        for _ in range(REVEAL_MAX_ATTEMPTS):
            self.reveal_password("WrongPassword789")

        neighbour = Client()
        neighbour.force_login(self.other)

        # Locked out owner, but the other account is only blocked by having no connection.
        self.assertEqual(self.reveal_password(ACCOUNT_PASSWORD).status_code, 429)
        self.assertEqual(self.reveal_password(ACCOUNT_PASSWORD, client=neighbour).status_code, 409)

    @override_settings(CREDENTIAL_ENCRYPTION_KEY="")
    def test_credential_storage_fails_closed_without_a_key(self):
        response = self.save_connection()

        self.assertEqual(response.status_code, 503)
        self.assertNotIn(SYNTHETIC_CONNECTION["password"], response.content.decode())
        self.assertFalse(SavedConnection.objects.filter(user=self.owner).exists())
