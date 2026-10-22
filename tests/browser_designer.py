"""Stage 1 visual and graph acceptance tests; no production services or databases."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('LIGNET_PREVIEW_URL', 'http://127.0.0.1:8101')
OUT = Path('/tmp/lignet-designer-qa')
OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    for width in (320, 375, 768, 1024, 1920):
        context = browser.new_context(viewport={'width': width, 'height': 1000}, has_touch=width <= 900)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.route('https://cdn.jsdelivr.net/**', lambda r: r.abort())
        page.route('https://www.googletagmanager.com/**', lambda r: r.abort())
        page.goto(BASE + '/ferramentas/projetista-ftth/', wait_until='domcontentloaded')
        expect(page.locator('#palette-items button')).to_have_count(13)
        checks = page.evaluate('''async () => {
          const m = await import('/static/ftth_designer/engine.js');
          let checks=0;const assert=(v,msg)=>{if(!v)throw Error(msg);checks++};
          const p=m.empty(),a=m.createNode('olt'),s=m.createNode('asymmetric'),b=m.createNode('cto'),o=m.createNode('onu');p.nodes=[a,s,b,o];
          function edge(from,to,port=0){return {id:crypto.randomUUID(),from:from.id,to:to.id,port,targetPort:0,fiber:m.fiber()};}
          p.edges=[edge(a,s),edge(s,b,1),edge(b,o)];m.validate(p);
          assert(Math.abs(m.asymmetricLoss(10)-10)<1e-12,'10% loss');
          assert(Math.abs(m.asymmetricLoss(90)-.457574905606751)<1e-12,'90% loss');
          assert(m.asymmetricLoss(10,.2,10.7)===10.7,'real loss override');
          assert(m.portLabel(s,1).startsWith('90%'),'output mapping');
          assert(!!m.connectionError(p,o.id,a.id,0),'ONU source');
          assert(!!m.connectionError(p,s.id,o.id,2),'capacity');
          assert(!!m.connectionError(p,s.id,o.id,1),'occupied port');
          assert(!!m.connectionError(p,b.id,s.id,1),'cycle');
          const f=m.fiber();f.km=2;assert(m.fiberLoss(f,1310)===.7,'fiber loss');assert(m.fiberLoss(f,1577)===null,'unknown attenuation');
          const bad=structuredClone(p);bad.edges[0].fiber.km=-1;let rejected=false;try{m.validate(bad)}catch{rejected=true}assert(rejected,'negative distance');
          assert(JSON.stringify(m.validate(p))===JSON.stringify(p),'graph roundtrip');
          const chain=m.empty(),u=m.createNode('splice'),v=m.createNode('splice');chain.nodes=[u,v];chain.edges=[edge(u,v)];assert(!!m.connectionError(chain,v.id,u.id,0),'real cycle rejection');
          for(const ratio of Object.keys(m.BALANCED).map(Number)){const n=m.createNode('balanced',0,0,ratio);assert(n.ports===ratio,'balanced physical outputs');}
          return checks;
        }''')
        mobile = width <= 900
        def open_palette():
            if mobile and not page.locator('#designer-palette').is_visible():
                page.locator('#palette-toggle').click()
        def close_properties():
            if mobile and page.locator('#designer-properties').is_visible():
                page.locator('#properties-close').click()
        open_palette()
        page.locator('#palette-items [data-type=olt]').click()
        form = page.locator('#properties-form')
        form.locator('[name=x]').fill('80')
        form.locator('[name=y]').fill('20')
        form.locator('button[type=submit]').click()
        close_properties()
        open_palette()
        page.locator('#palette-items [data-type=asymmetric]').click()
        form.locator('[name=x]').fill('80')
        form.locator('[name=y]').fill('260')
        form.locator('[name=ratio]').select_option('15')
        form.locator('button[type=submit]').click()
        expect(page.locator('[data-node]').last).to_contain_text('15/85')
        close_properties()
        if mobile:
            page.locator('#palette-close').click()
        page.locator('#fit').click()
        page.locator('[data-mode=connect]').click()
        page.locator('[data-node]').first.focus()
        page.keyboard.press('Enter')
        expect(page.locator('[data-node]').first).to_be_focused()
        page.keyboard.press('Tab')
        page.keyboard.press('Enter')
        expect(page.locator('[data-edge]')).to_have_count(1)
        page.locator('[data-mode=move]').click()
        page.locator('[data-edge]').focus()
        page.keyboard.press('Enter')
        form.locator('[name="fiber.km"]').fill('2.5')
        form.locator('button[type=submit]').click()
        expect(page.locator('[data-edge]')).to_contain_text('2,5 km')
        close_properties()
        page.locator('[data-node]').last.focus()
        page.keyboard.press('Enter')
        close_properties()
        page.locator('#duplicate').click()
        expect(page.locator('[data-node]')).to_have_count(3)
        close_properties()
        page.locator('#undo').click()
        expect(page.locator('[data-node]')).to_have_count(2)
        page.locator('#redo').click()
        expect(page.locator('[data-node]')).to_have_count(3)
        page.locator('[data-node]').last.focus()
        page.keyboard.press('Enter')
        close_properties()
        page.locator('#delete').click()
        expect(page.locator('[data-node]')).to_have_count(2)
        page.locator('#theme').click()
        expect(page.locator('#designer')).to_have_class('dark')
        page.locator('#grid').click()
        expect(page.locator('#canvas-background')).to_have_attribute('fill', 'transparent')
        expect(page.locator('#save-state')).to_have_text('Salvo neste navegador')
        page.reload(wait_until='domcontentloaded')
        expect(page.locator('[data-node]')).to_have_count(2)
        expect(page.locator('[data-edge]')).to_have_count(1)
        page.locator('#fit').click()
        # Pointer dragging and keyboard movement preserve graph/history.
        page.locator('#designer-canvas').scroll_into_view_if_needed()
        node=page.locator('[data-node]').first
        before=node.get_attribute('transform')
        box=node.locator('rect').bounding_box()
        page.mouse.move(box['x']+30,box['y']+25)
        page.mouse.down()
        page.mouse.move(box['x']+60,box['y']+55,steps=5)
        page.mouse.up()
        assert page.locator('[data-node]').first.get_attribute('transform')!=before
        close_properties()
        page.locator('#undo').click()
        assert page.locator('[data-node]').first.get_attribute('transform')==before
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        if mobile:
            page.locator('#designer-canvas').scroll_into_view_if_needed()
            box=page.locator('#designer-canvas').bounding_box()
            x,y=box['x']+box['width']/2,box['y']+box['height']/2
            zoom_before=page.locator('#zoom-label').inner_text()
            cdp=context.new_cdp_session(page)
            cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x-25,'y':y,'id':1},{'x':x+25,'y':y,'id':2}]})
            cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-50,'y':y,'id':1},{'x':x+50,'y':y,'id':2}]})
            cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
            assert page.locator('#zoom-label').inner_text()!=zoom_before
            page.locator('#fit').click()
        expect(page.locator('#save-state')).to_have_text('Salvo neste navegador')
        page.locator('#help').click()
        expect(page.locator('#designer-help')).to_be_visible()
        page.screenshot(path=str(OUT/f'editor-{width}.png'),full_page=True)
        assert not errors, errors
        print(f'{width}px: {checks} engine checks; graph, ports, edit, undo/redo, autosave, drag and layout OK',flush=True)
        context.close()
    browser.close()
