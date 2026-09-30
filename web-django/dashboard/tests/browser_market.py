"""Optional browser coverage using synthetic prices; no market network requests."""
import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.test import LiveServerTestCase, override_settings
from playwright.sync_api import expect, sync_playwright

from .support import ACCOUNT_PASSWORD, TEST_ENCRYPTION_KEY


@override_settings(CREDENTIAL_ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class MarketBrowserTests(LiveServerTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        override = override_settings(AUCTION_UPLOAD_DIR=Path(directory.name))
        override.enable()
        self.addCleanup(override.disable)
        User.objects.create_user("market-buyer", password=ACCOUNT_PASSWORD)

    def test_market_chart_and_shared_header(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                headless=True,
            )
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))

            def prices(route):
                spy = "ticker=SPY" in route.request.url
                route.fulfill(json={
                    "ticker": "SPY" if spy else "SLX",
                    "name": "State Street SPDR S&P 500 ETF Trust" if spy else "VanEck Steel ETF",
                    "first_close": 100, "last_close": 90 if spy else 110,
                    "growth_percentage": -10 if spy else 10,
                    "prices": [
                        {"date": "2024-01-02", "close": 100},
                        {"date": "2024-01-03", "close": 105},
                        {"date": "2024-01-05", "close": 90 if spy else 110},
                    ],
                })

            page.route("**/api/index-performance*", prices)
            page.route("**/api/connection", lambda route: route.fulfill(json={"connection": None}))
            page.goto(self.live_server_url + "/login/")
            page.locator("#login-form input[name=username]").fill("market-buyer")
            page.locator("#login-form input[name=password]").fill(ACCOUNT_PASSWORD)
            page.locator("#login-form button[type=submit]").click()
            expect(page.locator("#ticker-title")).to_have_text("VanEck Steel ETF")
            expect(page.locator("#ending-close")).to_have_text("$110.00")
            expect(page.locator(".market-quote #growth")).to_have_text("+10.00%")
            expect(page.locator(".chart-summary")).to_have_count(0)
            chart = page.locator("#chart-wrapper")
            expect(chart.locator("svg")).to_be_visible()
            chart.hover(position={"x": 65, "y": 70})
            expect(page.locator(".chart-tooltip")).to_have_text("2024-01-02 · $100.00")
            chart.focus()
            chart.press("End")
            expect(page.locator(".chart-tooltip")).to_have_text("2024-01-05 · $110.00")
            chart.press("ArrowLeft")
            expect(page.locator(".chart-tooltip")).to_have_text("2024-01-03 · $105.00")
            chart.press("Escape")
            expect(page.locator(".chart-tooltip")).to_be_hidden()
            page.locator("#ticker").select_option("SPY")
            expect(page.locator("#ticker-title")).to_have_text("State Street SPDR S&P 500 ETF Trust")
            expect(page.locator("#ending-close")).to_have_text("$90.00")
            expect(page.locator("#growth")).to_have_class("growth growth-negative")
            page.screenshot(path="/private/tmp/market-desktop.png", full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            expect(chart.locator("svg")).to_be_visible()
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
            page.screenshot(path="/private/tmp/market-mobile.png", full_page=True)

            # Empty responses must clear the prior quote and provide feedback.
            page.unroute("**/api/index-performance*", prices)
            page.route("**/api/index-performance*", lambda route: route.fulfill(json={"prices": []}))
            page.locator("#ticker").select_option("SLX")
            expect(page.locator("#market-content .error")).to_contain_text("No closing prices")
            expect(page.locator("#ending-close")).to_be_empty()
            expect(page.locator("#growth")).to_be_empty()

            # Sticky positioning comes from the shared template on every page.
            for path in ["/", "/inventory/", "/auction/", "/history/purchases/"]:
                page.goto(self.live_server_url + path)
                page.evaluate("document.body.style.minHeight = '2200px'; window.scrollTo(0, 600)")
                header = page.locator(".dashboard-header")
                expect(header).to_be_visible()
                self.assertAlmostEqual(header.bounding_box()["y"], 0, delta=1)
                self.assertEqual(header.evaluate("el => getComputedStyle(el).paddingTop"), "20px")
            self.assertEqual(errors, [])
            browser.close()
