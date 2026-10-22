"""Run with Playwright against a local Django server (LIGNET_PREVIEW_URL)."""
import os
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('LIGNET_PREVIEW_URL', 'http://127.0.0.1:8097')
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True, args=['--no-sandbox'])
    for width in (320, 375, 768, 1024, 1920):
        page = browser.new_page(viewport={'width': width, 'height': 900})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('https://www.googletagmanager.com/**', lambda route: route.abort())
        page.route('https://cdn.jsdelivr.net/**', lambda route: route.abort())
        for path in ('/', '/ferramentas/calculadora-cidr/'):
            page.goto(BASE + path, wait_until='domcontentloaded')
            nav = page.locator('#site-nav')
            tools = page.locator('.site-tools > button')
            mobile = width <= 900
            assert page.locator('[data-site-navigation]').count() == 1
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            if mobile:
                expect(page.locator('.site-toggle')).to_be_visible()
                expect(nav).not_to_be_visible()
                page.locator('.site-toggle').click()
                expect(page.locator('.site-close')).to_be_focused()
                assert page.evaluate('document.body.style.position') == 'fixed'
                page.keyboard.press('Shift+Tab')
                expect(nav.locator('a').last).to_be_focused()
                page.keyboard.press('Tab')
                expect(page.locator('.site-close')).to_be_focused()
            tools.click()
            expect(page.locator('#site-tools')).to_be_visible()
            category = page.locator('[aria-controls=site-network]')
            category.click()
            expect(page.locator('#site-network')).not_to_be_visible()
            category.click()
            expect(page.locator('#site-network')).to_be_visible()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=f'/tmp/lignet-nav-{width}-{ "home" if path == "/" else "cidr"}.png')
            page.keyboard.press('Escape')
            if mobile:
                expect(nav).not_to_be_visible()
                expect(page.locator('.site-toggle')).to_be_focused()
                assert page.evaluate('document.body.style.position') != 'fixed'
                page.locator('.site-toggle').click()
                page.locator('.site-backdrop').click(position={'x': 5, 'y': 120})
                expect(nav).not_to_be_visible()
                page.locator('.site-toggle').click()
                page.locator('.site-close').click()
                expect(nav).not_to_be_visible()
                page.locator('.site-toggle').click()
                if tools.get_attribute("aria-expanded") != "true":
                    tools.click()
                nav.locator('a[href="/#qrcode"]').click()
                expect(nav).not_to_be_visible()
                assert page.evaluate('document.body.style.position') != 'fixed'
            else:
                expect(tools).to_be_focused()
            page.goto(BASE + '/ferramentas/calculadora-cidr/', wait_until='domcontentloaded')
            expect(page.locator('a[aria-current=page]')).to_have_attribute('href', '/ferramentas/calculadora-cidr/')
        assert not errors, errors
        print(f'{width}px: layout, accordion, keyboard, focus and dismissal OK')
        page.close()
    browser.close()
