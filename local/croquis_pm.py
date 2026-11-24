#!/usr/bin/env python3
"""Croquis PM · versión local (sin conexión).

Sirve la aplicación en http://127.0.0.1:8765 y guarda en la carpeta `datos/`:
  - la propia app (index.html) y sus librerías (mapa, QR, tipografías),
  - los grifos de Aguas Andinas,
  - un mapa local de calles, numeración y edificios (OpenStreetMap) de las
    comunas que atiende el CBS, con buscador de direcciones y cruces.

Con internet la app usa el satélite de Esri como siempre; sin internet cambia
sola al mapa local. Los datos se actualizan solos cada 7 días (o desde el menú).

Solo usa la librería estándar de Python 3.9+.

Uso:
  python croquis_pm.py                 abre la app (y actualiza si corresponde)
  python croquis_pm.py --actualizar    fuerza la descarga de mapa y grifos
  python croquis_pm.py --construir-datos CARPETA   solo genera los datos (GitHub Actions)
"""
import json, math, os, re, shutil, socket, sqlite3, subprocess, sys, threading, time, unicodedata, zipfile
import urllib.parse, urllib.request
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

VERSION = '1.0'
PORT = 8765
APP_URL = 'https://lechugaluminio.github.io/Simulador-PM/index.html'
DATA_RELEASE = 'https://github.com/Lechugaluminio/Simulador-PM/releases/download/sin-conexion/mapa-cbs.zip'
GRIFOS_URL = 'https://www.aguasandinas.cl/documents/20450/27663/mapaGrifos.js/b58ce74b-3892-d995-edf6-d5575c4df511'
OVERPASS = ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter',
            'https://maps.mail.ru/osm/tools/overpass/api/interpreter']
UA = 'CroquisPM-local/' + VERSION + ' (https://github.com/Lechugaluminio/Simulador-PM)'
CHROME_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
MAX_AGE = 7 * 86400

# Comunas que atiende el Cuerpo de Bomberos de Santiago (bbox aproximado: S, O, N, E)
COMUNAS = {
    'Santiago':         (-33.4800, -70.6930, -33.4230, -70.6240),
    'Estación Central': (-33.4830, -70.7300, -33.4380, -70.6740),
    'Independencia':    (-33.4310, -70.6820, -33.3990, -70.6430),
    'Recoleta':         (-33.4330, -70.6600, -33.3620, -70.6130),
    'Renca':            (-33.4280, -70.7750, -33.3700, -70.6780),
    'Providencia':      (-33.4460, -70.6420, -33.4080, -70.5830),
    'Las Condes':       (-33.4450, -70.6020, -33.3560, -70.4400),
    'Vitacura':         (-33.4070, -70.6220, -33.3630, -70.5480),
    'Lo Barnechea':     (-33.3930, -70.6250, -33.2750, -70.4300),
}
BUFFER = 0.009   # ~1 km extra para despachos limítrofes
CHUNK = 0.03     # trozos de ~3 km para no saturar Overpass

VENDOR = {
    'maplibre-gl.js': ['https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js',
                       'https://cdn.jsdelivr.net/npm/maplibre-gl@4.7.1/dist/maplibre-gl.js'],
    'maplibre-gl.css': ['https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css',
                        'https://cdn.jsdelivr.net/npm/maplibre-gl@4.7.1/dist/maplibre-gl.css'],
    'qrcode.min.js': ['https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js',
                      'https://unpkg.com/qrcode-generator@1.4.4/qrcode.js'],
}
GLYPH_FONT = 'Open Sans Semibold'
GLYPH_RANGES = ['0-255', '256-511', '8192-8447']
GLYPH_URLS = ['https://demotiles.maplibre.org/font/{f}/{r}.pbf',
              'https://fonts.openmaptiles.org/{f}/{r}.pbf']
FONTS_CSS = 'https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Barlow:wght@500;600;700&display=swap'

# ---------------------------------------------------------------- rutas
if getattr(sys, 'frozen', False):          # ejecutable de PyInstaller
    BASE = os.path.dirname(sys.executable)
    BUNDLE = getattr(sys, '_MEIPASS', BASE)
else:
    BASE = os.path.dirname(os.path.abspath(__file__))
    BUNDLE = os.path.dirname(BASE)         # el index.html del repo está un nivel arriba
