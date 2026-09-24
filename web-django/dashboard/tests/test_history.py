"""Purchase and sales history endpoints."""

import pandas as pd
from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..services import history
from .support import ACCOUNT_PASSWORD, SYNTHETIC_CONNECTION, TEST_ENCRYPTION_KEY

HISTORY_ENDPOINTS = ["purchase-history", "sales-history"]


@override_settings(CREDENTIAL_ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class HistoryEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("buyer-one", password=ACCOUNT_PASSWORD)
        self.client.force_login(self.user)

    def save_connection(self):
        return self.client.post(
            reverse("connection"),
            data=SYNTHETIC_CONNECTION,
            content_type="application/json",
        )

    def test_history_requires_authentication(self):
        anonymous = Client()

        for endpoint in HISTORY_ENDPOINTS:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(anonymous.get(reverse(endpoint)).status_code, 401)

    def test_history_requires_a_saved_connection(self):
        for endpoint in HISTORY_ENDPOINTS:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.client.get(reverse(endpoint)).status_code, 409)

    def test_unwritten_queries_report_that_they_are_not_configured(self):
        """The placeholder SQL is detected before any database connection is opened."""
        self.save_connection()

        for endpoint in HISTORY_ENDPOINTS:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(reverse(endpoint))
                self.assertEqual(response.status_code, 501)
                self.assertIn("has not been written yet", response.json()["detail"])

    def test_a_written_query_is_shaped_into_columns_and_rows(self):
        table = history._as_table(
            pd.DataFrame(
                [{"PO Number": "PO-1", "Cost": 10.5}, {"PO Number": "PO-2", "Cost": None}]
            )
        )

        self.assertEqual(table["columns"], ["PO Number", "Cost"])
        self.assertEqual(table["row_count"], 2)
        self.assertEqual(table["rows"][0], ["PO-1", 10.5])
        self.assertIsNone(table["rows"][1][1])

    def test_results_are_capped_so_a_missing_limit_cannot_flood_the_page(self):
        oversized = pd.DataFrame({"value": range(history.MAX_ROWS + 50)})

        table = history._as_table(oversized)

        self.assertEqual(table["row_count"], history.MAX_ROWS)
