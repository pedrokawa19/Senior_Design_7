"""Rendering of the dashboard, navigation, profile, history, and placeholders."""

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .support import ACCOUNT_PASSWORD, NAV_TABS, TEST_ENCRYPTION_KEY


@override_settings(CREDENTIAL_ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class PageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("buyer-one", password=ACCOUNT_PASSWORD)
        self.client.force_login(self.user)

    def test_dashboard_keeps_existing_content(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Most Profitable Products")
        self.assertContains(response, "Index Performance")
        self.assertContains(response, "card profitability-card")

    def test_dashboard_no_longer_manages_the_database_connection(self):
        response = self.client.get(reverse("dashboard"))

        self.assertNotContains(response, "CONNECT TO DATABASE")
        self.assertNotContains(response, "DATABASE CONNECTED")
        self.assertNotContains(response, "dialog-root")
        # Users are pointed at the Profile page instead.
        self.assertContains(response, reverse("profile"))

    def test_header_shows_a_profile_tab_and_no_inline_session_controls(self):
        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "tab-profile")
        self.assertNotContains(response, "Signed in as")
        self.assertNotContains(response, "session-controls")

    def test_navigation_tabs_are_present(self):
        response = self.client.get(reverse("dashboard"))

        for page in NAV_TABS:
            with self.subTest(page=page):
                self.assertContains(response, f'href="{reverse(page)}"')

    def test_placeholder_pages_render_their_card(self):
        expected = {
            "auction": "This is the Auction page",
            "inventory": "This is the Inventory page",
            "model": "This is the Model page",
        }
        for page, message in expected.items():
            with self.subTest(page=page):
                response = self.client.get(reverse(page))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, message)

    def test_history_opens_on_purchase_history(self):
        response = self.client.get(reverse("history"))

        self.assertRedirects(response, reverse("history-purchases"))

    def test_history_subpages_render_both_tabs(self):
        for page, heading in [
            ("history-purchases", "Purchase History"),
            ("history-sales", "Sales History"),
        ]:
            with self.subTest(page=page):
                response = self.client.get(reverse(page))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, heading)
                self.assertContains(response, reverse("history-purchases"))
                self.assertContains(response, reverse("history-sales"))

    def test_profile_shows_the_account_and_logout(self):
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "buyer-one")
        self.assertContains(response, "Database Information")
        self.assertContains(response, reverse("logout"))
        self.assertContains(response, "Log out")

    def test_profile_never_renders_the_account_password_hash(self):
        response = self.client.get(reverse("profile"))

        self.assertNotContains(response, self.user.password)
        self.assertNotContains(response, ACCOUNT_PASSWORD)
