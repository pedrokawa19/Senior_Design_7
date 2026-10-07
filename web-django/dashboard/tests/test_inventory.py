"""Inventory queries and endpoints use synthetic data, never the client database."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import mysql.connector
from django.contrib.auth.models import User
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from ..credentials import CredentialStorageUnavailable
from ..services import inventory
from .support import ACCOUNT_PASSWORD, SYNTHETIC_CONNECTION, TEST_ENCRYPTION_KEY


def inventory_row(key=1):
    row = [None] * len(inventory.COLUMNS)
    values = {
        "vmitf_key": key, "vmit_item_no": "Synthetic item",
        "vmit_po_date": date(2026, 10, 7), "vmit_qty": Decimal("1234.50"),
        "vmit_cost": Decimal("12.345"), "vmit_qty_status": 1,
    }
    for index, (column, _) in enumerate(inventory.COLUMNS):
        row[index] = values.get(column)
    return tuple(row)


class InventoryQueryTests(SimpleTestCase):
    def setUp(self):
        self.connection = MagicMock()
        self.cursor = self.connection.cursor.return_value
        self.cursor.description = [(column,) for column, _ in inventory.COLUMNS]
        self.cursor.fetchone.return_value = (1201,)
        self.cursor.fetchall.return_value = [inventory_row()]
        connect = patch.object(inventory, "get_database_connection", return_value=self.connection)
        self.connect = connect.start()
        self.addCleanup(connect.stop)

    def test_query_uses_existing_view_and_newest_first_with_no_writes(self):
        result = inventory.get_inventory(SYNTHETIC_CONNECTION)
        self.connect.assert_called_once_with(SYNTHETIC_CONNECTION)
        self.assertEqual(self.cursor.execute.call_args_list[0].args,
                         ("SELECT COUNT(*) FROM current_inventory",))
        query, params = self.cursor.execute.call_args_list[1].args
        self.assertEqual(query, "SELECT * FROM current_inventory ORDER BY "
                         "vmit_po_date DESC, vmitf_key DESC LIMIT %s OFFSET %s")
        self.assertEqual(params, (50, 0))
        self.assertEqual(result["page_size"], 50)
        self.assertEqual(result["columns"], [column for column, _ in inventory.COLUMNS])
        self.assertEqual(len(result["columns"]), 23)
        self.assertEqual(result["rows"][0], inventory_row())
        self.assertEqual(result["total_rows"], 1201)
        self.assertEqual(result["page_count"], 25)
        self.assertIsNone(result["expires_at"])
        self.cursor.close.assert_called_once()
        self.connection.close.assert_called_once()

    def test_pages_beyond_the_history_cap_are_accessible(self):
        result = inventory.get_inventory(SYNTHETIC_CONNECTION, page=23)
        self.assertEqual(result["page"], 23)
        self.assertEqual(self.cursor.execute.call_args.args[1], (50, 1100))

    def test_empty_partial_and_out_of_range_pages(self):
        full_page = [inventory_row(key) for key in range(50)]
        for total, rows, expected_page in (
                (0, [], 1), (50, full_page, 1), (100, full_page, 2),
                (101, [inventory_row()], 3)):
            with self.subTest(total=total):
                self.cursor.fetchone.return_value = (total,)
                self.cursor.fetchall.return_value = rows
                result = inventory.get_inventory(SYNTHETIC_CONNECTION, page=999)
                self.assertEqual(result["page"], expected_page)
                self.assertEqual(result["page_count"], expected_page)
                self.assertEqual(result["row_count"], len(rows))
                self.assertEqual(result["total_rows"], total)
                self.assertEqual(self.cursor.execute.call_args.args[1],
                                 (50, (expected_page - 1) * 50))

    def test_every_column_can_be_sorted_in_both_directions_in_sql(self):
        for index, (column, _) in enumerate(inventory.COLUMNS):
            for direction in ("asc", "desc"):
                with self.subTest(column=column, direction=direction):
                    inventory.get_inventory(SYNTHETIC_CONNECTION,
                                            sort_column=index, sort_direction=direction)
                    query = self.cursor.execute.call_args.args[0]
                    self.assertIn(f"ORDER BY {column} IS NULL, {column} "
                                  f"{direction.upper()}, vmitf_key DESC", query)

    def test_invalid_sort_does_not_open_connection(self):
        for options in ({"page": 0}, {"sort_column": -1, "sort_direction": "asc"},
                        {"sort_column": 23, "sort_direction": "asc"},
                        {"sort_column": 0}, {"sort_direction": "desc"},
                        {"sort_column": 0, "sort_direction": "DROP TABLE"}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                inventory.get_inventory(SYNTHETIC_CONNECTION, **options)
        self.connect.assert_not_called()

    def test_incompatible_view_is_reported_and_resources_are_closed(self):
        self.cursor.description = [("unexpected_column",)]
        with self.assertRaises(inventory.InvalidInventorySchema):
            inventory.get_inventory(SYNTHETIC_CONNECTION)
        self.cursor.close.assert_called_once()
        self.connection.close.assert_called_once()

    def test_uppercase_database_column_names_are_supported(self):
        self.cursor.description = [(column.upper(),) for column, _ in inventory.COLUMNS]
        result = inventory.get_inventory(SYNTHETIC_CONNECTION)
        self.assertEqual(result["column_labels"][0], "Tag key")
        self.assertEqual(result["columns"][0], "VMITF_KEY")

    def test_failed_query_closes_resources(self):
        self.cursor.execute.side_effect = mysql.connector.OperationalError("Synthetic failure")
        with self.assertRaises(mysql.connector.Error):
            inventory.get_inventory(SYNTHETIC_CONNECTION)
        self.cursor.close.assert_called_once()
        self.connection.close.assert_called_once()


@override_settings(CREDENTIAL_ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class InventoryEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("inventory-buyer", password=ACCOUNT_PASSWORD)
        self.client.force_login(self.user)
        self.url = reverse("current-inventory")

    def save_connection(self):
        self.client.post(reverse("connection"), SYNTHETIC_CONNECTION,
                         content_type="application/json")

    def test_authentication_connection_and_read_only_method(self):
        self.assertEqual(Client().get(self.url).status_code, 401)
        self.assertEqual(self.client.get(self.url).status_code, 409)
        self.assertEqual(self.client.post(self.url).status_code, 405)

    @patch.object(inventory, "get_inventory")
    def test_invalid_parameters_are_rejected_before_querying(self, loader):
        for params in ({"page": 0}, {"page": "1.5"}, {"page": "x"},
                       {"sort_column": -1, "sort_direction": "asc"},
                       {"sort_column": 23, "sort_direction": "desc"},
                       {"sort_column": 0}, {"sort_direction": "asc"},
                       {"sort_column": 0, "sort_direction": "DROP"},
                       {"refresh": "yes"}):
            with self.subTest(params=params):
                self.assertEqual(self.client.get(self.url, params).status_code, 400)
        loader.assert_not_called()

    @patch.object(inventory, "get_database_connection")
    def test_serialization_preserves_dates_decimal_precision_and_nulls(self, connect):
        self.save_connection()
        cursor = connect.return_value.cursor.return_value
        cursor.description = [(column,) for column, _ in inventory.COLUMNS]
        cursor.fetchone.return_value = (1,)
        cursor.fetchall.return_value = [inventory_row()]
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        row = dict(zip(data["columns"], data["rows"][0]))
        self.assertEqual(row["vmit_po_date"], "2026-10-07")
        self.assertEqual(row["vmit_qty"], "1234.50")
        self.assertEqual(row["vmit_cost"], "12.345")
        self.assertEqual(row["vmit_qty_status"], 1)
        self.assertIsNone(row["vmit_grade"])
        self.assertEqual(response["Cache-Control"], "no-store")

    @patch.object(inventory, "get_inventory")
    def test_valid_page_sort_refresh_and_user_connection(self, loader):
        self.save_connection()
        loader.return_value = {"columns": [], "rows": []}
        response = self.client.get(self.url, {
            "page": 12, "sort_column": 22, "sort_direction": "desc", "refresh": "1",
        })
        self.assertEqual(response.status_code, 200)
        loader.assert_called_once_with(SYNTHETIC_CONNECTION, page=12,
                                       sort_column=22, sort_direction="desc")
        other = User.objects.create_user("other-buyer", password=ACCOUNT_PASSWORD)
        self.client.force_login(other)
        self.assertEqual(self.client.get(self.url).status_code, 409)
        self.assertEqual(loader.call_count, 1)

    @patch.object(inventory, "get_inventory")
    def test_each_request_reads_fresh_data(self, loader):
        self.save_connection()
        loader.return_value = {"columns": [], "rows": []}
        for params in ({}, {"page": 2}, {"refresh": "1"}):
            self.assertEqual(self.client.get(self.url, params).status_code, 200)
        self.assertEqual(loader.call_count, 3)

    @patch("dashboard.views.api.connections.require_connection")
    def test_unreadable_credentials_are_explicit(self, require):
        require.side_effect = CredentialStorageUnavailable("Synthetic key unavailable.")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "Synthetic key unavailable.")

    @patch.object(inventory, "get_inventory")
    def test_database_errors_do_not_expose_driver_messages(self, loader):
        self.save_connection()
        for errno in (1146, 2003):
            loader.side_effect = mysql.connector.OperationalError(
                "Synthetic private host and password", errno=errno)
            with self.subTest(errno=errno), self.assertLogs("dashboard.views.api", level="WARNING") as logs:
                response = self.client.get(self.url)
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("Synthetic private", response.content.decode())
            self.assertNotIn("Synthetic private", "\n".join(logs.output))
            if errno == 1146:
                self.assertIn("current_inventory view is unavailable", response.json()["detail"])

    @patch.object(inventory, "get_inventory")
    def test_view_schema_errors_are_explicit(self, loader):
        self.save_connection()
        loader.side_effect = inventory.InvalidInventorySchema("Synthetic incompatible view.")
        with self.assertLogs("dashboard.views.api", level="WARNING"):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "Synthetic incompatible view.")
