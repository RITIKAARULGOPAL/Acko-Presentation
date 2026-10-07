"""Download the open data behind the site analysis (run once, needs network).

Writes raw extracts to tools/site/raw/ (git-ignored); site.py turns them into
tools/testfit/site.json offline.

  Overture Maps (release below; OSM-derived, ODbL)  buildings, roads, places, land use
  Google Open Buildings v3 (CC BY 4.0)               2023 footprints, cross-check only
  NOAA NCEI ISD-lite station 432950 BANGALORE        hourly wind
  NOAA NCEI GHCN-daily IN009010100 BANGALORE         daily temperature and rain

Needs: pip install pyarrow shapely; gsutil for Open Buildings (anonymous read).
"""
import gzip, io, json, os, subprocess, sys, urllib.request
import pyarrow.dataset as ds, pyarrow.fs as pafs
import shapely

LAT, LNG = 12.9311125, 77.614453          # plus code 7J4VWJJ7+CQW
RELEASE = '2026-09-23.1'
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw')
os.makedirs(RAW, exist_ok=True)

def box(dlat, dlng): return (LNG-dlng, LAT-dlat, LNG+dlng, LAT+dlat)
BOXES = {   # (xmin, ymin, xmax, ymax) in degrees
    'building': box(.0095, .0098),    # ~1.05 km each way
    'land_use': box(.0095, .0098),
    'segment':  box(.0170, .0175),    # ~1.9 km
    'place':    box(.0240, .0245),    # ~2.65 km, landmarks only
    'infrastructure': box(.0240, .0245),   # stations, bus stops
    'water':    box(.0240, .0245),
}
THEME = {'building':'buildings','land_use':'base','segment':'transportation','place':'places','infrastructure':'base','water':'base'}

def proxy(): return os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')

def overture(kind):
    s3 = pafs.S3FileSystem(anonymous=True, region='us-west-2', proxy_options=proxy()) if proxy() else pafs.S3FileSystem(anonymous=True, region='us-west-2')
    path = f'overturemaps-us-west-2/release/{RELEASE}/theme={THEME[kind]}/type={kind}/'
    d = ds.dataset(path, filesystem=s3, format='parquet')
    x0, y0, x1, y1 = BOXES[kind]
    f = ((ds.field('bbox', 'xmin') < x1) & (ds.field('bbox', 'xmax') > x0) &
         (ds.field('bbox', 'ymin') < y1) & (ds.field('bbox', 'ymax') > y0))
    want = [c for c in ('id', 'names', 'class', 'subtype', 'height', 'num_floors', 'level', 'is_underground',
                        'categories', 'basic_category', 'taxonomy', 'confidence', 'road_flags', 'geometry')
            if c in d.schema.names]
    t = d.to_table(columns=want, filter=f)
    out = []
    for r in t.to_pylist():
        g = shapely.from_wkb(r.pop('geometry'))
        r['geometry'] = shapely.geometry.mapping(g)
        out.append(r)
    with open(os.path.join(RAW, f'overture_{kind}.json'), 'w') as fh:
        json.dump({'release': RELEASE, 'bbox': BOXES[kind], 'features': out}, fh, default=str)
    print(kind, len(out), file=sys.stderr)

def open_buildings():
    x0, y0, x1, y1 = BOXES['building']
    cmd = ('gsutil cat gs://open-buildings-data/v3/polygons_s2_level_6_gzip_no_header/3baf_buildings.csv.gz | zcat | '
           f"awk -F, '$1>{y0} && $1<{y1} && $2>{x0} && $2<{x1}'")
    rows = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True).stdout
    with open(os.path.join(RAW, 'openbuildings_3baf.csv'), 'w') as fh: fh.write(rows)
    print('open buildings', rows.count('\n'), file=sys.stderr)

def get(url):
    return urllib.request.urlopen(url, timeout=60).read()

def noaa():
    lines = []
    for y in range(2014, 2026):
        try: lines.append(gzip.decompress(get(f'https://noaa-isd-pds.s3.amazonaws.com/isd-lite/data/{y}/432950-99999-{y}.gz')).decode())
        except Exception as e: print('isd', y, e, file=sys.stderr)
    with open(os.path.join(RAW, 'isd_432950.txt'), 'w') as fh: fh.write(''.join(lines))
    with open(os.path.join(RAW, 'ghcn_IN009010100.csv'), 'wb') as fh:
        fh.write(get('https://noaa-ghcn-pds.s3.amazonaws.com/csv/by_station/IN009010100.csv'))
    print('noaa done', file=sys.stderr)

if __name__ == '__main__':
    which = sys.argv[1:] or ['building', 'land_use', 'segment', 'place', 'openbuildings', 'noaa']
    for w in which:
        if w in BOXES: overture(w)
        elif w == 'openbuildings': open_buildings()
        elif w == 'noaa': noaa()
