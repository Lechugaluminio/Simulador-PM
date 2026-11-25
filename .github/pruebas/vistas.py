"""Prueba visual en GitHub Actions: carga un croquis de ejemplo y guarda capturas de las dos vistas."""
import json, os, sys
from playwright.sync_api import sync_playwright
OUT = 'capturas'; os.makedirs(OUT, exist_ok=True)
c = [-70.6668, -33.4062]
def off(dx, dy): return [c[0] + dx * 1e-5, c[1] + dy * 1e-5]
sq = [off(-30, -20), off(30, -20), off(30, 20), off(-30, 20)]
state = {'v': 1, 'title': 'Prueba vistas', 'address': 'Las Enredaderas & Fermín Vivaceta', 'startedAt': 1795500000000, 'center': c,
  'units': [
    {'id': 'u1', 'code': 'B-1', 'status': 'trabajando', 'fn': 'Ataque', 'side': '', 'note': '', 'wave': 'D', 'pos': off(-10, -45), 'arrivedAt': 1, 'addedAt': 1},
    {'id': 'u2', 'code': 'Z-3', 'status': 'trabajando', 'fn': 'Abastecimiento', 'side': '', 'note': '', 'wave': 'D', 'pos': off(-90, -60), 'arrivedAt': 1, 'addedAt': 2},
    {'id': 'u3', 'code': 'Q-7', 'status': 'lugar', 'fn': '', 'side': '', 'note': '', 'wave': '1', 'pos': off(45, -40), 'arrivedAt': 1, 'addedAt': 3}],
  'shapes': [
    {'id': 's1', 'kind': 'estructura', 'coords': sq, 'label': 'Casa 2 pisos', 'pisos': 2},
    {'id': 's2', 'kind': 'fuego', 'coords': [off(-25, -5), off(0, -5), off(0, 15), off(-25, 15)], 'label': '', 'piso': '1'},
    {'id': 's3', 'kind': 'humo', 'coords': [off(0, -15), off(25, -15), off(25, 15), off(0, 15)], 'label': 'humo denso', 'piso': '2'},
    {'id': 's4', 'kind': 'muro', 'coords': [off(-30, 20), off(30, 20)], 'label': ''},
    {'id': 's5', 'kind': 'ataque', 'coords': [off(-10, -45), off(-10, -25), off(-15, -5)], 'label': '1½"', 'color': '#2f7bff', 'piso': '1'},
    {'id': 's6', 'kind': 'abast', 'coords': [off(-130, -60), off(-90, -60), off(-10, -45)], 'label': 'grifo → Z-3 → B-1'},
    {'id': 's7', 'kind': 'corte', 'coords': [off(-60, -110), off(-60, -80)], 'label': 'cortada'}],
  'marks': [
    {'id': 'm1', 'kind': 'fuego', 'pos': off(-15, 5), 'text': '', 'piso': '1'},
    {'id': 'm2', 'kind': 'piton', 'pos': off(-12, -20), 'text': 'B-1', 'ptype': '1½"', 'rot': 0},
    {'id': 'm3', 'kind': 'victima', 'pos': off(15, 5), 'text': 'dormitorio', 'n': 2, 'vstate': 'confirmada', 'piso': '2'},
    {'id': 'm4', 'kind': 'pm', 'pos': off(-80, -100), 'text': ''},
    {'id': 'm5', 'kind': 'grifo', 'pos': off(-130, -60), 'text': ''},
    {'id': 'm6', 'kind': 'pap', 'pos': off(-110, -30), 'text': ''},
    {'id': 'm8', 'kind': 'victima', 'pos': off(-22, 12), 'text': 'piso 1', 'n': 1, 'vstate': 'rescatada'},
    {'id': 'm7', 'kind': 'mayday', 'pos': off(20, -10), 'text': '', 'piso': '2'}]}
