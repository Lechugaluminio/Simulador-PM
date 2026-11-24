#!/usr/bin/env python3
"""Arma datos/mapa.sqlite desde un extracto .osm.pbf (lo usa GitHub Actions cada semana).

Más rápido y estable que Overpass para el área completa del CBS.
Requiere: pip install osmium   ·   uso: python mapa_desde_pbf.py extracto.osm.pbf salida/
"""
import json, os, sqlite3, sys, time, zipfile
import osmium
import croquis_pm as C

SKIP = set('footway path steps cycleway track bridleway corridor elevator platform proposed construction bus_stop raceway abandoned razed via_ferrata'.split())


def main(pbf, out):
    os.makedirs(out, exist_ok=True)
    dbp = os.path.join(out, 'mapa.sqlite')
    if os.path.exists(dbp):
        os.remove(dbp)
    con = sqlite3.connect(dbp)
    con.executescript(C.SCHEMA)
    S = min(b[0] for b in C.COMUNAS.values()) - C.BUFFER
    W = min(b[1] for b in C.COMUNAS.values()) - C.BUFFER
    N = max(b[2] for b in C.COMUNAS.values()) + C.BUFFER
    E = max(b[3] for b in C.COMUNAS.values()) + C.BUFFER
    boxes = [(s - C.BUFFER, w - C.BUFFER, n + C.BUFFER, e + C.BUFFER) for (s, w, n, e) in C.COMUNAS.values()]

    def inside(x, y):
        return any(s <= y <= n and w <= x <= e for (s, w, n, e) in boxes)

    stats = {'r': 0, 'b': 0, 'a': 0}
    comunas = {}

    class H(osmium.SimpleHandler):
        def node(self, n):
            t = n.tags
            if 'addr:housenumber' in t and 'addr:street' in t and n.location.valid() and inside(n.location.lon, n.location.lat):
                x, y = n.location.lon, n.location.lat
                cur = con.execute('insert into addr(street,nstreet,num,lon,lat) values(?,?,?,?,?)',
                                  (t['addr:street'], ' '.join(C.tokens(t['addr:street'])), t['addr:housenumber'], x, y))
                con.execute('insert into addr_ix values(?,?,?,?,?)', (cur.lastrowid, x, x, y, y))
                stats['a'] += 1

        def way(self, w):
            t = w.tags
            hw = t.get('highway')
            bl = t.get('building')
            if not hw and not bl:
                return
            if hw in SKIP and not bl:
                return
            try:
                g = [[round(p.lon, 6), round(p.lat, 6)] for p in w.nodes if p.location.valid()]
            except osmium.InvalidLocationError:
                return
            if len(g) < 2:
                return
            x0, y0, x1, y1 = C.bbox_of(g)
            if not inside((x0 + x1) / 2, (y0 + y1) / 2):
                return
            js = json.dumps(g, separators=(',', ':'))
            if bl:
                cur = con.execute('insert into blds(geom) values(?)', (js,))
                con.execute('insert into blds_ix values(?,?,?,?,?)', (cur.lastrowid, x0, x1, y0, y1))
                stats['b'] += 1
                if t.get('addr:housenumber') and t.get('addr:street'):
                    cx, cy = sum(p[0] for p in g) / len(g), sum(p[1] for p in g) / len(g)
                    cur = con.execute('insert into addr(street,nstreet,num,lon,lat) values(?,?,?,?,?)',
                                      (t['addr:street'], ' '.join(C.tokens(t['addr:street'])), t['addr:housenumber'], cx, cy))
                    con.execute('insert into addr_ix values(?,?,?,?,?)', (cur.lastrowid, cx, cx, cy, cy))
                    stats['a'] += 1
            else:
                name = t.get('name') or t.get('ref') or ''
                cur = con.execute('insert into roads(name,nname,kind,rank,geom) values(?,?,?,?,?)',
                                  (name, ' '.join(C.tokens(name)), hw, C.ROAD_RANK.get(hw, 5), js))
                con.execute('insert into roads_ix values(?,?,?,?,?)', (cur.lastrowid, x0, x1, y0, y1))
                stats['r'] += 1


    print(time.strftime('%H:%M:%S'), 'leyendo', pbf, flush=True)
    H().apply_file(pbf, locations=True, idx='flex_mem')
    con.commit()
    # límites de comunas: consulta chica a Overpass
    if not comunas:
        try:
            names = '|'.join(C.re.escape(n) for n in C.COMUNAS)
            j = C.overpass(f'[out:json][timeout:180];rel["boundary"="administrative"]["admin_level"="8"]["name"~"^({names})$"]({S},{W},{N},{E});out geom;')
            for el in j.get('elements', []):
                ways = [[[p['lon'], p['lat']] for p in m.get('geometry', [])] for m in el.get('members', [])
                        if m.get('type') == 'way' and m.get('role') in ('outer', '')]
                rings = C.assemble_rings(ways)
                if rings:
                    comunas[el['tags']['name']] = rings
        except Exception as e:  # noqa
            print('sin límites de comunas:', e)
    for name, rings in comunas.items():
        con.execute('insert into comunas values(?,?)', (name, json.dumps(rings)))
    con.execute('insert or replace into meta values(?,?)', ('fecha', time.strftime('%Y-%m-%d')))
    con.execute('insert or replace into meta values(?,?)', ('fuente', '© colaboradores de OpenStreetMap (ODbL) · Geofabrik'))
    con.commit()
    con.execute('vacuum')
    con.close()
    print(time.strftime('%H:%M:%S'), f"listo: {stats['r']} calles, {stats['b']} edificios, {stats['a']} números, {len(comunas)} comunas", flush=True)
    with zipfile.ZipFile(os.path.join(out, 'mapa-cbs.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(dbp, 'mapa.sqlite')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'salida')
