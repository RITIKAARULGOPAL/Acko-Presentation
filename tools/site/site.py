"""Site analysis data for the test-fit deck.

  python3 site.py prep                      raw/ → context.json   (map, wind, climate; needs fetch.py's raw data)
  python3 site.py build realfit.json OUT    context.json + the plan → OUT (site.json, spliced into the deck)

Map coordinates are metres east/south of the site centre (SVG y down), north up.
Plan coordinates are the deck's drawing units (50 mm, from realfit.json).
"""
import csv, json, math, os, sys, collections, heapq, datetime
from shapely.geometry import Polygon, LineString, Point, MultiPolygon, MultiLineString, box, shape
from shapely.ops import unary_union, nearest_points
from shapely.prepared import prep
from shapely import affinity

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'raw')
CONTEXT = os.path.join(HERE, 'context.json')
FACTS = os.path.join(HERE, 'facts.json')
LAT, LNG = 12.9311125, 77.614453            # plus code 7J4VWJJ7+CQW
TZ = 5.5                                    # IST
KX = math.cos(math.radians(LAT)) * 111320.0
KY = 110574.0
def en(lng, lat): return ((lng - LNG) * KX, (lat - LAT) * KY)
def r(v, n=0): return round(v, n) if n else int(round(v))
def load(name): return json.load(open(os.path.join(RAW, name)))['features']
def name_of(f): return ((f.get('names') or {}).get('primary') or '').strip()

# ======================================================================
# PREP: open data → context.json
# ======================================================================
def geoms_en(g):
    """GeoJSON-ish geometry in lng/lat → shapely in local metres (north up)."""
    s = shape(g)
    return affinity.affine_transform(s, [KX, 0, 0, KY, -LNG * KX, -LAT * KY])

