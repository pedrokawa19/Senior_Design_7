"""Optional real-browser check: see instructions.md for the Playwright command."""
import io
import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.test import LiveServerTestCase, override_settings
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright, expect

from .support import ACCOUNT_PASSWORD, TEST_ENCRYPTION_KEY
from .test_auction import excel


@override_settings(CREDENTIAL_ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class AuctionBrowserTests(LiveServerTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        override = override_settings(AUCTION_UPLOAD_DIR=Path(directory.name))
        override.enable()
        self.addCleanup(override.disable)
        User.objects.create_user('browser-buyer', password=ACCOUNT_PASSWORD)

    def test_complete_auction_workflow(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(self.live_server_url + '/login/')
            page.locator('#login-form input[name=username]').fill('browser-buyer')
            page.locator('#login-form input[name=password]').fill(ACCOUNT_PASSWORD)
            # Go straight to Auction after login so no external market lookup is needed.
            page.route('**/api/index-performance*', lambda route: route.fulfill(status=200, json={
                'ticker': 'SLX', 'first_close': 1, 'last_close': 1, 'growth_percentage': 0,
                'prices': [{'date': '2026-01-01', 'close': 1}]}))
            page.locator('#login-form button[type=submit]').click()
            page.get_by_role('link', name='Auction', exact=True).click()
            expect(page.get_by_role('heading', name='Upload Auction List')).to_be_visible()
            expect(page.locator('#eligible-card')).to_have_count(0)
            rows = ['Width,Weight lbs,Tag'] + [f'60,{1000-i},E{i}' for i in range(205)] + [f'70,{1000-i},X{i}' for i in range(105)]
            page.locator('#id_file').set_input_files({'name': 'synthetic.csv', 'mimeType': 'text/csv', 'buffer': '\n'.join(rows).encode()})
            page.get_by_role('button', name='Upload', exact=True).click()
            eligible = page.locator('#eligible-card')
            expect(eligible.locator('tbody tr')).to_have_count(100)
            expect(page.locator('#excluded-card')).to_have_count(0)
            expect(eligible).to_contain_text('Filtered out 105 rows.')
            page.set_viewport_size({'width': 390, 'height': 844})
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))
            page.set_viewport_size({'width': 1280, 'height': 900})
            eligible.get_by_role('button', name='Last page', exact=True).click()
            expect(eligible.locator('tbody tr')).to_have_count(5)
            eligible.get_by_role('spinbutton', name='Eligible page number').fill('2')
            eligible.get_by_role('spinbutton', name='Eligible page number').press('Enter')
            expect(eligible.locator('tbody tr').first).to_contain_text('E100')
            eligible.get_by_role('button', name='Weight lbs: Sort ascending', exact=True).click()
            expect(eligible.locator('tbody tr').first).to_contain_text('796')
            eligible.get_by_role('button', name='Weight lbs: Sort descending', exact=True).click()
            expect(eligible.locator('tbody tr').first).to_contain_text('E0')
            eligible.get_by_role('button', name='Weight lbs: Restore original order', exact=True).click()
            page.get_by_role('button', name='Show excluded coils', exact=True).click()
            excluded = page.locator('#excluded-card')
            expect(excluded).to_be_visible()
            expect(excluded.locator('tbody tr')).to_have_count(100)
            excluded.get_by_role('button', name='Last page', exact=True).click()
            expect(excluded.locator('tbody tr')).to_have_count(5)
            excluded.locator('summary').click()
            page.locator('#excluded_width_op').select_option('ge')
            page.locator('#excluded_width').fill('70')
            excluded.get_by_role('button', name='Apply Filters').click()
            expect(eligible).to_contain_text('Filtered out 205 rows.')
            expect(page.locator('#eligible_width')).to_have_value('70')
            expect(page.locator('#excluded_width')).to_have_value('70')
            page.get_by_role('button', name='Hide Excluded Table').click()
            expect(excluded).to_have_count(0)
            with page.expect_download() as download:
                page.get_by_role('link', name='Download Excel').click()
            workbook = load_workbook(io.BytesIO(Path(download.value.path()).read_bytes()))
            self.assertEqual(workbook['Eligible'].max_row, 106)
            self.assertEqual(workbook['Excluded'].max_row, 206)
            workbook.close()
            content = excel({'First': [['Width', 'Weight lbs'], [62, 48000]], 'Second': [['Width', 'Weight lbs'], [63, 48001]]})
            page.locator('#id_file').set_input_files({'name': 'multi.xlsx', 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'buffer': content})
            page.get_by_role('button', name='Replace upload').click()
            expect(eligible).to_have_count(0)
            page.locator('#sheet-select').select_option('First')
            page.get_by_role('button', name='Load worksheet').click()
            expect(page.locator('#eligible_width')).to_have_value('62')
            expect(eligible.locator('tbody tr')).to_have_count(1)
            expect(excluded).to_have_count(0)
            page.screenshot(path='/private/tmp/auction-desktop.png', full_page=True)
            page.set_viewport_size({'width': 390, 'height': 844})
            page.screenshot(path='/private/tmp/auction-mobile.png', full_page=True)
            self.assertEqual(errors, [])
            browser.close()
