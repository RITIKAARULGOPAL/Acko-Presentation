"""Check the room hatches the deck hovers on, against the plan's other layers, from plan_vector.py's export.

The rooms DXF (group "rooms") holds one solid hatch per room type (AC_<TYPE>), each with a loop per room. For hover every
room must be its own clean shape, so each hatch is split into rooms (even-odd over its loops; furniture islands are
holes in a CAD fill, so a room's hover shape is its outer edge) and every room is checked:
  shape        a valid polygon of a sensible size
  overlap      no other room's hover shape covers part of it (the cursor would light two rooms)
  outline      the zoneBoundaries group has an outline of the same type that matches it (intersection over union);
               outlines with no hatch are listed too
  label        a label from the text group sits inside it, and its words fit the type
  neighbourhood  which of the six it lies in (the neighbourhoods group), for the occupancy panels
Writes <dir>/rooms.json: every room (type, colour, area, label, neighbourhood, outline match, its shape in world mm) and
every issue with its position, which plan_view.html draws as a hover layer and an issue list.

usage: python tools/acko/plan_rooms.py <export dir, e.g. tools/_work/plan>
"""
import sys, os, re, json, math, collections
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.ops import unary_union
from shapely.validation import explain_validity

DIR = sys.argv[1]
meta = json.load(open(os.path.join(DIR, "layers.json"), encoding="utf-8"))
L = meta["layers"]

def decode(a, k):
    pts, x, y = [(a[0] * k, a[1] * k)], a[0], a[1]
    for i in range(2, len(a), 2):
        x += a[i]; y += a[i + 1]; pts.append((x * k, y * k))
    return pts

def expand(group):
    """every placed item of a group in world mm: (layer, colour, kind, item) with item = loops / points / text"""
    out = []
    for b in meta["blocks"]:
        if b["group"] != group: continue
        data = json.load(open(os.path.join(DIR, b["file"]), encoding="utf-8"))
        defs = data["defs"]
        def resolve(spec, ctx):
            layer = spec[0] or ctx[0]
            col = (L.get(layer, {}).get("colour", "#000000") if spec[1] == "L" else ctx[1] if spec[1] == "B" else spec[1])
            return layer, col
        root = ("0", L.get("0", {}).get("colour", "#000000"))
        def walk(di, M, ctx):
            d = defs[di]; k = 10 ** -d["q"]; a, b_, c, e, f, g = M
            T = lambda p: (a * p[0] + c * p[1] + f, b_ * p[0] + e * p[1] + g)
            for r in d["runs"]:
                layer, col = resolve(r[:4], ctx); kind = r[4]
                for it in r[5]:
                    if kind == "i":
                        ci, ca, cb, cc, cd, ce, cf = it
                        walk(ci, [a * ca + c * cb, b_ * ca + e * cb, a * cc + c * cd, b_ * cc + e * cd, a * ce + c * cf + f, b_ * ce + e * cf + g], (layer, col))
                    elif kind == "t":
                        out.append((layer, col, "t", (T((it[0] * k, it[1] * k)), it[6], it[2])))
                    elif kind == "f":
                        out.append((layer, col, "f", [[T(p) for p in decode(l, k)] for l in it]))
                    else:
                        out.append((layer, col, kind, [T(p) for p in decode(it, k)]))
        walk(data["root"], data["place"]["m"], resolve(data["place"]["spec"], root))
    return out

issues = []
def issue(kind, layer, pt, what, level="issue", **kw):
    """level: "issue" needs a look in CAD; "note" is expected but worth knowing (it shows in the hover)"""
    issues.append({"kind": kind, "level": level, "layer": layer, "x": round(pt[0]), "y": round(pt[1]), "what": what, **kw})

def clean(pts):
    pg = Polygon(pts)
    return pg if pg.is_valid else pg.buffer(0)
def parts(g): return [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and not p.is_empty]

