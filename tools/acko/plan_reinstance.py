"""Find the repeated shapes in exploded geometry and store each once, placed by reference.

Some blocks of the plan hold furniture that was exploded in CAD: thousands of chairs, desks and fittings as loose lines,
with no block references left to share. Inside each run of strokes (consecutive lines of one layer, colour, linetype and
lineweight, so AutoCAD's draw order is untouched), lines that touch end to end are grouped into shapes. Each shape is put
into a canonical pose: centred on its vertices' mean, turned so its longest segment lies along +x, mirrored or not, and
the pose whose coordinates sort first is kept. Shapes whose canonical coordinates agree (to the millimetre) are one shape:
it becomes a definition of its own, and each occurrence a placement [definition, a, b, c, d, e, f], right after the rest
of its run. The placement passes its context through ("", "B", "B", -2), so the shape's layer, colour, linetype and
lineweight resolve exactly as they did in place.

Used by plan_vector.py (reinstance(defs)); on its own, it rewrites an instanced block file:
usage: python tools/acko/plan_reinstance.py <in layers/block.json> <out layers/block.json>
"""
import sys, json, math, collections

MIN_POINTS = 12          # a shape must be worth more than its placement (7 numbers)
MAX_SIZE = 6000          # mm: larger groups are walls and outlines, not furniture
BIG_DEF = 200_000        # only definitions holding at least this many bytes of runs are searched

def decode(a):
    pts, x, y = [(a[0], a[1])], a[0], a[1]
    for i in range(2, len(a), 2):
        x += a[i]; y += a[i + 1]; pts.append((x, y))
    return pts

def enc(pts):
    out, px, py = [], 0, 0
    for i, (x, y) in enumerate(pts):
        x, y = round(x), round(y)
        if i and x == px and y == py: continue
        out += [x, y] if not i else [x - px, y - py]
        px, py = x, y
    return out

def components(polys):
    """indices of polylines grouped by shared endpoints (rounded to the millimetre, neighbours included)"""
    parent = list(range(len(polys)))
    def find(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    at = {}
    for i, p in enumerate(polys):
        for (x, y) in (p[0], p[-1]):
            k = (round(x), round(y))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    j = at.get((k[0] + dx, k[1] + dy))
                    if j is not None:
                        a, b = find(i), find(j)
                        if a != b: parent[a] = b
            at[k] = i
    groups = collections.defaultdict(list)
    for i in range(len(polys)): groups[find(i)].append(i)
    return list(groups.values())

def canonical(polys):
    """(key, canonical polylines, placement affine) for one shape, or None"""
    allp = [p for poly in polys for p in poly]
    n = len(allp)
    cx = sum(p[0] for p in allp) / n; cy = sum(p[1] for p in allp) / n
    best, blen = None, -1
    for poly in polys:
        for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
            L = (x1 - x0) ** 2 + (y1 - y0) ** 2
            if L > blen + 1e-6: blen, best = L, math.atan2(y1 - y0, x1 - x0)
    if best is None: return None
    cands = []
    for ang in (best, best + math.pi):
        c, s = math.cos(ang), math.sin(ang)
        for m in (1, -1):
            out = []
            for poly in polys:
                q = tuple((round((x - cx) * c + (y - cy) * s), round(m * (-(x - cx) * s + (y - cy) * c))) for x, y in poly)
                out.append(min(q, q[::-1]))           # a polyline drawn either way round is the same line
            out.sort()
            cands.append((out, ang, m))
    out, ang, m = min(cands, key=lambda t: t[0])
    c, s = math.cos(ang), math.sin(ang)
    # canonical -> placed: p = centre + R(ang) . diag(1, m) . q   (canvas setTransform order a, b, c, d, e, f)
    aff = [c, s, -s * m, c * m, cx, cy]
    return json.dumps(out, separators=(",", ":")), out, aff

def reinstance(defs, stats=None):
    """rewrite big definitions in place: repeated exploded shapes become definitions of their own"""
    stats = stats if stats is not None else collections.Counter()
    for di in range(len(defs)):
        d = defs[di]
        if d.get("q", 0) != 0: continue
        if len(json.dumps(d["runs"], separators=(",", ":"))) < BIG_DEF: continue
        # pass 1: every candidate shape, by run
        found = []          # (run index, member item indices, key, canonical, affine)
        count = collections.Counter()
        for ri, r in enumerate(d["runs"]):
            if r[4] != "s": continue
            polys = [decode(it) for it in r[5]]
            for g in components(polys):
                pts = sum(len(polys[i]) for i in g)
                if pts < MIN_POINTS: continue
                xs = [p[0] for i in g for p in polys[i]]; ys = [p[1] for i in g for p in polys[i]]
                if max(xs) - min(xs) > MAX_SIZE or max(ys) - min(ys) > MAX_SIZE: continue
                c = canonical([polys[i] for i in g])
                if c is None: continue
                key = json.dumps(r[:4]) + c[0]          # the same shape in another layer or colour is another shape
                found.append((ri, g, key, c[1], c[2])); count[key] += 1
        # pass 2: shapes that occur more than once become definitions
        shape_def = {}
        moved = collections.defaultdict(set)       # run index -> item indices taken out
        place = collections.defaultdict(list)      # run index -> placements to add after the run
        for ri, g, key, out, aff in found:
            if count[key] < 2: continue
            if key not in shape_def:
                shape_def[key] = len(defs)
                r = d["runs"][ri]
                defs.append({"name": f"{d['name']}~shape{len(shape_def)}", "q": 0,
                             "runs": [[r[0], r[1], r[2], r[3], "s", [enc(p) for p in out]]]})
                stats["shapes"] += 1
            moved[ri].update(g)
            place[ri].append([shape_def[key], *[round(v, 9) for v in aff[:4]], round(aff[4], 3), round(aff[5], 3)])
            stats["occurrences"] += 1
        runs = []
        for ri, r in enumerate(d["runs"]):
            if ri in moved:
                keep = [it for i, it in enumerate(r[5]) if i not in moved[ri]]
                if keep: runs.append(r[:5] + [keep])
                runs.append(["", "B", "B", -2, "i", place[ri]])
                stats["lines_moved"] += len(moved[ri])
            else:
                runs.append(r)
        d["runs"] = runs
    return stats

if __name__ == "__main__":
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    st = reinstance(data["defs"])
    json.dump(data, open(sys.argv[2], "w", encoding="utf-8"), separators=(",", ":"))
    print(dict(st))
