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
    {'id': 's1', 'kind': 'estructura', 'coords': sq, 'label': 'Casa 2 pisos'},
    {'id': 's2', 'kind': 'fuego', 'coords': [off(-25, -5), off(0, -5), off(0, 15), off(-25, 15)], 'label': ''},
    {'id': 's3', 'kind': 'humo', 'coords': [off(0, -15), off(25, -15), off(25, 15), off(0, 15)], 'label': 'humo denso'},
    {'id': 's4', 'kind': 'muro', 'coords': [off(-30, 20), off(30, 20)], 'label': ''},
    {'id': 's5', 'kind': 'ataque', 'coords': [off(-10, -45), off(-10, -25), off(-15, -5)], 'label': '1½"', 'color': '#2f7bff'},
    {'id': 's6', 'kind': 'abast', 'coords': [off(-130, -60), off(-90, -60), off(-10, -45)], 'label': 'grifo → Z-3 → B-1'},
    {'id': 's7', 'kind': 'corte', 'coords': [off(-60, -110), off(-60, -80)], 'label': 'cortada'}],
  'marks': [
    {'id': 'm1', 'kind': 'fuego', 'pos': off(-15, 5), 'text': ''},
    {'id': 'm2', 'kind': 'piton', 'pos': off(-12, -20), 'text': 'B-1', 'ptype': '1½"', 'rot': 0},
    {'id': 'm3', 'kind': 'victima', 'pos': off(15, 5), 'text': 'piso 2', 'n': 2, 'vstate': 'confirmada'},
    {'id': 'm4', 'kind': 'pm', 'pos': off(-80, -100), 'text': ''},
    {'id': 'm5', 'kind': 'grifo', 'pos': off(-130, -60), 'text': ''},
    {'id': 'm6', 'kind': 'pap', 'pos': off(-110, -30), 'text': ''},
    {'id': 'm7', 'kind': 'mayday', 'pos': off(20, -10), 'text': 'piso 2'}]}
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
    # crear un pitón nuevo con la herramienta
    pg.keyboard.press('i'); pg.mouse.click(760, 520); pg.wait_for_timeout(1500)
    pg.screenshot(path=f'{OUT}/3_piton_panel.png')
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
    b.close()
open(f'{OUT}/errores.txt', 'w').write('\n'.join(errs) or 'sin errores')
print('\n'.join(errs) or 'sin errores')