DATA = os.path.join(BASE, 'datos')
DB = os.path.join(DATA, 'mapa.sqlite')
META = os.path.join(DATA, 'estado.json')

STATUS = {'version': VERSION, 'updating': False, 'step': '', 'progress': 0, 'error': '', 'log': []}
_last_ping = [time.time()]
_db_lock = threading.Lock()


def log(msg):
    line = time.strftime('%H:%M:%S ') + msg
    print(line, flush=True)
    STATUS['log'] = (STATUS['log'] + [line])[-40:]


def load_meta():
    try:
        with open(META, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_meta(m):
    os.makedirs(DATA, exist_ok=True)
    tmp = META + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    os.replace(tmp, META)


def http_get(url, timeout=60, data=None, ua=UA, retries=2):
    last = None
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, data=data, headers={'User-Agent': ua, 'Accept-Encoding': 'identity'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa
            last = e
            time.sleep(2 + 3 * i)
    raise last


def online():
    try:
        socket.create_connection(('1.1.1.1', 443), timeout=4).close()
        return True
    except OSError:
        return False


# ---------------------------------------------------------------- texto
def norm(s):
    s = unicodedata.normalize('NFD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9 ]+', ' ', s).strip()


STOP = {'avenida', 'av', 'avda', 'calle', 'pasaje', 'psje', 'pje', 'general', 'gral', 'los', 'las', 'el', 'la',
        'de', 'del', 'presidente', 'pdte', 'doctor', 'dr', 'camino', 'diagonal', 'y', 'con'}


def tokens(s):
    return [t for t in norm(s).split() if t and t not in STOP]


# ---------------------------------------------------------------- geometría
def bbox_of(coords):
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return min(xs), min(ys), max(xs), max(ys)


def point_in_poly(x, y, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def assemble_rings(ways):
    """Une tramos (listas de [lon,lat]) en anillos cerrados."""
    segs = [list(w) for w in ways if len(w) >= 2]
    rings = []
    while segs:
        ring = segs.pop(0)
        changed = True
        while ring[0] != ring[-1] and changed:
            changed = False
            for k, s in enumerate(segs):
                if s[0] == ring[-1]:
                    ring += s[1:]
                elif s[-1] == ring[-1]:
                    ring += s[::-1][1:]
                elif s[-1] == ring[0]:
                    ring = s[:-1] + ring
                elif s[0] == ring[0]:
                    ring = s[::-1][:-1] + ring
                else:
                    continue
                segs.pop(k)
                changed = True
                break
        if len(ring) >= 4:
            rings.append(ring)
    return rings


M_LAT = 110574.0


def meters(a, b):
    kx = 111320.0 * math.cos(math.radians(-33.44))
    return math.hypot((a[0] - b[0]) * kx, (a[1] - b[1]) * M_LAT)


def closest_between(la, lb):
    """Punto medio más cercano entre dos conjuntos de polilíneas; devuelve (dist_m, [lon,lat])."""
    kx = 111320.0 * math.cos(math.radians(-33.44))
    best = (float('inf'), None)

    def proj(p):
        return (p[0] * kx, p[1] * M_LAT)

    def test(L1, L2):
        nonlocal best
        for l1 in L1:
            A = [proj(p) for p in l1]
            for l2 in L2:
                for c in l2:
                    v = proj(c)
                    for i in range(len(A) - 1):
                        ax, ay = A[i]
                        bx, by = A[i + 1]
                        dx, dy = bx - ax, by - ay
                        L = dx * dx + dy * dy
                        t = max(0.0, min(1.0, ((v[0] - ax) * dx + (v[1] - ay) * dy) / L)) if L else 0.0
                        qx, qy = ax + t * dx, ay + t * dy
                        d = math.hypot(qx - v[0], qy - v[1])
                        if d < best[0]:
                            best = (d, [((qx + v[0]) / 2) / kx, ((qy + v[1]) / 2) / M_LAT])
    test(la, lb)
    test(lb, la)
    if best[0] > 1:  # tramos que se cruzan sin compartir un vértice
        for l1 in la:
            A = [proj(p) for p in l1]
            for l2 in lb:
                B = [proj(p) for p in l2]
                for i in range(len(A) - 1):
                    (x1, y1), (x2, y2) = A[i], A[i + 1]
                    for k in range(len(B) - 1):
                        (x3, y3), (x4, y4) = B[k], B[k + 1]
                        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
                        if not den:
                            continue
                        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
                        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den
                        if 0 <= t <= 1 and 0 <= u <= 1:
                            return (0.0, [(x1 + t * (x2 - x1)) / kx, (y1 + t * (y2 - y1)) / M_LAT])
    return best


# ---------------------------------------------------------------- base de datos
SCHEMA = """
create table if not exists roads(id integer primary key, name text, nname text, kind text, rank int, geom text);
create virtual table if not exists roads_ix using rtree(id, minx, maxx, miny, maxy);
create table if not exists blds(id integer primary key, geom text);
create virtual table if not exists blds_ix using rtree(id, minx, maxx, miny, maxy);
create table if not exists addr(id integer primary key, street text, nstreet text, num text, lon real, lat real);
create virtual table if not exists addr_ix using rtree(id, minx, maxx, miny, maxy);
create table if not exists comunas(name text, geom text);
create table if not exists meta(k text primary key, v text);
create index if not exists roads_nname on roads(nname);
create index if not exists addr_nstreet on addr(nstreet);
"""
ROAD_RANK = {'motorway': 1, 'trunk': 1, 'primary': 2, 'secondary': 2, 'tertiary': 3, 'motorway_link': 3,
             'trunk_link': 3, 'primary_link': 3, 'secondary_link': 3, 'tertiary_link': 3,
             'residential': 4, 'unclassified': 4, 'living_street': 4, 'road': 4, 'service': 5, 'pedestrian': 5}


def chunks():
    seen = set()
    for (s, w, n, e) in COMUNAS.values():
        s, w, n, e = s - BUFFER, w - BUFFER, n + BUFFER, e + BUFFER
        y = math.floor(s / CHUNK) * CHUNK
        while y < n:
            x = math.floor(w / CHUNK) * CHUNK
            while x < e:
                k = (round(x, 4), round(y, 4))
                if k not in seen:
                    seen.add(k)
                    yield (y, x, y + CHUNK, x + CHUNK)
                x += CHUNK
            y += CHUNK


def overpass(q, timeout=240, tries=6):
    data = urllib.parse.urlencode({'data': q}).encode()
    last = None
    for attempt in range(tries):
        url = OVERPASS[attempt % len(OVERPASS)]
        try:
            raw = http_get(url, timeout=timeout, data=data, retries=0)
            return json.loads(raw)
        except Exception as e:  # noqa
            last = e
            log(f'  Overpass falló ({url.split("/")[2]}): {e}; reintento…')
            time.sleep(10 + 10 * attempt)
    raise RuntimeError(f'Overpass no respondió: {last}')


def fetch_box(s, w, n, e, hw_skip, depth=0):
    """Descarga una zona; si Overpass no da abasto, la divide en 4 y reintenta."""
    bb = f'{s:.5f},{w:.5f},{n:.5f},{e:.5f}'
    q = (f'[out:json][timeout:200];('
         f'way["highway"]["highway"!~"^({hw_skip})$"]({bb});'
         f'way["building"]({bb});'
         f'node["addr:housenumber"]["addr:street"]({bb});'
         f');out tags geom;')
    try:
        return overpass(q, tries=3 if depth < 2 else 6).get('elements', [])
    except Exception:
        if depth >= 2:
            raise
        ms, mw = (s + n) / 2, (w + e) / 2
        out = []
        for sub in ((s, w, ms, mw), (s, mw, ms, e), (ms, w, n, mw), (ms, mw, n, e)):
            out += fetch_box(*sub, hw_skip, depth + 1)
        return out


def build_map(dest_db, progress=lambda f, s: None):
    tmp = dest_db + '.nuevo'
    if os.path.exists(tmp):
        os.remove(tmp)
    con = sqlite3.connect(tmp)
    con.executescript(SCHEMA)
    names = '|'.join(re.escape(n) for n in COMUNAS)
    S = min(b[0] for b in COMUNAS.values()) - BUFFER
    W = min(b[1] for b in COMUNAS.values()) - BUFFER
    N = max(b[2] for b in COMUNAS.values()) + BUFFER
    E = max(b[3] for b in COMUNAS.values()) + BUFFER
    progress(0.01, 'Límites de comunas')
    try:
        j = overpass(f'[out:json][timeout:180];rel["boundary"="administrative"]["admin_level"="8"]["name"~"^({names})$"]({S},{W},{N},{E});out geom;')
        for el in j.get('elements', []):
            ways = [[[p['lon'], p['lat']] for p in m.get('geometry', [])] for m in el.get('members', [])
                    if m.get('type') == 'way' and m.get('role') in ('outer', '')]
            rings = assemble_rings(ways)
            if rings:
                con.execute('insert into comunas values(?,?)', (el['tags'].get('name'), json.dumps(rings)))
    except Exception as e:  # los límites son opcionales
        log(f'  Sin límites de comunas: {e}')
    con.commit()
    seen_w, seen_n = set(), set()
    cl = list(chunks())
    hw_skip = 'footway|path|steps|cycleway|track|bridleway|corridor|elevator|platform|proposed|construction|bus_stop|raceway|abandoned|razed|via_ferrata'
    for i, (s, w, n, e) in enumerate(cl):
        progress(0.03 + 0.95 * i / len(cl), f'Mapa: zona {i + 1} de {len(cl)}')
        els = fetch_box(s, w, n, e, hw_skip)
        rows_r, rows_b, rows_a = [], [], []
        for el in els:
            t = el.get('tags', {})
            if el['type'] == 'node':
                if el['id'] in seen_n:
                    continue
                seen_n.add(el['id'])
                rows_a.append((t.get('addr:street'), t.get('addr:housenumber'), el['lon'], el['lat']))
                continue
            if el['id'] in seen_w:
                continue
            seen_w.add(el['id'])
            g = [[round(p['lon'], 6), round(p['lat'], 6)] for p in el.get('geometry', []) if p]
            if len(g) < 2:
                continue
            if 'building' in t:
                rows_b.append(g)
                if t.get('addr:housenumber') and t.get('addr:street'):
                    cx = sum(p[0] for p in g) / len(g)
                    cy = sum(p[1] for p in g) / len(g)
                    rows_a.append((t['addr:street'], t['addr:housenumber'], cx, cy))
            elif 'highway' in t:
                kind = t['highway']
                rows_r.append((t.get('name') or t.get('ref') or '', kind, ROAD_RANK.get(kind, 5), g))
        for name, kind, rank, g in rows_r:
            cur = con.execute('insert into roads(name,nname,kind,rank,geom) values(?,?,?,?,?)',
                              (name, ' '.join(tokens(name)), kind, rank, json.dumps(g, separators=(',', ':'))))
            x0, y0, x1, y1 = bbox_of(g)
            con.execute('insert into roads_ix values(?,?,?,?,?)', (cur.lastrowid, x0, x1, y0, y1))
        for g in rows_b:
            cur = con.execute('insert into blds(geom) values(?)', (json.dumps(g, separators=(',', ':')),))
            x0, y0, x1, y1 = bbox_of(g)
            con.execute('insert into blds_ix values(?,?,?,?,?)', (cur.lastrowid, x0, x1, y0, y1))
        for st, num, x, y in rows_a:
            cur = con.execute('insert into addr(street,nstreet,num,lon,lat) values(?,?,?,?,?)',
                              (st, ' '.join(tokens(st)), num, x, y))
            con.execute('insert into addr_ix values(?,?,?,?,?)', (cur.lastrowid, x, x, y, y))
        con.commit()
        log(f'  zona {i + 1}/{len(cl)}: {len(rows_r)} calles, {len(rows_b)} edificios, {len(rows_a)} números')
        time.sleep(1.5)
    stamp = time.strftime('%Y-%m-%d')
    con.execute('insert or replace into meta values(?,?)', ('fecha', stamp))
    con.execute('insert or replace into meta values(?,?)', ('fuente', '© colaboradores de OpenStreetMap (ODbL)'))
    con.commit()
    n_r = con.execute('select count(*) from roads').fetchone()[0]
    n_b = con.execute('select count(*) from blds').fetchone()[0]
    n_a = con.execute('select count(*) from addr').fetchone()[0]
    con.execute('vacuum')
    con.close()
    with _db_lock:
        os.replace(tmp, dest_db)
    log(f'Mapa listo: {n_r} calles, {n_b} edificios, {n_a} números de casa.')
    return stamp


# ---------------------------------------------------------------- actualización
def update_vendor():
    vd = os.path.join(DATA, 'vendor')
    os.makedirs(vd, exist_ok=True)
    for name, urls in VENDOR.items():
        for u in urls:
            try:
                b = http_get(u, timeout=60)
                if len(b) > 1000:
                    with open(os.path.join(vd, name), 'wb') as f:
                        f.write(b)
                    break
            except Exception as e:  # noqa
                log(f'  {name}: {e}')
    gd = os.path.join(vd, 'glyphs', GLYPH_FONT)
    os.makedirs(gd, exist_ok=True)
    for r in GLYPH_RANGES:
        for tpl in GLYPH_URLS:
            try:
                b = http_get(tpl.format(f=urllib.parse.quote(GLYPH_FONT), r=r), timeout=30)
                if b:
                    with open(os.path.join(gd, r + '.pbf'), 'wb') as f:
                        f.write(b)
                    break
            except Exception as e:  # noqa
                log(f'  letras {r}: {e}')
    try:  # tipografías Barlow de la interfaz
        css = http_get(FONTS_CSS, ua=CHROME_UA).decode('utf-8')
        fd = os.path.join(vd, 'fonts')
        os.makedirs(fd, exist_ok=True)
        for k, u in enumerate(sorted(set(re.findall(r'url\((https://[^)]+)\)', css)))):
            fn = f'f{k}.woff2'
            with open(os.path.join(fd, fn), 'wb') as f:
                f.write(http_get(u))
            css = css.replace(u, '/vendor/fonts/' + fn)
        with open(os.path.join(vd, 'fonts.css'), 'w', encoding='utf-8') as f:
            f.write(css)
    except Exception as e:  # noqa
        log(f'  tipografías: {e}')


def update_app():
    try:
        b = http_get(APP_URL + '?v=' + str(int(time.time())), timeout=60)
        if b'Croquis' in b and len(b) > 50000:
            os.makedirs(os.path.join(DATA, 'app'), exist_ok=True)
            with open(os.path.join(DATA, 'app', 'index.html'), 'wb') as f:
                f.write(b)
            log('App actualizada desde GitHub.')
    except Exception as e:  # noqa
        log(f'  app: {e}')


def update_grifos():
    b = http_get(GRIFOS_URL, timeout=90)
    if b.count(b'"lg"') + b.count(b'lg:') < 1000:
        raise RuntimeError('el archivo de grifos vino vacío')
    with open(os.path.join(DATA, 'grifos.js'), 'wb') as f:
        f.write(b)


def download_prebuilt():
    """Intenta bajar el mapa ya preparado (lo genera GitHub cada semana)."""
    zp = os.path.join(DATA, 'mapa-cbs.zip')
    b = http_get(DATA_RELEASE, timeout=600, retries=1)
    with open(zp, 'wb') as f:
        f.write(b)
    with zipfile.ZipFile(zp) as z:
        tmp = DB + '.nuevo'
        with z.open('mapa.sqlite') as src, open(tmp, 'wb') as dst:
            shutil.copyfileobj(src, dst)
    os.remove(zp)
    con = sqlite3.connect(tmp)
    fecha = con.execute("select v from meta where k='fecha'").fetchone()[0]
    con.close()
    with _db_lock:
        os.replace(tmp, DB)
    return fecha


def run_update(force=False):
    if STATUS['updating']:
        return
    STATUS.update(updating=True, error='', progress=0, step='Comenzando')
    meta = load_meta()
    try:
        os.makedirs(DATA, exist_ok=True)
        if not online():
            raise RuntimeError('sin conexión a internet')
        STATUS.update(step='App y librerías', progress=0.02)
        update_app()
        update_vendor()
        meta['vendor'] = time.time()
        save_meta(meta)
        STATUS.update(step='Grifos de Aguas Andinas', progress=0.06)
        try:
            update_grifos()
            meta['grifos'] = time.time()
            save_meta(meta)
            log('Grifos actualizados.')
        except Exception as e:  # noqa
            log(f'  grifos: {e}')
            STATUS['error'] = 'No se pudieron actualizar los grifos (se mantienen los anteriores).'
        STATUS.update(step='Mapa de calles (descarga rápida)', progress=0.1)
        fecha = None
        try:
            fecha = download_prebuilt()
            log(f'Mapa preparado descargado ({fecha}).')
        except Exception as e:  # noqa
            log(f'  mapa preparado no disponible ({e}); se arma desde OpenStreetMap…')

            def prog(f, s):
                STATUS.update(progress=0.1 + 0.9 * f, step=s)
            fecha = build_map(DB, prog)
        meta['mapa'] = time.time()
        meta['mapa_fecha'] = fecha
        save_meta(meta)
        STATUS.update(step='Listo', progress=1)
    except Exception as e:  # noqa
        STATUS['error'] = str(e)
        log(f'Error al actualizar: {e}')
    finally:
        STATUS['updating'] = False


def needs_update():
    m = load_meta()
    return (not os.path.exists(DB)) or time.time() - m.get('mapa', 0) > MAX_AGE or time.time() - m.get('grifos', 0) > MAX_AGE


# ---------------------------------------------------------------- consultas
def db():
    if not os.path.exists(DB):
        return None
    con = sqlite3.connect('file:' + DB.replace('\\', '/') + '?mode=ro', uri=True, check_same_thread=False)
    return con


def features(bbox, z):
    w, s, e, n = bbox
    out = {'roads': [], 'blds': [], 'addr': []}
    con = db()
    if not con:
        return out
    try:
        maxrank = 2 if z < 13 else 3 if z < 14.5 else 4 if z < 16 else 5
        lim = 6000
        for name, kind, rank, g in con.execute(
                'select r.name,r.kind,r.rank,r.geom from roads_ix i join roads r on r.id=i.id '
                'where i.maxx>=? and i.minx<=? and i.maxy>=? and i.miny<=? and r.rank<=? limit ?',
                (w, e, s, n, maxrank, lim)):
            out['roads'].append({'type': 'Feature', 'properties': {'n': name, 'k': kind, 'r': rank},
                                 'geometry': {'type': 'LineString', 'coordinates': json.loads(g)}})
        if z >= 15.5:
            for (g,) in con.execute('select b.geom from blds_ix i join blds b on b.id=i.id '
                                    'where i.maxx>=? and i.minx<=? and i.maxy>=? and i.miny<=? limit 12000', (w, e, s, n)):
                c = json.loads(g)
                if c[0] != c[-1]:
                    c.append(c[0])
                out['blds'].append({'type': 'Feature', 'properties': {}, 'geometry': {'type': 'Polygon', 'coordinates': [c]}})
        if z >= 17.5:
            for num, x, y in con.execute('select a.num,a.lon,a.lat from addr_ix i join addr a on a.id=i.id '
                                         'where i.maxx>=? and i.minx<=? and i.maxy>=? and i.miny<=? limit 3000', (w, e, s, n)):
                out['addr'].append({'type': 'Feature', 'properties': {'h': num},
                                    'geometry': {'type': 'Point', 'coordinates': [x, y]}})
    finally:
        con.close()
    return out


_comunas_cache = []


def comuna_of(con, x, y):
    if not _comunas_cache:
        for name, g in con.execute('select name,geom from comunas'):
            _comunas_cache.append((name, json.loads(g)))
    for name, rings in _comunas_cache:
        for r in rings:
            if point_in_poly(x, y, r):
                return name
    return ''


def street_geoms(con, name, limit=400):
    tk = tokens(name)
    if not tk:
        return []
    main = max(tk, key=len)
    rows = con.execute("select nname, geom from roads where nname like ? and rank<=5 limit ?", ('%' + main + '%', limit * 3)).fetchall()
    out = []
    for nn, g in rows:
        parts = set(nn.split())
        if all(t in parts or any(p.startswith(t) for p in parts) for t in tk):
            out.append(json.loads(g))
    return out[:limit]


def search(q):
    con = db()
    if not con:
        return {'ok': False, 'msg': 'Todavía no hay mapa local. Conéctate a internet y usa “Actualizar mapa y grifos”.', 'results': []}
    try:
        q = q.strip()
        res = []
        head = q.split(',')[0]
        m = re.split(r'\s+(?:y|con|esq\.?|esquina)\s+|\s*[&/]\s*', head, flags=re.I)
        m = [x.strip() for x in m if x.strip()]
        if len(m) == 2:
            ga, gb = street_geoms(con, m[0]), street_geoms(con, m[1])
            if ga and gb:
                d, p = closest_between(ga, gb)
                if p and d < 150:
                    res.append({'lon': p[0], 'lat': p[1], 'label': f'{m[0]} con {m[1]}',
                                'detail': (comuna_of(con, *p) or 'Cruce') + ('' if d < 25 else f' · aprox. ±{round(d)} m'), 'cross': True})
            if not res:
                return {'ok': True, 'msg': 'No encontré ese cruce en el mapa local.', 'results': []}
            return {'ok': True, 'results': res}
        mm = re.match(r'^(.*?)[\s#nN°º.]*?(\d+[a-zA-Z]?)\s*$', head)
        if mm and tokens(mm.group(1)):
            street, num = mm.group(1), mm.group(2).upper()
            tk = tokens(street)
            main = max(tk, key=len)
            rows = con.execute('select street,nstreet,num,lon,lat from addr where nstreet like ? limit 3000', ('%' + main + '%',)).fetchall()
            exact = [r for r in rows if all(t in r[1].split() for t in tk) and str(r[2]).upper() == num]
            for st, _, n_, x, y in exact[:8]:
                res.append({'lon': x, 'lat': y, 'label': f'{st} {n_}', 'detail': comuna_of(con, x, y)})
            if not res:  # número más cercano de esa calle
                cand = [r for r in rows if all(t in r[1].split() for t in tk)]
                try:
                    target = int(re.sub(r'\D', '', num))
                    nums = []
                    for r in cand:
                        d = re.sub(r'\D', '', str(r[2]))
                        if d:
                            nums.append((abs(int(d) - target), r))
                    nums.sort(key=lambda t: t[0])
                    for dd, (st, _, n_, x, y) in nums[:5]:
                        res.append({'lon': x, 'lat': y, 'label': f'{st} {n_}', 'detail': (comuna_of(con, x, y) + ' · ' if comuna_of(con, x, y) else '') + f'número más cercano a {num}'})
                except ValueError:
                    pass
            if res:
                return {'ok': True, 'results': res}
            q = street
        # nombre de calle: un resultado por comuna
        geoms = street_geoms(con, q, limit=600)
        by_com = {}
        for g in geoms:
            mid = g[len(g) // 2]
            c = comuna_of(con, *mid) or 'Fuera de las comunas del CBS'
            by_com.setdefault(c, []).append(mid)
        for c, pts in by_com.items():
            x = sorted(p[0] for p in pts)[len(pts) // 2]
            y = sorted(p[1] for p in pts)[len(pts) // 2]
            res.append({'lon': x, 'lat': y, 'label': q.title(), 'detail': c})
        return {'ok': True, 'results': res[:10], 'msg': '' if res else 'Sin resultados en el mapa local.'}
    finally:
        con.close()


# ---------------------------------------------------------------- servidor
def app_html():
    p = os.path.join(DATA, 'app', 'index.html')
    if not os.path.exists(p):
        p = os.path.join(BUNDLE, 'index.html')
    with open(p, encoding='utf-8') as f:
        h = f.read()
    vd = os.path.join(DATA, 'vendor')
    if os.path.exists(os.path.join(vd, 'maplibre-gl.css')):
        h = h.replace('https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css', '/vendor/maplibre-gl.css')
    # siempre local: si no hay internet, un CSS remoto bloquearía la carga de la página
    h = re.sub(r'https://fonts\.googleapis\.com/css2\?[^"\']+', '/vendor/fonts.css', h)
    h = h.replace('<link rel="preconnect" href="https://fonts.googleapis.com">', '')
    if os.path.exists(os.path.join(DATA, 'grifos.js')):
        h = h.replace(GRIFOS_URL, '/local/grifos.js')
    return h


MIME = {'.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.pbf': 'application/x-protobuf',
        '.woff2': 'font/woff2', '.html': 'text/html; charset=utf-8', '.json': 'application/json', '.png': 'image/png',
        '.jpg': 'image/jpeg', '.mp4': 'video/mp4'}


class H(BaseHTTPRequestHandler):
    server_version = 'CroquisPM/' + VERSION

    def log_message(self, *a):
        pass

    def send(self, code, body, ctype='application/json', cache=False):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        elif isinstance(body, str):
            body = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'max-age=86400' if cache else 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def file(self, path):
        if not os.path.isfile(path):
            return self.send(404, 'no encontrado', 'text/plain')
        with open(path, 'rb') as f:
            self.send(200, f.read(), MIME.get(os.path.splitext(path)[1].lower(), 'application/octet-stream'), cache=True)

    def do_POST(self):
        if self.path.startswith('/local/update'):
            threading.Thread(target=run_update, args=(True,), daemon=True).start()
            return self.send(200, {'ok': True})
        self.send(404, {'ok': False})

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        p = u.path
        _last_ping[0] = time.time()
        if p in ('/', '/index.html'):
            return self.send(200, app_html(), 'text/html; charset=utf-8')
        if p == '/local/status':
            m = load_meta()
            st = dict(STATUS)
            fecha = m.get('mapa_fecha')
            if not fecha and os.path.exists(DB):
                try:
                    c = db()
                    fecha = c.execute("select v from meta where k='fecha'").fetchone()[0]
                    c.close()
                except Exception:
                    pass
            st.update(local=True, mapa=os.path.exists(DB), mapa_fecha=fecha,
                      grifos_t=m.get('grifos'), glyphs=os.path.isdir(os.path.join(DATA, 'vendor', 'glyphs', GLYPH_FONT)),
                      comunas=list(COMUNAS))
            return self.send(200, st)
        if p == '/local/ping':
            return self.send(200, {'ok': True})
        if p == '/local/features':
            try:
                bb = [float(x) for x in qs.get('bbox', [''])[0].split(',')]
                z = float(qs.get('z', ['16'])[0])
                with _db_lock:
                    return self.send(200, features(bb, z))
            except Exception as e:  # noqa
                return self.send(400, {'error': str(e)})
        if p == '/local/search':
            with _db_lock:
                return self.send(200, search(qs.get('q', [''])[0]))
        if p == '/local/grifos.js':
            return self.file(os.path.join(DATA, 'grifos.js'))
        if p.startswith('/vendor/'):
            rel = urllib.parse.unquote(p[len('/vendor/'):])
            full = os.path.normpath(os.path.join(DATA, 'vendor', rel))
            if not full.startswith(os.path.normpath(os.path.join(DATA, 'vendor'))):
                return self.send(403, 'no', 'text/plain')
            if rel == 'fonts.css' and not os.path.isfile(full):
                return self.send(200, '/* tipografías aún no descargadas */', 'text/css; charset=utf-8')
            return self.file(full)
        if p.startswith('/docs/'):
            return self.file(os.path.join(BUNDLE, 'docs', os.path.basename(p)))
        self.send(404, 'no encontrado', 'text/plain')


def already_running():
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/local/ping', timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def open_window(url):
    cands = []
    for env in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'):
        root = os.environ.get(env)
        if root:
            cands += [os.path.join(root, 'Google', 'Chrome', 'Application', 'chrome.exe'),
                      os.path.join(root, 'Microsoft', 'Edge', 'Application', 'msedge.exe')]
    cands += [shutil.which('google-chrome') or '', shutil.which('chromium') or '', shutil.which('microsoft-edge') or '']
    for c in cands:
        if c and os.path.isfile(c):
            try:
                subprocess.Popen([c, '--app=' + url, '--window-size=1400,900'])
                return
            except Exception:
                pass
    import webbrowser
    webbrowser.open(url)


def watchdog():
    """Apaga el servidor cuando la ventana lleva 3 minutos cerrada (y no hay actualización en curso)."""
    while True:
        time.sleep(30)
        if not STATUS['updating'] and time.time() - _last_ping[0] > 180:
            log('Ventana cerrada: se apaga Croquis PM local.')
            os._exit(0)


def main():
    args = sys.argv[1:]
    if args[:1] == ['--construir-datos']:
        out = args[1] if len(args) > 1 else 'salida'
        os.makedirs(out, exist_ok=True)
        dbp = os.path.join(out, 'mapa.sqlite')
        build_map(dbp, lambda f, s: None)
        with zipfile.ZipFile(os.path.join(out, 'mapa-cbs.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
            z.write(dbp, 'mapa.sqlite')
        return
    url = f'http://127.0.0.1:{PORT}/'
    if already_running():
        if '--actualizar' in args:
            urllib.request.urlopen(urllib.request.Request(url + 'local/update', data=b'', method='POST'), timeout=5)
        open_window(url)
        return
    os.makedirs(DATA, exist_ok=True)
    srv = ThreadingHTTPServer(('127.0.0.1', PORT), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    log(f'Croquis PM local {VERSION} en {url} · datos en {DATA}')
    if '--actualizar' in args or needs_update():
        threading.Thread(target=run_update, args=('--actualizar' in args,), daemon=True).start()
    if '--sin-ventana' not in args:
        open_window(url)
        threading.Thread(target=watchdog, daemon=True).start()
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