def site_footprint(B):
    wings = [geoms_en(f['geometry']) for f in B if name_of(f) in ('Wing A', 'Wing B', 'Wing C')
             and geoms_en(f['geometry']).distance(Point(0, 0)) < 200]
    assert len(wings) == 3, 'expected the three Regalium wings in the building data'
    fp = unary_union([w.buffer(0.8, join_style=2) for w in wings]).buffer(-0.8, join_style=2)   # the wings touch with small drawing gaps
    edges = []
    for w in wings:
        c = list(w.exterior.coords)
        for (x0, y0), (x1, y1) in zip(c, c[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            if L > 40: edges.append((L, math.degrees(math.atan2(x1 - x0, y1 - y0)) % 90))   # the long façades set the grid
    # length-weighted circular mean of edge bearings, mod 90°
    s = sum(L * math.sin(math.radians(4 * b)) for L, b in edges); c = sum(L * math.cos(math.radians(4 * b)) for L, b in edges)
    grid = (math.degrees(math.atan2(s, c)) / 4) % 90
    return fp, wings, grid, edges

def path_d(geom, ox, oy, nd=0):
    """shapely (metres, north up) → SVG path data relative to (ox, oy), y down."""
    def ring(coords):
        pts = [(r(x - ox, nd), r(oy - y, nd)) for x, y in coords]
        out = [pts[0]]
        for p in pts[1:]:
            if p != out[-1]: out.append(p)
        if len(out) < 3: return ''
        s = 'M%s %s' % out[0]
        for (a, b), (c, d) in zip(out, out[1:]): s += 'l%s %s' % (r(c - a, nd), r(d - b, nd))
        return s + 'z'
    def line(coords):
        pts = [(r(x - ox, nd), r(oy - y, nd)) for x, y in coords]
        out = [pts[0]]
        for p in pts[1:]:
            if p != out[-1]: out.append(p)
        if len(out) < 2: return ''
        s = 'M%s %s' % out[0]
        for (a, b), (c, d) in zip(out, out[1:]): s += 'l%s %s' % (r(c - a, nd), r(d - b, nd))
        return s
    if geom.is_empty: return ''
    t = geom.geom_type
    if t == 'Polygon': return ''.join(ring(x.coords) for x in [geom.exterior] + list(geom.interiors))
    if t == 'LineString': return line(geom.coords)
    if hasattr(geom, 'geoms'): return ''.join(path_d(g, ox, oy, nd) for g in geom.geoms)
    return ''

ROAD_W = {'motorway': 16, 'trunk': 16, 'primary': 14, 'secondary': 10, 'tertiary': 8, 'unclassified': 6, 'residential': 5,
          'living_street': 4, 'service': 3, 'unknown': 4, 'pedestrian': 3, 'footway': 1.6, 'path': 1.6, 'steps': 1.6, 'track': 2.5}
ROAD_RANK = {'motorway': 0, 'trunk': 0, 'primary': 0, 'secondary': 1, 'tertiary': 2, 'unclassified': 3, 'residential': 3,
             'living_street': 3, 'unknown': 3, 'service': 4, 'pedestrian': 5, 'footway': 5, 'path': 5, 'steps': 5, 'track': 5}
ALIAS = {'Doctor M H Marigowda Road': 'Dr M H Marigowda Road', 'Dr. M H Marigowda Road': 'Dr M H Marigowda Road',
         'Sarjapura Road': 'Sarjapur Road', 'Jyothi Nivas College Road': 'Jyoti Nivas College Road'}

def walk_graph(S):
    """pedestrian graph from road segments: nodes are shared vertices (Overture splits at junctions)."""
    G = collections.defaultdict(list)
    for f in S:
        if f.get('subtype') != 'road' or f.get('class') in ('motorway',): continue
        pts = [en(*c) for c in f['geometry']['coordinates']]
        keys = [(round(x, 1), round(y, 1)) for x, y in pts]
        for a, b in zip(keys, keys[1:]):
            d = math.dist(a, b); G[a].append((b, d)); G[b].append((a, d))
    return G

def dijkstra(G, src):
    dist = {src: 0}; pq = [(0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]: continue
        for v, w in G[u]:
            nd = d + w
            if nd < dist.get(v, 1e18): dist[v] = nd; heapq.heappush(pq, (nd, v))
    return dist

def nearest_node(G, p, maxd=120):
    best = min(G, key=lambda k: (k[0] - p[0]) ** 2 + (k[1] - p[1]) ** 2)
    return best if math.dist(best, p) < maxd else None

def wind_rose():
    S16 = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    seasons = [('winter', 'Dec–Feb', (12, 1, 2)), ('summer', 'Mar–May', (3, 4, 5)), ('monsoon', 'Jun–Sep', (6, 7, 8, 9)), ('postmonsoon', 'Oct–Nov', (10, 11))]
    acc = {k: {'n': 0, 'calm': 0, 'sec': [0] * 16, 'spd': [0.0] * 16, 'sum': 0.0, 'm': 0} for k, _, _ in seasons + [('year', 'All year', tuple(range(1, 13)))]}
    years = set()
    for line in open(os.path.join(RAW, 'isd_432950.txt')):
        f = line.split()
        if len(f) < 9: continue
        y, mo, d, s = int(f[0]), int(f[1]), int(f[7]), int(f[8])
        if d == -9999 or s == -9999: continue
        years.add(y)
        for k, _, months in seasons + [('year', '', tuple(range(1, 13)))]:
            if mo not in months: continue
            a = acc[k]; a['n'] += 1
            if s == 0 or d == 0: a['calm'] += 1; continue
            i = int(((d % 360) + 11.25) // 22.5) % 16
            a['sec'][i] += 1; a['spd'][i] += s / 10; a['sum'] += s / 10; a['m'] += 1
    out = []
    for k, lab, months in seasons + [('year', 'All year', ())]:
        a = acc[k]
        sec = [r(100 * c / a['n'], 1) for c in a['sec']]
        top = sorted(range(16), key=lambda i: -a['sec'][i])[:2]
        out.append({'id': k, 'label': lab, 'calm': r(100 * a['calm'] / a['n']), 'mean': r(a['sum'] / max(1, a['m']), 1), 'n': a['n'],
                    'pct': sec, 'spd': [r(a['spd'][i] / a['sec'][i], 1) if a['sec'][i] else 0 for i in range(16)],
                    'top': [S16[i] for i in top]})
    return {'station': 'IMD Bangalore (WMO 43295), 5 km NNW of the site', 'years': [min(years), max(years)], 'dirs': S16, 'seasons': out,
            'source': 'NOAA NCEI Integrated Surface Database (ISD-lite), 3-hourly observations'}

def climate():
    Y0, Y1 = 1991, 2020
    v = collections.defaultdict(lambda: collections.defaultdict(list))   # elem → (year, month) → values
    for row in csv.reader(open(os.path.join(RAW, 'ghcn_IN009010100.csv'))):
        if row[0] == 'ID' or row[5]: continue                           # skip quality-flagged values
        y, mo = int(row[1][:4]), int(row[1][4:6])
        if not Y0 <= y <= Y1 or row[2] not in ('TMAX', 'TMIN', 'PRCP'): continue
        v[row[2]][(y, mo)].append(int(row[3]))
    months = []
    for mo in range(1, 13):
        def mean_of(el):
            vals = [sum(x) / len(x) for (y, m), x in v[el].items() if m == mo and len(x) >= 20]
            return sum(vals) / len(vals) / 10 if vals else None
        rains = [sum(x) / 10 for (y, m), x in v['PRCP'].items() if m == mo and len(x) >= 27]
        months.append({'tmax': r(mean_of('TMAX'), 1), 'tmin': r(mean_of('TMIN'), 1), 'rain': r(sum(rains) / len(rains)) if rains else None})
    return {'years': [Y0, Y1], 'months': months, 'rainYear': r(sum(m['rain'] for m in months)),
            'station': 'Bangalore city observatory (GHCN IN009010100)', 'source': 'NOAA NCEI GHCN-daily, quality-flagged days excluded',
            'imdNormal': {'rain': 1077.1, 'note': 'IMD long-period average 1991–2020'}}

def prep_context():
    B = load('overture_building.json'); S = load('overture_segment.json'); P = load('overture_place.json')
    LU = load('overture_land_use.json'); WA = load('overture_water.json'); INF = load('overture_infrastructure.json')
    fp, wings, grid, edges = site_footprint(B)
    C = fp.centroid; cx, cy = C.x, C.y
    W, H = 1500, 1160                                       # city frame, metres
    frame = box(cx - W / 2, cy - H / 2, cx + W / 2, cy + H / 2)
    pframe = prep(frame.buffer(40))
    # ---- buildings (figure-ground) ----
    blds = []
    near = fp.buffer(2)
    for f in B:
        g = geoms_en(f['geometry'])
        if g.is_empty or not pframe.intersects(g) or g.area < 25 or near.contains(g.representative_point()): continue
        g = g.simplify(1.2, preserve_topology=True)
        d = path_d(g, cx, cy)
        if not d: continue
        h = f.get('height') or ((f.get('num_floors') or 0) * 3.5) or None
        blds.append([d, r(h) if h else 0])
    blds.sort(key=lambda b: b[0])
    # ---- roads ----
    roads = collections.defaultdict(list); rail = []; named = collections.defaultdict(list)
    for f in S:
        g = geoms_en(f['geometry'])
        if f.get('subtype') == 'rail':
            n = name_of(f); cl = f.get('class')
            if not n or 'Pocket' in n: continue
            line = n.split(' (')[0].replace('Namma Metro - ', '')
            gi = g.intersection(frame.buffer(300))
            if gi.is_empty: continue
            rail.append({'n': line, 'live': cl == 'subway', 'd': path_d(gi.simplify(2), cx, cy)})
            continue
        cl = f.get('class') or 'unknown'
        if cl not in ROAD_W: continue
        gi = g.intersection(frame)
        if gi.is_empty: continue
        roads[cl].append(gi.simplify(0.8))
        n = ALIAS.get(name_of(f), name_of(f))
        if n and ROAD_RANK[cl] <= 2: named[n].append((cl, g))
    road_out = []
    for cl in sorted(roads, key=lambda c: -ROAD_RANK[c]):
        merged = unary_union(roads[cl])
        road_out.append({'c': cl, 'w': ROAD_W[cl], 'rank': ROAD_RANK[cl], 'd': path_d(merged, cx, cy)})
    # merge duplicate rail rows per line
    rl = collections.OrderedDict()
    for x in rail: rl.setdefault((x['n'], x['live']), []).append(x['d'])
    rail = [{'n': n, 'live': live, 'd': ''.join(ds)} for (n, live), ds in rl.items()]
    # road labels: the longest straight run of each named road inside a frame
    def labels_in(fr, pad):
        inner = fr.buffer(-pad); out = []
        for n, parts in named.items():
            best = None
            rank = min(ROAD_RANK[c] for c, _ in parts)
            for cl, g in parts:
                gi = g.intersection(inner)
                for ln in (gi.geoms if hasattr(gi, 'geoms') else [gi]):
                    if ln.is_empty or ln.geom_type != 'LineString': continue
                    c = list(ln.coords)
                    # grow straight runs (direction change < 12°)
                    i = 0
                    while i < len(c) - 1:
                        j = i + 1; a0 = math.atan2(c[j][1] - c[i][1], c[j][0] - c[i][0])
                        while j < len(c) - 1:
                            a1 = math.atan2(c[j + 1][1] - c[j][1], c[j + 1][0] - c[j][0])
                            if abs((a1 - a0 + math.pi) % (2 * math.pi) - math.pi) > math.radians(12): break
                            j += 1
                        L = math.dist(c[i], c[j])
                        if not best or L > best[0]: best = (L, c[i], c[j])
                        i = j
            if not best or best[0] < 70: continue
            L, a, b = best
            ang = math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0]))
            if ang > 90: ang -= 180
            if ang < -90: ang += 180
            out.append({'t': n, 'x': r((a[0] + b[0]) / 2 - cx), 'y': r(cy - (a[1] + b[1]) / 2), 'a': r(ang, 1), 'len': r(L), 'rank': rank})
        return sorted(out, key=lambda o: (o['rank'], -o['len']))
    # ---- land use, water ----
    LU_KIND = {'park': 'park', 'recreation_ground': 'park', 'pitch': 'pitch', 'garden': 'park', 'grass': 'park', 'playground': 'park',
               'school': 'edu', 'college': 'edu', 'university': 'edu', 'education': 'edu', 'hospital': 'med', 'cemetery': 'park', 'stadium': 'pitch'}
    land = collections.defaultdict(list); lnames = []
    for f in LU:
        k = LU_KIND.get(f.get('class'))
        if not k: continue
        g = geoms_en(f['geometry'])
        if g.area > 4e6: continue                          # whole-region polygons, not land use
        gi = g.intersection(frame)
        if gi.is_empty or gi.area < 150: continue
        land[k].append(gi.simplify(1.5))
        if name_of(f) and gi.area > 3000: lnames.append((name_of(f), f.get('class'), g))
    land_out = {k: path_d(unary_union(v), cx, cy) for k, v in land.items()}
    water = []
    for f in WA:
        if f.get('subtype') not in ('lake', 'pond', 'reservoir', 'water'): continue
        g = geoms_en(f['geometry'])
        if g.area > 4e6: continue
        gi = g.intersection(frame.buffer(600))
        if gi.is_empty: continue
        water.append({'n': name_of(f), 'd': path_d(gi.simplify(2), cx, cy), 'x': r(g.centroid.x - cx), 'y': r(cy - g.centroid.y)})
    # ---- landmarks and transit ----
    def place(nm):
        c = [f for f in P if name_of(f) == nm]
        assert c, nm
        return en(*c[0]['geometry']['coordinates'])
    def landuse(nm):
        c = [g for n, cl, g in lnames if n == nm]
        return (c[0].centroid.x, c[0].centroid.y) if c else None
    stations = {}
    for f in INF:
        if f.get('class') == 'subway_station' and name_of(f):
            stations.setdefault(name_of(f), en(*f['geometry']['coordinates']))
    stops = {}
    for f in INF:
        if f.get('class') in ('bus_stop', 'stop_position') and name_of(f) and f['geometry']['type'] == 'Point':
            p = en(*f['geometry']['coordinates'])
            if math.dist(p, (cx, cy)) < 650 and name_of(f) not in stops: stops[name_of(f)] = p
    G = walk_graph(S)
    # the way out of the site: the road node nearest the plus-code point (the gate on the Hosur Road side)
    gate = nearest_node(G, (0, 0), 80)
    DIST = dijkstra(G, gate) if gate else {}
    def walk(p):
        n = nearest_node(G, p, 150)
        if n is None or n not in DIST: return None
        return DIST[n] + math.dist(n, p)
    LM = [
        ('Nexus Mall Koramangala', 'mall', place('Nexus Mall Koramangala'), 'Nexus (Forum) mall'),
        ('Jyoti Nivas College', 'edu', place('Jyoti Nivas College Autonomous'), None),
        ("St John's Medical College Hospital", 'med', place('St John Medical College and Hospital'), None),
        ('Christ University', 'edu', landuse('Christ University'), None),
        ('Koramangala Stadium', 'park', landuse('Koramangala stadium'), None),
    ]
    marks = []
    for n, k, p, alt in LM:
        if not p: continue
        d = math.dist(p, (0, 0)); w = walk(p)
        marks.append({'n': n, 'k': k, 'x': r(p[0] - cx), 'y': r(cy - p[1]), 'd': r(d, -1), 'walk': r(w, -1) if w else None})
    for n in ('Central Silk Board', 'BTM Layout'):
        p = stations[n]; d = math.dist(p, (0, 0)); w = walk(p)
        marks.append({'n': n + ' metro', 'k': 'metro', 'line': 'Yellow Line', 'x': r(p[0] - cx), 'y': r(cy - p[1]), 'd': r(d, -1), 'walk': r(w, -1) if w else None})
    bus = []
    for n, p in sorted(stops.items(), key=lambda kv: math.dist(kv[1], (cx, cy))):
        if any(math.dist(p, (b['x'] + cx, cy - b['y'])) < 60 for b in bus): continue
        w = walk(p)
        bus.append({'n': n, 'x': r(p[0] - cx), 'y': r(cy - p[1]), 'd': r(math.dist(p, (0, 0)), -1), 'walk': r(w, -1) if w else None})
    near_frame = box(cx - 260, cy - 200, cx + 260, cy + 200)
    ctx = {
        'origin': {'lat': LAT, 'lng': LNG, 'plus': '7J4VWJJ7+CQW', 'cx': r(cx, 1), 'cy': r(cy, 1),
                   'centre': [r(LAT + cy / KY, 6), r(LNG + cx / KX, 6)]},
        'gridDeg': r(grid, 2), 'edges': [[r(L, 1), r(b, 2)] for L, b in edges],
        'footprint': {'d': path_d(fp, cx, cy, 1), 'wings': [path_d(w, cx, cy, 1) for w in wings], 'len': r(max(math.dist(a, b) for a, b in zip(fp.minimum_rotated_rectangle.exterior.coords, list(fp.minimum_rotated_rectangle.exterior.coords)[1:]))),
                      'raw': [[r(x - cx, 2), r(cy - y, 2)] for x, y in fp.exterior.coords], 'height': 36, 'floors': 11},
        'gate': [r(-cx, 1), r(cy, 1)],
        'hosur': [[[r(x - cx, 1), r(cy - y, 1)] for x, y in ln.coords] for ln in (lambda u: u.geoms if hasattr(u, 'geoms') else [u])(
            unary_union([g for c, g in named['Hosur Road']]).intersection(Point(cx, cy).buffer(450)).simplify(2))],
        'frame': {'w': W, 'h': H},
        'buildings': blds, 'roads': road_out, 'rail': rail, 'land': land_out, 'water': water,
        'labels': labels_in(frame, 60), 'nearLabels': labels_in(near_frame, 15),
        'marks': marks, 'bus': bus[:6],
        'wind': wind_rose(), 'climate': climate(),
        'attribution': '© OpenStreetMap contributors, Overture Maps Foundation (release 2026-09-23.1)',
    }
    json.dump(ctx, open(CONTEXT, 'w'), separators=(',', ':'), ensure_ascii=False)
    print('context.json', os.path.getsize(CONTEXT), 'bytes;', len(blds), 'buildings; grid', r(grid, 2), '°; gate', gate,
          '; marks', [(m['n'], m['d'], m['walk']) for m in marks], '; bus', [(b['n'], b['d'], b['walk']) for b in bus[:4]])

# ======================================================================
# SUN
# ======================================================================
def solar(doy, minutes):
    """NOAA general solar position. minutes = clock time (IST) since midnight. → (azimuth°, altitude°, declination°, eqtime min)"""
    g = 2 * math.pi / 365 * (doy - 1 + (minutes / 60 - TZ - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    dec = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
           - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    tst = minutes + eqt + 4 * LNG - 60 * TZ
    ha = math.radians(tst / 4 - 180)
    la = math.radians(LAT)
    cz = math.sin(la) * math.sin(dec) + math.cos(la) * math.cos(dec) * math.cos(ha)
    zen = math.acos(max(-1, min(1, cz)))
    alt = 90 - math.degrees(zen)
    az = (math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(la) - math.tan(dec) * math.cos(la))) + 180) % 360
    return az, alt, math.degrees(dec), eqt

# ASHRAE clear-sky direct normal: DNI = A·exp(-B / sin(alt)), monthly A (W/m²) and B
ASH_A = [1230, 1215, 1186, 1136, 1104, 1088, 1085, 1107, 1151, 1192, 1221, 1233]
ASH_B = [.142, .144, .156, .180, .196, .205, .207, .201, .177, .160, .149, .142]
def dni(month, alt):
    if alt <= 0.5: return 0.0
    return ASH_A[month - 1] * math.exp(-ASH_B[month - 1] / math.sin(math.radians(alt)))

def doy_of(m, d): return datetime.date(2026, m, d).timetuple().tm_yday
def hhmm(mins): return '%02d:%02d' % (mins // 60, mins % 60)

def solar_noon(doy):
    lo, hi = 9 * 60, 15 * 60
    for _ in range(40):
        m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        if solar(doy, m1)[1] < solar(doy, m2)[1]: lo = m1
        else: hi = m2
    return (lo + hi) / 2

def rise_set(doy):
    def cross(a, b):
        for _ in range(40):
            mid = (a + b) / 2
            if (solar(doy, a)[1] + 0.833) * (solar(doy, mid)[1] + 0.833) <= 0: b = mid
            else: a = mid
        return (a + b) / 2
    n = solar_noon(doy)
    return cross(4 * 60, n), cross(n, 21 * 60)

def sun_block():
    days = [('jun', '21 Jun', 6, 21), ('may', '21 May · 23 Jul', 5, 21), ('apr', '20 Apr · 23 Aug', 4, 20), ('mar', '20 Mar · 23 Sep', 3, 20),
            ('feb', '20 Feb · 22 Oct', 2, 20), ('jan', '21 Jan · 22 Nov', 1, 21), ('dec', '21 Dec', 12, 21)]
    arcs = []
    for k, lab, m, d in days:
        doy = doy_of(m, d); a, b = rise_set(doy)
        pts = []
        t = math.ceil(a / 10) * 10
        pts.append([r(solar(doy, a)[0], 1), 0.0, r(a)])
        while t < b:
            az, alt, _, _ = solar(doy, t); pts.append([r(az, 1), r(alt, 1), t]); t += 10
        pts.append([r(solar(doy, b)[0], 1), 0.0, r(b)])
        hours = [[r(solar(doy, h * 60)[0], 1), r(solar(doy, h * 60)[1], 1), h] for h in range(6, 20) if solar(doy, h * 60)[1] > 0]
        n = solar_noon(doy); naz, nalt, dec, _ = solar(doy, n)
        arcs.append({'k': k, 'label': lab, 'pts': pts, 'hours': hours, 'noon': hhmm(r(n)), 'noonAlt': r(nalt, 1), 'noonAz': r(naz, 1),
                     'rise': hhmm(r(a)), 'set': hhmm(r(b)), 'riseAz': r(solar(doy, a)[0], 1), 'setAz': r(solar(doy, b)[0], 1),
                     'dayLen': r((b - a) / 60, 2)})
    # dates when the noon sun stands north of the zenith (declination > latitude)
    north = [d for d in range(1, 366) if solar(d, solar_noon(d))[2] > LAT]
    fmtd = lambda doy: (datetime.date(2026, 1, 1) + datetime.timedelta(doy - 1)).strftime('%-d %b')
    return {'lat': LAT, 'lng': LNG, 'tz': 'IST (UTC+5:30)', 'arcs': arcs, 'northFrom': fmtd(north[0]), 'northTo': fmtd(north[-1]),
            'northDays': len(north)}

# ======================================================================
# BUILD: the plan placed on the site, and the sun on the layout
# ======================================================================
def core_blocks(RF):
    """solid core blocks (lift shafts, stairs, toilets) from the core wall lines, as obstacles to sunlight."""
    import re
    segs = []
    for d in RF['g']['core']['S'].split('M')[1:]:
        n = list(map(float, re.findall(r'-?\d+(?:\.\d+)?', d)))
        x, y = n[0], n[1]; pts = [(x, y)]
        for i in range(2, len(n), 2): x += n[i]; y += n[i + 1]; pts.append((x, y))
        if len(pts) > 1: segs.append(LineString(pts))
    u = unary_union([s.buffer(12) for s in segs])
    blocks = []
    for p in (u.geoms if hasattr(u, 'geoms') else [u]):
        solid = Polygon(p.exterior).buffer(-6)
        if solid.area > 600: blocks.append(solid)
    for st in RF['stairs']: blocks.append(box(st['x'], st['y'], st['x'] + st['w'], st['y'] + st['h']))
    return unary_union(blocks)

def place_plate(RF, ctx, up):
    """plan units → map metres (relative to the map centre, y down) for a given plan-up bearing; best overlap with the footprint."""
    fp = Polygon(ctx['footprint']['raw'])                     # map coords (y down)
    a = math.radians(up)
    ex = (math.sin(a + math.pi / 2), -math.cos(a + math.pi / 2))    # plan +x in map (y down)
    ey = (-math.sin(a), math.cos(a))                                # plan +y (down) in map
    plate = Polygon(RF['plate']); pc = plate.centroid
    def tf(u, v, ox, oy):
        X, Y = (u - pc.x) * RF['unit'], (v - pc.y) * RF['unit']
        return (ox + X * ex[0] + Y * ey[0], oy + X * ex[1] + Y * ey[1])
    fc = fp.centroid; best = None
    for du in range(-50, 51, 2):
        for dv in range(-24, 25, 2):
            ox = fc.x + du * ex[0] + dv * ey[0]; oy = fc.y + du * ex[1] + dv * ey[1]
            pl = Polygon([tf(u, v, ox, oy) for u, v in RF['plate']])
            ov = pl.intersection(fp).area / pl.area
            if not best or ov > best[0]: best = (ov, ox, oy)
    ov, ox, oy = best
    # refine to 0.5 m
    for du in [x / 2 for x in range(-4, 5)]:
        for dv in [x / 2 for x in range(-4, 5)]:
            x2 = ox + du * ex[0] + dv * ey[0]; y2 = oy + du * ex[1] + dv * ey[1]
            pl = Polygon([tf(u, v, x2, y2) for u, v in RF['plate']])
            o2 = pl.intersection(fp).area / pl.area
            if o2 > best[0]: best = (o2, x2, y2)
    ov, ox, oy = best
    return ov, (lambda u, v: tf(u, v, ox, oy)), ex, ey

def build(rf_path, out_path):
    RF = json.load(open(rf_path)); ctx = json.load(open(CONTEXT)); facts = json.load(open(FACTS))
    U = RF['unit']
    # ---- which way is north: the floor's long axis runs along the local grid; test both ways round ----
    grid = ctx['gridDeg']
    hosur = unary_union([LineString(l) for l in ctx['hosur'] if len(l) > 1])
    plate = Polygon(RF['plate'])
    # slanted west end of the plate: the plate edge between the bottom-left corner and the top arc
    pts = RF['plate']; slant = max(zip(pts, pts[1:] + pts[:1]), key=lambda e: abs(e[1][0] - e[0][0]) * abs(e[1][1] - e[0][1]))
    smid = ((slant[0][0] + slant[1][0]) / 2, (slant[0][1] + slant[1][1]) / 2)
    tests = []
    for up in (grid, grid + 180):
        ov, tf, ex, ey = place_plate(RF, ctx, up)
        sm = Point(*tf(*smid))
        dh = sm.distance(hosur) if hosur else 0
        tests.append({'up': r(up % 360, 2), 'overlap': r(ov, 3), 'slantToHosur': r(dh), 'tf': tf, 'ex': ex, 'ey': ey})
    tests.sort(key=lambda t: (t['slantToHosur'], -t['overlap']))
    T0 = tests[0]; up = T0['up']; tf = T0['tf']
    print('orientation tests', [(t['up'], t['overlap'], t['slantToHosur']) for t in tests], '→ plan-up bearing', up)
    on_site = {
        'plate': path_d(Polygon([tf(u, v) for u, v in RF['plate']]), 0, 0, 1).replace('M', 'M').strip(),
        'terraces': [path_d(Polygon([tf(u, v) for u, v in t]), 0, 0, 1) for t in RF['terraces']],
        'stairs': [[r(tf(s['x'] + s['w'] / 2, s['y'] + s['h'] / 2)[0], 1), r(tf(s['x'] + s['w'] / 2, s['y'] + s['h'] / 2)[1], 1)] for s in RF['stairs']],
        'lifts': [[r(tf(l['x'], l['y'])[0], 1), r(tf(l['x'], l['y'])[1], 1)] for l in RF.get('lifts', [])],
        'tf': (lambda o, x, y: [r(x[0] - o[0], 5), r(y[0] - o[0], 5), r(o[0], 2), r(x[1] - o[1], 5), r(y[1] - o[1], 5), r(o[1], 2)])(tf(0, 0), tf(1, 0), tf(0, 1)),
        'overlap': T0['overlap'], 'tests': [{k: v for k, v in t.items() if k in ('up', 'overlap', 'slantToHosur')} for t in tests],
    }
    # path_d flips y (it expects north-up metres); our map coords are already y-down, so redo without the flip
    def pd_map(poly):
        c = [(r(x, 1), r(y, 1)) for x, y in poly.exterior.coords]
        return 'M' + 'L'.join('%s %s' % p for p in c[:-1]) + 'Z'
    on_site['plate'] = pd_map(Polygon([tf(u, v) for u, v in RF['plate']]))
    on_site['terraces'] = [pd_map(Polygon([tf(u, v) for u, v in t])) for t in RF['terraces']]
    # ---- façades: plate edges with outward normals as true bearings ----
    def bearing_of_plan_vec(nx, ny):         # plan vector (y down) → compass bearing
        return (up + math.degrees(math.atan2(nx, -ny))) % 360
    P = RF['plate']; cw = Polygon(P).exterior.is_ccw   # in y-down coords, is_ccw==False means clockwise on screen
    edges = []
    for (x0, y0), (x1, y1) in zip(P, P[1:] + P[:1]):
        dx, dy = x1 - x0, y1 - y0; L = math.hypot(dx, dy)
        if L < 1: continue
        nx, ny = (dy / L, -dx / L)
        mid = Point((x0 + x1) / 2 + nx * 5, (y0 + y1) / 2 + ny * 5)
        if Polygon(P).contains(mid): nx, ny = -nx, -ny
        edges.append({'a': (x0, y0), 'b': (x1, y1), 'L': L, 'n': (nx, ny), 'brg': bearing_of_plan_vec(nx, ny)})
    terr = unary_union([Polygon(t) for t in RF['terraces']]).buffer(2)
    def face_of(e):
        ln = LineString([e['a'], e['b']])
        if ln.difference(terr).length < 0.3 * ln.length: return 'T'          # glass facing a terrace
        rel = (e['brg'] - up) % 360
        if rel < 45 or rel >= 315: return 'N'
        if rel < 135: return 'E'
        if rel < 225: return 'S'
        return 'W'
    for e in edges: e['f'] = face_of(e)
    def comp16(b): return ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][int(((b % 360) + 22.5) // 45) % 8]
    faces = {}
    for f in 'NESWT':
        es = [e for e in edges if e['f'] == f]
        if not es: continue
        Lsum = sum(e['L'] for e in es)
        sx = sum(e['L'] * math.sin(math.radians(e['brg'])) for e in es); cx_ = sum(e['L'] * math.cos(math.radians(e['brg'])) for e in es)
        b = math.degrees(math.atan2(sx, cx_)) % 360 if f != 'T' else None
        main = max(es, key=lambda e: e['L'])
        faces[f] = {'f': f, 'len': r(Lsum * U, 1), 'brg': r(b, 1) if b is not None else None, 'comp': comp16(b) if b is not None else 'S/E/W',
                    'mid': [r((main['a'][0] + main['b'][0]) / 2, 1), r((main['a'][1] + main['b'][1]) / 2, 1)], 'n': [r(main['n'][0], 3), r(main['n'][1], 3)]}
    # ---- sun on each façade through the year (21st of each month; unshaded façade, clear sky) ----
    year = []
    for m in range(1, 13):
        doy = doy_of(m, 21); row = {}
        for f, fc in faces.items():
            if f == 'T': continue
            hrs = 0; wh = 0.0
            for t in range(5 * 60, 20 * 60, 5):
                az, alt, _, _ = solar(doy, t)
                if alt <= 2: continue
                c = math.cos(math.radians(alt)) * math.cos(math.radians(az - fc['brg']))
                if c > 0.05: hrs += 5; wh += dni(m, alt) * c * 5 / 60
            row[f] = [r(hrs / 60, 1), r(wh / 1000, 2)]
        year.append(row)
    # ---- the sun on the layout, through the day ----
    obst = core_blocks(RF)
    prep_plate = prep(plate.buffer(-0.5))
    walls = unary_union([obst.boundary, plate.boundary])
    H = 3.25 / U                                              # glazing head (beam bottom) in plan units
    areas = {k: Polygon(v) for k, v in RF['areas'].items()}
    def sun_vec(az):                                          # plan unit vector pointing towards the sun (y down)
        t = math.radians(az - up); return (math.sin(t), -math.cos(t))
    def lit_patch(az, alt):
        sx, sy = sun_vec(az)
        L = H / math.tan(math.radians(alt))
        vx, vy = -sx * L, -sy * L
        out = collections.defaultdict(list); wsum = {}
        for e in edges:
            cos_h = e['n'][0] * sx + e['n'][1] * sy
            if cos_h <= 0.02: continue
            n = max(2, int(e['L'] / 10)); quads = []
            prev = None
            for i in range(n + 1):
                t = i / n; p = (e['a'][0] + (e['b'][0] - e['a'][0]) * t, e['a'][1] + (e['b'][1] - e['a'][1]) * t)
                # shaded if the ray towards the sun re-enters the floor plate (recesses, the slanted end)
                o = (p[0] + e['n'][0] * 1.5 + sx * 1.5, p[1] + e['n'][1] * 1.5 + sy * 1.5)
                ray_out = LineString([o, (o[0] + sx * 6000, o[1] + sy * 6000)])
                if prep_plate.intersects(ray_out):
                    end = None
                else:
                    q0 = (p[0] - e['n'][0] * 0.5, p[1] - e['n'][1] * 0.5)
                    ray_in = LineString([q0, (q0[0] + vx, q0[1] + vy)])
                    hit = ray_in.intersection(walls)
                    tmax = 1.0
                    if not hit.is_empty:
                        for g in (hit.geoms if hasattr(hit, 'geoms') else [hit]):
                            gp = g if g.geom_type == 'Point' else Point(g.coords[0])
                            d = math.dist(q0, (gp.x, gp.y)) / max(1e-6, L)
                            if d > 0.004: tmax = min(tmax, d)
                    end = (q0, (q0[0] + vx * tmax, q0[1] + vy * tmax))
                if prev and prev[1] and end:
                    quads.append(Polygon([prev[1][0], end[0], end[1], prev[1][1]]).buffer(0.6))
                prev = (p, end)
            if quads:
                out[e['f']].extend(quads)
                wsum.setdefault(e['f'], []).append((e['L'], math.cos(math.radians(alt)) * cos_h))
        res = {}
        for f, qs in out.items():
            g = unary_union(qs).intersection(plate).difference(obst)
            if g.is_empty or g.area < 400: continue
            ws = wsum[f]; c = sum(L * c for L, c in ws) / sum(L for L, c in ws)
            res[f] = (g.simplify(3), c)
        return res
    seasons = [('mar', '20 Mar · 23 Sep', 3, 20), ('jun', '21 Jun', 6, 21), ('dec', '21 Dec', 12, 21)]
    day = []
    for k, lab, m, d in seasons:
        doy = doy_of(m, d); frames = []
        for t in range(7 * 60, 18 * 60 + 31, 30):
            az, alt, _, _ = solar(doy, t)
            fr = {'t': hhmm(t), 'az': r(az, 1), 'alt': r(alt, 1)}
            if alt > 1:
                if alt < 8: fr['low'] = 1                 # very low sun: neighbours across the road will often block it
                D = dni(m, alt); fr['dni'] = r(D)
                patches = lit_patch(az, alt); lit = {}
                allp = []
                fr['p'] = []
                for f, (g, c) in sorted(patches.items()):
                    w = D * c
                    fr['p'].append({'f': f, 'w': r(w), 'd': path_d(affinity.scale(g, 1, -1, origin=(0, 0)), 0, 0)})
                    allp.append((g, w))
                gain = {}
                for a, poly in areas.items():          # sun strong enough to matter for glare and heat
                    s = sum(poly.intersection(g).area for g, w in allp if w >= 120)
                    if s * U * U > 1: lit[a] = r(s * U * U)
                    e = sum(poly.intersection(g).area * U * U * w for g, w in allp)   # W of direct sun on the floor
                    if e > 0: gain[a] = e
                fr['lit'] = lit
                fr['_gain'] = gain
                fr['top'] = max(patches, key=lambda f: patches[f][1]) if patches else None
                fr['m2'] = r(sum(g.area for g, w in allp) * U * U)
            frames.append(fr)
        n = solar_noon(doy)
        day.append({'k': k, 'label': lab, 'frames': frames, 'noon': hhmm(r(n)), 'rise': hhmm(r(rise_set(doy)[0])), 'set': hhmm(r(rise_set(doy)[1]))})
    # per area: direct sun reaching its floor before noon and after 2 pm, kWh per 100 m² of floor on a clear day
    summ = {}
    for s in day:
        for a, poly in areas.items():
            m2 = poly.area * U * U
            am = sum(f.get('_gain', {}).get(a, 0) * 0.5 for f in s['frames'] if f['t'] < '12:00') / 1000 / m2 * 100
            pm = sum(f.get('_gain', {}).get(a, 0) * 0.5 for f in s['frames'] if f['t'] >= '14:00') / 1000 / m2 * 100
            pk = max([f.get('lit', {}).get(a, 0) for f in s['frames']] or [0])
            summ.setdefault(a, {})[s['k']] = [r(am, 2), r(pm, 2), pk]
        for f in s['frames']: f.pop('_gain', None)
    sun = sun_block()
    sun.update({'faces': faces, 'year': year, 'day': day, 'areaSun': summ, 'head': 3.25,
                'model': 'Clear-sky sun (ASHRAE), full-height glazing to 3.25 m; the floor’s own recesses and cores cast shade; neighbours and fins not modelled'})
    # ---- numbers ----
    sba, carpet, hc = facts['sbaSft'], facts['carpetSft'], facts['headcount']
    desks = sum(d[2] for d in RF['desks'])
    nums = {'efficiency': r(100 * carpet / sba), 'carpetPerHead': r(carpet / hc), 'sbaPerHead': r(sba / hc),
            'plateSft': r(RF['plateM2'] * 10.7639), 'desks': desks, 'spare': desks - hc,
            'clearUnderBeam': facts['dd'][2]['mm'], 'slab': facts['dd'][1]['mm'], 'beamZone': facts['dd'][1]['mm'] - facts['dd'][2]['mm']}
    out = dict(ctx)
    out.update({'up': up, 'onSite': on_site, 'sun': sun, 'facts': facts, 'nums': nums})
    out.pop('edges', None)
    for k in ('raw',): out['footprint'].pop(k, None)
    json.dump(out, open(out_path, 'w'), separators=(',', ':'), ensure_ascii=False)
    print(out_path, os.path.getsize(out_path), 'bytes; plan-up', up, '; faces', {f: (v['brg'], v['comp'], v['len']) for f, v in faces.items()})

if __name__ == '__main__':
    if sys.argv[1] == "prep": prep_context()
    elif sys.argv[1] == 'build': build(sys.argv[2], sys.argv[3])
