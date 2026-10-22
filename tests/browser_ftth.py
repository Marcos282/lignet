"""FTTH integration QA using installed Chrome. No production network calls.
Run: uv run --with playwright python tests/browser_ftth.py
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('LIGNET_PREVIEW_URL', 'http://127.0.0.1:8098')
OUT = Path('/tmp/lignet-ftth-qa')
OUT.mkdir(exist_ok=True)
CASES = Path(__file__).with_name('ftth_engine_cases.js').read_text()
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
    for width in [int(value) for value in os.environ.get('FTTH_TEST_WIDTHS', '320,375,768,1024,1920').split(',')]:
        context = browser.new_context(viewport={'width': width, 'height': 1000}, has_touch=width < 900, accept_downloads=True)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('https://www.googletagmanager.com/**', lambda route: route.abort())
        page.route('https://cdn.jsdelivr.net/**', lambda route: route.abort())
        page.route('**/ftth-engine-cases.js', lambda route: route.fulfill(content_type='application/javascript', body=CASES))
        page.goto(BASE + '/ferramentas/simulador-ftth/', wait_until='domcontentloaded')
        expect(page.locator('#palette button')).to_have_count(13)
        page.add_script_tag(url=BASE + '/ftth-engine-cases.js', type='module')
        page.wait_for_function('Array.isArray(window.ftthEngineChecks)')
        print(f'{width}px: {len(page.evaluate("window.ftthEngineChecks"))} optical/validation checks passed', flush=True)
        def click(selector):
            target = page.locator(selector)
            group = target.locator('xpath=ancestor::details')
            if group.count() and not group.evaluate('(el) => el.open'):
                group.locator('summary').click()
            target.click()
        # Build a simple OLT -> ONU using UI only, configure TX and RX limits.
        click('[data-add=olt]')
        form = page.locator('#properties-form')
        form.locator('[name=x]').fill('100')
        form.locator('[name=y]').fill('50')
        form.locator('[name="down.tx"]').fill('5')
        form.locator('button[type=submit]').click()
        if width <= 900:
            click('#properties-close')
        click('[data-add=onu]')
        form.locator('[name=x]').fill('100')
        form.locator('[name=y]').fill('320')
        form.locator('[name="down.sensitivity"]').fill('-28')
        form.locator('[name="down.overload"]').fill('-8')
        form.locator('button[type=submit]').click()
        if width <= 900:
            click('#properties-close')
        click('#fit')
        click('[data-mode=connect]')
        # Keyboard activation avoids the small visual port dots; node selects first free output.
        page.locator('.ftth-node').first.focus()
        page.keyboard.press('Enter')
        expect(page.locator('.ftth-node').first).to_be_focused()
        page.keyboard.press('Tab')
        expect(page.locator('.ftth-node').last).to_be_focused()
        page.keyboard.press('Enter')
        expect(page.locator('[data-edge-id]')).to_have_count(1)
        expect(page.locator('#results-body')).to_contain_text('Fora dos limites')
        # Connection properties include all independent fiber losses.
        click('[data-mode=move]')
        page.locator('[data-edge-id]').focus()
        page.keyboard.press('Enter')
        form.locator('[name="fiber.km"]').fill('20')
        form.locator('[name="fiber.extra"]').fill('15')
        form.locator('button[type=submit]').click()
        expect(page.locator('#results-body')).to_contain_text('-15')
        expect(page.locator('#results-body')).to_contain_text('Dentro dos limites')
        if width <= 900:
            click('#properties-close')
        click('#save')
        saved = json.loads(page.evaluate("localStorage.getItem('lignet-ftth-v1')"))
        assert len(saved['nodes']) == 2 and len(saved['edges']) == 1
        page.locator('#project-name').fill('Mudança de nome')
        page.locator('#project-name').press('Tab')
        click('#load')
        expect(page.locator('#project-name')).to_have_value(saved['name'])
        with page.expect_download() as download:
            click('#export')
        exported = download.value
        exported.save_as(str(OUT / f'project-{width}.json'))
        assert json.loads((OUT / f'project-{width}.json').read_text()) == saved
        malicious = json.loads(json.dumps(saved))
        malicious['nodes'][0]['label'] = '<img src=x onerror=alert(1)>'
        payload = {'name': 'project.json', 'mimeType': 'application/json', 'buffer': json.dumps(malicious).encode()}
        page.locator('#import-file').set_input_files(payload)
        expect(page.locator('#ftth-status')).to_contain_text('carregado e validado')
        assert page.locator('#ftth-app img').count() == 0
        invalid = json.loads(json.dumps(saved))
        invalid['edges'][0]['fiber']['km'] = -1
        page.locator('#import-file').set_input_files({'name': 'invalid.json', 'mimeType': 'application/json', 'buffer': json.dumps(invalid).encode()})
        expect(page.locator('#ftth-status')).to_contain_text('Importação rejeitada')
        page.locator('#import-file').set_input_files({'name': 'broken.json', 'mimeType': 'application/json', 'buffer': b'{bad json'})
        expect(page.locator('#ftth-status')).to_contain_text('Importação rejeitada')
        expect(page.locator('.ftth-node')).to_have_count(2)
        click('#load')
        click('#example')
        expect(page.locator('.ftth-node')).to_have_count(5)
        expect(page.locator('#results-body tr')).to_have_count(2)
        click('#undo')
        expect(page.locator('.ftth-node')).to_have_count(2)
        click('#redo')
        expect(page.locator('.ftth-node')).to_have_count(5)
        page.locator('#direction').select_option('up')
        expect(page.locator('#results-body')).to_contain_text('Dentro dos limites')
        page.locator('#direction').select_option('down')
        oldzoom = page.locator('#zoom-label').inner_text()
        click('#zoom-in')
        assert page.locator('#zoom-label').inner_text() != oldzoom
        click('#fit')
        # Move one component by keyboard, delete and undo.
        page.locator('.ftth-node').first.focus()
        page.keyboard.press('Enter')
        if width <= 900:
            click('#properties-close')
        click('#delete-node')
        expect(page.locator('.ftth-node')).to_have_count(4)
        click('#undo')
        expect(page.locator('.ftth-node')).to_have_count(5)
        if width <= 900:
            click('#components-toggle')
            expect(page.locator('#ftth-components')).to_be_visible()
            click('#components-close')
            expect(page.locator('#ftth-components')).not_to_be_visible()
        # Real pointer drag and background pan; history must restore coordinates.
        page.locator('#ftth-canvas').scroll_into_view_if_needed()
        node = page.locator('.ftth-node').first
        before = node.get_attribute('transform')
        box = node.locator('rect').first.bounding_box()
        page.mouse.move(box['x'] + 35, box['y'] + 25)
        page.mouse.down()
        page.mouse.move(box['x'] + 65, box['y'] + 55, steps=6)
        page.mouse.up()
        assert page.locator('.ftth-node').first.get_attribute('transform') != before
        if width <= 900:
            click('#properties-close')
        click('#undo')
        assert page.locator('.ftth-node').first.get_attribute('transform') == before
        box = page.locator('#ftth-canvas').bounding_box()
        scene_before = page.locator('#ftth-scene').get_attribute('transform')
        page.mouse.move(box['x'] + 8, box['y'] + 30)
        page.mouse.down()
        page.mouse.move(box['x'] + 28, box['y'] + 60, steps=4)
        page.mouse.up()
        assert page.locator('#ftth-scene').get_attribute('transform') != scene_before
        if width <= 900:
            # Chromium touch input exercises two-finger pinch through Pointer Events.
            cdp = context.new_cdp_session(page)
            x, y = box['x'] + box['width'] / 2, box['y'] + box['height'] / 2
            zoom_before = page.locator('#zoom-label').inner_text()
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x-30, 'y': y, 'id': 1}, {'x': x+30, 'y': y, 'id': 2}]})
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x-60, 'y': y, 'id': 1}, {'x': x+60, 'y': y, 'id': 2}]})
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
            assert page.locator('#zoom-label').inner_text() != zoom_before
        click('#fit')
        # Build and print the actual report, including network SVG and results.
        page.evaluate('window.print = () => {window.printRequested = true}')
        click('#report')
        assert page.evaluate('window.printRequested')
        assert page.locator('#ftth-print svg').count() == 1
        assert page.locator('#ftth-print tbody tr').count() == 2
        expect(page.locator('#ftth-print')).to_contain_text('Valores estimados')
        page.pdf(path=str(OUT / f'report-{width}.pdf'), print_background=True)
        assert (OUT / f'report-{width}.pdf').stat().st_size > 5000
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'overflow at {width}'
        page.screenshot(path=str(OUT / f'editor-{width}.png'), full_page=True)
        assert not errors, errors
        print(f'{width}px: UI creation, connection, calculation, persistence, import/export, undo/redo, PDF and layout OK', flush=True)
        context.close()
    browser.close()