TYPE_WORDS = {   # words a room's label should carry, by type (beyond its own layer name's words)
    "AC_COLLAB_HUDDLE": ["COLLABORATION", "HUDDLE"], "AC_QUICK_SPRINT": ["SPRINT", "PAX"], "AC_PHONE_BOOTH": ["PHONE", "BOOTH", "PAX"],
    "AC_DEPARTMENTAL_ROOMS": ["DEPARTMENTAL"], "AC_UPS_SERVER_BATTERY_BMS_ROOM": ["UPS", "SERVER", "BATTERY", "BMS", "ELECTRICAL"],
    "AC_EXECUTIVE_CORNER_CABIN": ["EXECUTIVE", "CABIN"], "AC_THE_STUDIO_ROOM": ["STUDIO"], "AC_THE_HATCHERY": ["HATCHERY"],
    "AC_BOARD_ROOM": ["BOARD"], "AC_COFFEE_CORNER": ["COFFEE"], "AC_WORKHALL": ["WORK"], "AC_CORRIDOR": ["CORRIDOR"],
}
DEV_MM = 400            # mm a hover shape may stray from its outline (a wall's thickness and a little)
OPEN = {"AC_WORKHALL", "AC_CORRIDOR", "AC_OUT_OF_ZONE", "AC_OUT_OF_SCOPE", "AC_TERRACE", "AC_ENTRY"}
ZONES = ["AC_AUTO", "AC_LIFE", "AC_HEALTH", "AC_DRIVE", "AC_TRAVEL", "AC_HOME"]

# ---------------------------------------------------------------- the room hatches, split into rooms
rooms = []
for layer, col, kind, it in expand("rooms"):
    if kind != "f":
        continue
    g = None
    for loop in it:                                # even-odd over the hatch's loops, as AutoCAD fills it
        pg = clean(loop)
        if pg.is_empty: continue
        g = pg if g is None else g.symmetric_difference(pg)
    if g is None: continue
    for p in parts(g):
        shell = Polygon(p.exterior)                # furniture islands are holes in the fill, not gaps in the room
        if shell.area < 2e5: continue              # under 0.2 m2: a sliver between loops, not a room
        rooms.append({"type": layer, "colour": col, "poly": shell, "fill": p, "islands": len(p.interiors)})
# a filled loop inside a furniture island (a table's inlay, a planter) is drawn as its own piece; for hover it is part of
# the room around it
rooms.sort(key=lambda r: -r["poly"].area)
kept = []
for r in rooms:
    host = next((k for k in kept if k["type"] == r["type"] and k["poly"].contains(r["poly"].representative_point())
                 and k["poly"].intersection(r["poly"]).area > 0.95 * r["poly"].area), None)
    if host: host["nested"] = host.get("nested", 0) + 1
    else: kept.append(r)
nested = len(rooms) - len(kept); rooms = kept
print(f"{len(rooms)} rooms from {sum(1 for x in expand('rooms') if x[2] == 'f')} hatches ({nested} nested pieces folded into their rooms)")

# ---------------------------------------------------------------- the other layers
outlines = []
for layer, col, kind, pts in expand("zoneBoundaries"):
    if kind == "s" and layer.startswith("AC_") and len(pts) >= 4 and math.dist(pts[0], pts[-1]) < 1000:
        outlines.append({"type": layer, "poly": clean(pts), "open": math.dist(pts[0], pts[-1]) > 1})
labels = [{"layer": layer, "pt": it[0], "words": it[1].replace("\n", " ").strip(), "h": it[2]}
          for layer, col, kind, it in expand("text") if kind == "t" and it[1].strip()]
zones = []
for layer, col, kind, pts in expand("neighbourhoods"):
    if layer in ZONES and kind == "s" and len(pts) >= 4:
        zones.append({"name": layer[3:].title(), "poly": clean(pts + [pts[0]])})
print(f"{len(outlines)} outlines, {len(labels)} labels, {len(zones)} neighbourhoods")

