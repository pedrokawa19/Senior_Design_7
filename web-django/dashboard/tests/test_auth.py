"""Sign-up, log-in, log-out, and protection of every page."""

import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .support import ACCOUNT_PASSWORD, PROTECTED_PAGES, TEST_ENCRYPTION_KEY


@override_settings(CREDENTIAL_ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class AuthenticationTests(TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        override = override_settings(AUCTION_UPLOAD_DIR=Path(directory.name))
        override.enable()
        self.addCleanup(override.disable)

    def sign_up(self, username="buyer-one", password=ACCOUNT_PASSWORD, confirmation=None):
        return self.client.post(
            reverse("signup"),
            {
                "username": username,
                "password1": password,
                "password2": confirmation or password,
            },
        )

    def test_signup_creates_account_hashes_password_and_redirects(self):
        response = self.sign_up()

        self.assertRedirects(response, reverse("dashboard"))
        user = User.objects.get(username="buyer-one")
        self.assertNotEqual(user.password, ACCOUNT_PASSWORD)
        self.assertTrue(user.check_password(ACCOUNT_PASSWORD))

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user("buyer-one", password=ACCOUNT_PASSWORD)

        response = self.sign_up()

        self.assertEqual(response.status_code, 200)
        self.assertIn("username", response.context["signup_form"].errors)
        self.assertEqual(User.objects.filter(username="buyer-one").count(), 1)

    def test_mismatched_passwords_are_rejected(self):
        response = self.sign_up(confirmation="DifferentPass456")

        self.assertEqual(response.status_code, 200)
        self.assertIn("password2", response.context["signup_form"].errors)
        self.assertFalse(User.objects.filter(username="buyer-one").exists())

    def test_login_then_logout(self):
        User.objects.create_user("buyer-one", password=ACCOUNT_PASSWORD)

        login = self.client.post(
            reverse("login"), {"username": "buyer-one", "password": ACCOUNT_PASSWORD}
        )
        self.assertRedirects(login, reverse("dashboard"))
        self.assertTrue(self.client.get(reverse("dashboard")).wsgi_request.user.is_authenticated)

        logout = self.client.post(reverse("logout"))
        self.assertRedirects(logout, reverse("login"))
        self.assertFalse(self.client.get(reverse("login")).wsgi_request.user.is_authenticated)

    def test_invalid_login_is_rejected(self):
        User.objects.create_user("buyer-one", password=ACCOUNT_PASSWORD)

        response = self.client.post(
            reverse("login"), {"username": "buyer-one", "password": "WrongPassword789"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["login_form"].errors)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_unknown_username_is_rejected(self):
        response = self.client.post(
            reverse("login"), {"username": "no-such-buyer", "password": ACCOUNT_PASSWORD}
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_protected_pages_redirect_anonymous_visitors(self):
        for page in PROTECTED_PAGES:
            with self.subTest(page=page):
                response = self.client.get(reverse(page))
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response["Location"])

    def test_login_is_the_initial_route_for_anonymous_visitors(self):
        response = self.client.get("/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")