errs = []
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    pg = b.new_page(viewport={'width': 1500, 'height': 900})
    pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
    pg.on('console', lambda m: errs.append('console.' + m.type + ': ' + m.text) if m.type == 'error' else None)
    pg.goto('http://127.0.0.1:8000/index.html')
    pg.evaluate("([s,v])=>{localStorage.setItem('croquisPM.state.v1',s);localStorage.setItem('croquisPM.view.v1',v);}",
                [json.dumps(state), json.dumps({'center': c, 'zoom': 18.6, 'bearing': 0})])
    pg.reload(); pg.wait_for_timeout(9000)
    pg.screenshot(path=f'{OUT}/1_territorio.png')
    pg.keyboard.press('Tab'); pg.wait_for_timeout(4000)
    pg.screenshot(path=f'{OUT}/2_estructura.png')
    pg.click('.fcol .fr[data-f="2"]'); pg.wait_for_timeout(800)
    pg.screenshot(path=f'{OUT}/2b_solo_piso2.png')
    pg.click('.fcol .fh button'); pg.wait_for_timeout(500)
    # mover la columna de pisos desde su encabezado y comprobar que vuelve al mismo lugar tras cambiar de vista
    hb = pg.locator('.fcol .fh').bounding_box()
    hx, hy = hb['x'] + 20, hb['y'] + hb['height'] / 2
    pg.mouse.move(hx, hy); pg.mouse.down(); pg.mouse.move(hx + 30, hy + 60, steps=4); pg.mouse.move(hx + 60, hy + 230, steps=6); pg.mouse.up(); pg.wait_for_timeout(500)
    b1 = pg.locator('.fcol').bounding_box()
    pg.keyboard.press('Tab'); pg.wait_for_timeout(2500); pg.keyboard.press('Tab'); pg.wait_for_timeout(3500)
    pg.screenshot(path=f'{OUT}/2c_columna_movida.png')
    b2 = pg.locator('.fcol').bounding_box()
    errs.append('info: columna movida a %d,%d; tras volver a Estructura %d,%d' % (b1['x'], b1['y'], b2['x'], b2['y']))
    # arrastrar el foco ya puesto, y arrastrar el botón Humo de la barra al mapa
    st0 = pg.evaluate("JSON.parse(localStorage.getItem('croquisPM.state.v1'))")
    fb = pg.locator('.m-fire').first.bounding_box()
    fx, fy = fb['x'] + fb['width'] / 2, fb['y'] + fb['height'] / 2
    pg.mouse.move(fx, fy); pg.mouse.down(); pg.mouse.move(fx + 20, fy + 20, steps=4); pg.mouse.move(fx + 70, fy + 50, steps=6); pg.mouse.up(); pg.wait_for_timeout(500)
    hb2 = pg.locator('#tools [data-mode="mk:humo"]').bounding_box()
    pg.mouse.move(hb2['x'] + hb2['width'] / 2, hb2['y'] + hb2['height'] / 2); pg.mouse.down()
    pg.mouse.move(hb2['x'] + 80, hb2['y'] + 40, steps=5); pg.mouse.move(1300, 300, steps=8); pg.mouse.up(); pg.wait_for_timeout(600)
    st1 = pg.evaluate("JSON.parse(localStorage.getItem('croquisPM.state.v1'))")
    f0 = [m for m in st0['marks'] if m['kind'] == 'fuego'][0]['pos']; f1 = [m for m in st1['marks'] if m['kind'] == 'fuego'][0]['pos']
    errs.append('info: foco movido %s -> %s; humos antes %d, después %d; zonas de humo que quedan %d' % (
        [round(v, 6) for v in f0], [round(v, 6) for v in f1], sum(m['kind'] == 'humo' for m in st0['marks']), sum(m['kind'] == 'humo' for m in st1['marks']),
        sum(x['kind'] == 'humo' for x in st1['shapes'])))
    pg.screenshot(path=f'{OUT}/2d_foco_y_humo.png')
    # dibujar una línea de ataque nueva (la punta es el pitón) y elegir monitor
    pg.keyboard.press('l'); pg.mouse.click(700, 660); pg.wait_for_timeout(300); pg.mouse.dblclick(760, 470); pg.wait_for_timeout(1200)
    pg.click('#panel [data-act="lpt"][data-v="monitor"]'); pg.wait_for_timeout(800)
    pg.screenshot(path=f'{OUT}/3_linea_monitor.png')
    pg.keyboard.press('Escape'); pg.keyboard.press('Escape')
    # panel de la línea de ataque (diámetros en mm)
    pg.mouse.click(824, 572); pg.wait_for_timeout(1000)
    pg.screenshot(path=f'{OUT}/3b_linea_panel.png')
    pg.keyboard.press('Escape'); pg.keyboard.press('Escape')
    # imagen exportada
    pg.click('#btnShare'); pg.wait_for_timeout(400)
    pg.click('[data-share="snap"]')
    pg.wait_for_timeout(9000)
    pg.screenshot(path=f'{OUT}/4_imagen.png')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    pg.keyboard.press('Tab'); pg.wait_for_timeout(3000)
    pg.screenshot(path=f'{OUT}/5_territorio_otra_vez.png')
    # pantalla de notebook: la barra de herramientas debe caber sin desplazarse
    pg.set_viewport_size({'width': 1366, 'height': 768}); pg.wait_for_timeout(800)
    pg.keyboard.press('Tab'); pg.wait_for_timeout(3500)
    pg.screenshot(path=f'{OUT}/6_estructura_1366x768.png')
    errs.append('info: barra ' + pg.evaluate("(()=>{const t=document.querySelector('#tools');return t.className+' '+t.scrollHeight+'/'+t.clientHeight})()"))
    # torre de 37 pisos: lista con scroll y botón para ver el edificio completo
    tsq = [off(-25, -25), off(25, -25), off(25, 25), off(-25, 25)]
    def zona(kind, piso, dx=0):
        return {'id': 'z%s%s' % (kind, piso), 'kind': kind, 'coords': [off(-20 + dx, -20), off(0 + dx, -20), off(0 + dx, 0), off(-20 + dx, 0)], 'label': '', 'piso': piso}
    torre = {'v': 1, 'title': 'Torre 37 pisos', 'address': 'Prueba', 'startedAt': 1795500000000, 'center': c, 'units': [],
      'shapes': [{'id': 't1', 'kind': 'estructura', 'coords': tsq, 'label': 'Torre', 'pisos': 37, 'subt': 3},
        zona('fuego', '18'), zona('humo', '18', 20), zona('humo', '19', 20), zona('humo', '20', 20), zona('colapso', '17'),
        {'id': 'l1', 'kind': 'ataque', 'coords': [off(-60, -60), off(-10, -10)], 'label': '52 mm · B-1', 'color': '#2f7bff', 'piso': '18'},
        {'id': 'l2', 'kind': 'ataque', 'coords': [off(60, -60), off(10, -10)], 'label': '52 mm · B-2', 'color': '#2f7bff', 'piso': '18'},
        {'id': 'l3', 'kind': 'ataque', 'coords': [off(60, 60), off(10, 10)], 'label': '38 mm · Q-7', 'color': '#2f7bff', 'piso': '19'}],
      'marks': [{'id': 'v1', 'kind': 'victima', 'pos': off(5, 5), 'text': '', 'n': 3, 'vstate': 'confirmada', 'piso': '19'},
        {'id': 'v2', 'kind': 'victima', 'pos': off(-5, 10), 'text': '', 'n': 1, 'vstate': 'confirmada', 'piso': '25'},
        {'id': 'my', 'kind': 'mayday', 'pos': off(10, -5), 'text': '', 'piso': '19'}]}
    pg.evaluate("([s,v])=>{localStorage.setItem('croquisPM.state.v1',s);localStorage.setItem('croquisPM.view.v1',v);}",
                [json.dumps(torre), json.dumps({'center': c, 'zoom': 18.8, 'bearing': 0})])
    pg.reload(); pg.wait_for_timeout(7000)
    if pg.locator('body.view-terr').count(): pg.keyboard.press('Tab'); pg.wait_for_timeout(3000)
    pg.screenshot(path=f'{OUT}/7_torre.png')
    pg.click('.fcol [data-x]'); pg.wait_for_timeout(800)
    pg.screenshot(path=f'{OUT}/8_torre_completa.png')
    pg.click('.fcol [data-x]'); pg.wait_for_timeout(300)
    pg.click('.fcol [data-c]'); pg.wait_for_timeout(600)
    pg.screenshot(path=f'{OUT}/8b_torre_solo_con_algo.png')
    pg.click('#btnShare'); pg.wait_for_timeout(400); pg.click('[data-share="snap"]'); pg.wait_for_timeout(8000)
    pg.screenshot(path=f'{OUT}/9_torre_imagen.png')
    b.close()
open(f'{OUT}/errores.txt', 'w').write('\n'.join(errs) or 'sin errores')
print('\n'.join(errs) or 'sin errores')