# ---------------------------------------------------------------- checks
for i, r in enumerate(rooms):
    p, c = r["poly"], r["poly"].representative_point().coords[0]
    r["id"], r["m2"], r["x"], r["y"] = i, round(p.area / 1e6, 2), round(c[0]), round(c[1])
    # shape
    raw = Polygon(r["poly"].exterior.coords)
    if not raw.is_valid: issue("shape", r["type"], c, f"hover shape self-crosses: {explain_validity(raw)}", room=i)
    # outline of the same type
    best, bi = 0, None
    for j, o in enumerate(outlines):
        if o["type"] != r["type"] or not o["poly"].intersects(p): continue
        iou = o["poly"].intersection(p).area / o["poly"].union(p).area
        if iou > best: best, bi = iou, j
    r["outline_iou"] = round(best, 3)
    if bi is not None:
        outlines[bi].setdefault("rooms", []).append(i)
        # how far the hover shape strays from its outline: a fill stops at the wall's inner face, so up to a wall's
        # thickness is expected
        o = outlines[bi]["poly"]
        dev, ratio = p.hausdorff_distance(o), p.area / o.area
        r["outline_dev_mm"], r["outline_area_ratio"] = round(dev), round(ratio, 3)
        if dev > DEV_MM and r["type"] not in OPEN:
            # furniture islands that touch a wall notch the fill's edge: a smaller area than the outline but in its bounds
            ok = 0.8 <= ratio <= 1.05
            issue("outline", r["type"], c, f"{r['type'][3:]} ({r['m2']} m²): the hatch is {ratio:.0%} of its outline's area, "
                  f"its edge up to {dev / 1000:.2f} m off" + (" (furniture notches)" if ok else ""), level="note" if ok else "issue", room=i)
    if best < 0.5:
        issue("outline", r["type"], c, f"{r['type'][3:]} ({r['m2']} m²) has no matching outline in zoneBoundaries" + (f" (best overlap {best:.0%})" if best else ""), room=i)
    # labels
    inside = [l for l in labels if p.contains(Point(l["pt"]))]
    r["labels"] = [l["words"] for l in inside][:6]
    if r["type"] not in OPEN:
        if not inside:
            issue("label", r["type"], c, f"{r['type'][3:]} ({r['m2']} m²) has no label inside", room=i)
    # neighbourhood
    z = max(zones, key=lambda z: z["poly"].intersection(p).area, default=None)
    r["zone"] = z["name"] if z and z["poly"].intersection(p).area > 0.5 * p.area else None

# overlaps between hover shapes: the cursor would light two rooms
for i in range(len(rooms)):
    for j in range(i + 1, len(rooms)):
        a, b = rooms[i], rooms[j]
        if not a["poly"].intersects(b["poly"]): continue
        ov = a["poly"].intersection(b["poly"]).area
        if ov < 5e5: continue                       # under 0.5 m2: a shared wall line
        small = min(a["poly"].area, b["poly"].area)
        inner = a if a["poly"].area < b["poly"].area else b
        outer = b if inner is a else a
        if ov > 0.95 * small and outer["type"] in OPEN:
            continue                                # a room drawn over an open area (the room wins on top): fine for hover if drawn last
        c = a["poly"].intersection(b["poly"]).representative_point().coords[0]
        issue("overlap", a["type"], c, f"{a['type'][3:]} ({a['m2']} m²) and {b['type'][3:]} ({b['m2']} m²) overlap by {ov / 1e6:.1f} m² ({ov / small:.0%} of the smaller)", room=i, other=j)

# rooms lying inside an open-area hatch: hover needs the room on top
for r in rooms:
    if r["type"] in OPEN: continue
    for o in rooms:
        if o["type"] in OPEN and o["poly"].intersection(r["poly"]).area > 0.95 * r["poly"].area:
            r["inside_open"] = o["type"]; break

# outlines with no room hatch
for o in outlines:
    if o["type"] in ("AC_GLAZING", "AC_FIRE_COMPARTMENTALISATION"): continue
    if not o.get("rooms"):
        c = o["poly"].representative_point().coords[0]
        issue("outline", o["type"], c, f"outline {o['type'][3:]} ({o['poly'].area / 1e6:.1f} m²) has no room hatch" + (" (not closed in CAD)" if o["open"] else ""))

# labels in no room
union = unary_union([r["poly"] for r in rooms])
for l in labels:
    if l["layer"] == "OB-I-ANNO-TEXT" and not union.contains(Point(l["pt"])):
        issue("label", l["layer"], l["pt"], f"label {l['words'][:40]!r} sits in no room hatch")

# ---------------------------------------------------------------- write
def ring(p): return [[round(x), round(y)] for x, y in p.exterior.coords]
out = {
    "rooms": [{k: v for k, v in r.items() if k not in ("poly", "fill")} | {"shape": ring(r["poly"])} for r in rooms],
    "issues": issues,
    "summary": {"rooms": len(rooms), "by_type": dict(collections.Counter(r["type"] for r in rooms).most_common()),
                "outlines": len(outlines), "labels": len(labels), "issues": dict(collections.Counter(i["kind"] for i in issues))},
}
json.dump(out, open(os.path.join(DIR, "rooms.json"), "w", encoding="utf-8"), separators=(",", ":"))
out["summary"]["levels"] = dict(collections.Counter(i["kind"] + ":" + i["level"] for i in issues))
json.dump(out, open(os.path.join(DIR, "rooms.json"), "w", encoding="utf-8"), separators=(",", ":"))
print("issues", out["summary"]["levels"])
for i in issues:
    if i["level"] == "issue": print(f"  {i['kind']:8s} {i['layer'][:28]:28s} ({i['x']}, {i['y']})  {i['what']}")
