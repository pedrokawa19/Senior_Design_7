"""Input validation for the market performance endpoint."""

from unittest.mock import patch

import pandas as pd

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .support import ACCOUNT_PASSWORD, TEST_ENCRYPTION_KEY


@override_settings(CREDENTIAL_ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class MarketEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("buyer-one", password=ACCOUNT_PASSWORD)
        self.client.force_login(self.user)

    def test_missing_dates_return_a_validation_error(self):
        response = self.client.get(reverse("index-performance"))

        self.assertEqual(response.status_code, 400)

    def test_unsupported_ticker_is_rejected(self):
        response = self.client.get(
            reverse("index-performance"),
            {"start_date": "2024-01-01", "end_date": "2024-01-31", "ticker": "NVDA"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Ticker must be SPY or SLX.")

    def test_reversed_date_range_is_rejected(self):
        response = self.client.get(
            reverse("index-performance"),
            {"start_date": "2024-02-01", "end_date": "2024-01-01", "ticker": "SLX"},
        )

        self.assertEqual(response.status_code, 400)


    @patch("dashboard.services.market.yf.download")
    def test_names_and_selected_range_prices(self, download):
        download.return_value = pd.DataFrame(
            {"Close": [100.0, 110.0]},
            index=pd.to_datetime(["2024-01-02", "2024-01-05"]),
        )
        for ticker, name in [
            ("SLX", "VanEck Steel ETF"),
            ("SPY", "State Street SPDR S&P 500 ETF Trust"),
        ]:
            with self.subTest(ticker=ticker):
                response = self.client.get(reverse("index-performance"), {
                    "start_date": "2024-01-01", "end_date": "2024-01-07", "ticker": ticker,
                })
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertEqual(data["name"], name)
                self.assertEqual(data["last_close"], 110.0)
                self.assertEqual(data["growth_percentage"], 10.0)
                self.assertEqual(data["prices"][-1], {"date": "2024-01-05", "close": 110.0})
                self.assertEqual(download.call_args.kwargs["end"], "2024-01-08")
