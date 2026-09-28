"""Purchase and sales history endpoints."""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pandas as pd
from django.core.cache import cache
from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..services import history
from .support import ACCOUNT_PASSWORD, SYNTHETIC_CONNECTION, TEST_ENCRYPTION_KEY

HISTORY_ENDPOINTS = ["purchase-history", "sales-history"]


@override_settings(
    CREDENTIAL_ENCRYPTION_KEY=TEST_ENCRYPTION_KEY,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class HistoryEndpointTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
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
                with patch.object(history, "PURCHASE_HISTORY_QUERY", ""), patch.object(history, "SALES_HISTORY_QUERY", ""):
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


    def snapshot(self, count=1000):
        return {"columns": ["ID"], "rows": [[n] for n in range(count)], "row_count": count}

    @patch.object(history, "_run_history_query")
    def test_pages_share_one_bounded_snapshot(self, run):
        self.save_connection()
        run.return_value = self.snapshot()
        first = self.client.get(reverse("purchase-history")).json()
        second = self.client.get(reverse("purchase-history"), {"page": 2}).json()
        last = self.client.get(reverse("purchase-history"), {"page": 10}).json()
        self.assertEqual(first["rows"], [[n] for n in range(100)])
        self.assertEqual(second["rows"], [[n] for n in range(100, 200)])
        self.assertEqual(last["rows"], [[n] for n in range(900, 1000)])
        self.assertEqual(last["page_count"], 10)
        self.assertEqual(first["refreshed_at"], second["refreshed_at"])
        self.assertEqual(run.call_count, 1)
        self.assertIn("limit 1000", run.call_args.args[1])

    @patch.object(history, "_run_history_query")
    def test_refresh_replaces_snapshot_and_timestamp_for_one_hour(self, run):
        self.save_connection()
        run.side_effect = [self.snapshot(101), self.snapshot(50)]
        initial = datetime.now(timezone.utc)
        with patch.object(history.timezone, "now", return_value=initial), patch.object(cache, "set", wraps=cache.set) as store:
            first = self.client.get(reverse("sales-history")).json()
            self.assertEqual(store.call_args.args[2], 3600)
        with patch.object(history.timezone, "now", return_value=initial + timedelta(minutes=5)):
            refreshed = self.client.get(reverse("sales-history"), {"refresh": "1", "page": 2}).json()
        self.assertNotEqual(first["refreshed_at"], refreshed["refreshed_at"])
        self.assertEqual(refreshed["total_rows"], 50)
        self.assertEqual(refreshed["page"], 1)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(datetime.fromisoformat(refreshed["expires_at"]) - datetime.fromisoformat(refreshed["refreshed_at"]), timedelta(hours=1))
        self.assertEqual(self.client.get(reverse("sales-history")).json()["total_rows"], 50)
        self.assertEqual(run.call_count, 2)

    @patch.object(history, "_run_history_query")
    def test_expired_cache_reloads(self, run):
        self.save_connection()
        run.return_value = self.snapshot(1)
        with patch("time.time", return_value=100000):
            self.client.get(reverse("purchase-history"))
        with patch("time.time", return_value=103599):
            self.client.get(reverse("purchase-history"))
        self.assertEqual(run.call_count, 1)
        with patch("time.time", return_value=103601):
            self.client.get(reverse("purchase-history"))
        self.assertEqual(run.call_count, 2)

    @patch.object(history, "_run_history_query")
    def test_cache_isolates_filters_reports_users_and_connection_versions(self, run):
        self.save_connection()
        run.return_value = self.snapshot(1)
        url = reverse("purchase-history")
        self.client.get(url)
        self.client.get(url, {"item": "steel"})
        self.client.get(reverse("sales-history"))
        self.save_connection()
        self.client.get(url)
        other = User.objects.create_user("buyer-two", password=ACCOUNT_PASSWORD)
        self.client.force_login(other)
        self.save_connection()
        self.client.get(url)
        self.assertEqual(run.call_count, 5)

    @patch.object(history, "_run_history_query")
    def test_invalid_filters_never_query(self, run):
        self.save_connection()
        for params in ({"page": "0"}, {"page": "11"}, {"page": "x"},
                       {"start_date": "invalid"}, {"start_date": "2026-09-20", "end_date": "2026-09-01"},
                       {"item": "x" * 129}, {"refresh": "yes"}):
            with self.subTest(params=params):
                self.assertEqual(self.client.get(reverse("purchase-history"), params).status_code, 400)
        run.assert_not_called()

    def test_filters_are_bound_before_limit_and_use_report_columns(self):
        filters = {"start_date": date(2026, 1, 1), "end_date": date(2026, 9, 27),
                   "item": "%' OR 1=1 --", "party": "Synthetic"}
        for report, query, party in (("purchases", history.PURCHASE_HISTORY_QUERY, "poln_vendor_name"),
                                     ("sales", history.SALES_HISTORY_QUERY, "oh.ordh_cust_name")):
            with self.subTest(report=report):
                sql, params = history._filtered_query(query, report, filters)
                self.assertNotIn(filters["item"], sql)
                self.assertIn(filters["item"], params)
                self.assertIn(party, sql)
                self.assertLess(sql.index("WHERE"), sql.index("limit 1000"))
                self.assertEqual(params[-1], "Synthetic")
                self.assertEqual(sql.count("%s"), len(params))

    @patch.object(history, "_run_history_query")
    def test_empty_partial_and_out_of_range_pages(self, run):
        self.save_connection()
        for count, expected_page, expected_rows in ((0, 1, 0), (101, 2, 1), (200, 2, 100)):
            run.return_value = self.snapshot(count)
            data = self.client.get(reverse("purchase-history"), {"refresh": "1", "page": 10}).json()
            self.assertEqual((data["page"], data["row_count"]), (expected_page, expected_rows))

    @patch.object(history, "_run_history_query")
    def test_failed_refresh_does_not_poison_cache_or_expose_error(self, run):
        self.save_connection()
        run.side_effect = [self.snapshot(1), RuntimeError("private database details")]
        self.client.get(reverse("purchase-history"))
        response = self.client.get(reverse("purchase-history"), {"refresh": "1"})
        self.assertEqual(response.status_code, 503)
        self.assertNotContains(response, "private database details", status_code=503)
        self.assertEqual(self.client.get(reverse("purchase-history")).json()["total_rows"], 1)

    @patch.object(history.pd, "read_sql")
    @patch.object(history, "get_database_connection")
    def test_query_binds_parameters_and_closes_connection_even_on_error(self, connect, read):
        connection = MagicMock()
        connect.return_value = connection
        read.side_effect = RuntimeError("synthetic failure")
        with self.assertRaises(RuntimeError):
            history._run_history_query(SYNTHETIC_CONNECTION, "SELECT %s", ["value"])
        read.assert_called_once_with("SELECT %s", con=connection, params=["value"])
        connection.close.assert_called_once()

    def test_history_page_exposes_filters_refresh_timestamp_and_pagination(self):
        for page, party in (("history-purchases", "Vendor"), ("history-sales", "Customer")):
            response = self.client.get(reverse(page))
            for text in ("Last Refreshed", "Apply filters", "Clear filters", "Previous", "Next", party,
                         'id="refresh-history"', 'name="start_date"', 'name="item"'):
                self.assertContains(response, text)


    @patch.object(history, "_run_history_query")
    def test_sort_cycles_across_pages_without_requerying_or_mutating_cache(self, run):
        self.save_connection()
        run.return_value = {"columns": ["ID"], "rows": [[n] for n in range(205, 0, -1)], "row_count": 205}
        url = reverse("purchase-history")
        original = self.client.get(url).json()
        ascending = self.client.get(url, {"sort_column": 0, "sort_direction": "asc"}).json()
        second = self.client.get(url, {"sort_column": 0, "sort_direction": "asc", "page": 2}).json()
        descending = self.client.get(url, {"sort_column": 0, "sort_direction": "desc"}).json()
        restored = self.client.get(url).json()
        self.assertEqual(ascending["rows"], [[n] for n in range(1, 101)])
        self.assertEqual(second["rows"][0], [101])
        self.assertEqual(descending["rows"], original["rows"])
        self.assertEqual(restored["rows"], original["rows"])
        self.assertEqual(ascending["refreshed_at"], original["refreshed_at"])
        self.assertEqual(run.call_count, 1)

    def test_sort_handles_numbers_text_dates_ties_and_missing_values(self):
        numeric = [[10], [2], [None], [""]]
        self.assertEqual(history._sort_rows(numeric, 0, "asc"), [[2], [10], [None], [""]])
        self.assertEqual(history._sort_rows(numeric, 0, "desc"), [[10], [2], [None], [""]])
        text = [["beta", 1], ["Alpha", 2], ["alpha", 3]]
        self.assertEqual(history._sort_rows(text, 0, "asc"), [text[1], text[2], text[0]])
        self.assertEqual(history._sort_rows([["2026-10-01"], ["2025-12-31"]], 0, "asc"),
                         [["2025-12-31"], ["2026-10-01"]])
        self.assertEqual(history._sort_rows(numeric, None, ""), numeric)

    @patch.object(history, "_run_history_query")
    def test_invalid_sort_parameters_do_not_query_database(self, run):
        self.save_connection()
        for params in ({"sort_column": -1, "sort_direction": "asc"},
                       {"sort_column": 10, "sort_direction": "asc"},
                       {"sort_column": 0}, {"sort_direction": "asc"},
                       {"sort_column": 0, "sort_direction": "DROP TABLE"}):
            self.assertEqual(self.client.get(reverse("sales-history"), params).status_code, 400)
        run.assert_not_called()
