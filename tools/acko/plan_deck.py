"""The deck's floor plan from the checked plan export (plan_vector.py + plan_rooms.py, approved in plan_view.html).

Writes, from <export dir> (e.g. tools/_work/plan-28):
  data/plan-base.js   window.PLAN_BASE: the base plan, plants and labels as plan_vector.py instanced them, drawn by
                      assets/js/plan-canvas.js under the deck's hovers (vector at every zoom; replaces the pictures and
                      plan-vec.js on the layout and blow-up slides)
  data/plan-dxf.js    window.PLAN_DXF, rewritten: its spaces are the approved hover shapes (furniture cut out), typed and
                      coloured by the deck's legend; the neighbourhood outlines are the export's; seats, desks, occupancy,
                      egress, overlays and the pictures' levels are kept from the current file (the axo and key plans use them)

The deck draws in the toolkit's SVG frame: (x - OX, OY - y) of the DXF's mm. OX, OY were the toolkit's (full.svg data-ox,
data-oy) for the 22.10 drawing, which the export keeps its coordinates in (28.10 is shifted onto it).

usage: python tools/acko/plan_deck.py <export dir>
"""
import sys, os, re, ast, json, time
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OX, OY = -185842, -211384          # deck frame = (x - OX, OY - y); matched on 110 of the 22.10 rooms (IoU > 0.8)
GROUPS = ["base", "vegetation", "text"]
OUT_TYPES = {"OUT_OF_ZONE"}         # not a space the deck names (the floor outside the neighbourhoods)

def consts(path, *names):
    """top-level literals of a tool, without running it (named_layers.py needs cv2)"""
    tree, out = ast.parse(open(path, encoding="utf-8").read()), {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in names:
            out[n.targets[0].id] = ast.literal_eval(n.value)
    return out

here = os.path.dirname(os.path.abspath(__file__))
C = consts(os.path.join(here, "plan_dxf.py"), "LEGEND", "EXTRA_COLOURS") | consts(os.path.join(here, "named_layers.py"), "LAYER_TYPE", "NAMED")
LAYER_TYPE = C["LAYER_TYPE"] | {"DEALER_ROOM": "Dealer room", "GREEN_ROOM": "Green room", "STORE_ROOM": "Store room"}
NAMED = set(C["NAMED"]) | {"Dealer room", "Green room"}
COLOUR = {t: "#" + c for t, c in C["LEGEND"] + C["EXTRA_COLOURS"]} | {"Dealer room": "#D9D3C7", "Green room": "#CFDCC9"}

def title(t):
    t = re.sub(r"[A-Za-z]+(?:'[A-Za-z]+)?", lambda m: m.group(0).capitalize(), t)
    return re.sub(r"\s*-\s*", " - ", re.sub(r"\bPax\b", "PAX", re.sub(r"\bPb\b", "PB", t)))

def deck(x, y): return x - OX, OY - y

def poly_of(d):
    """an SVG path's rings as one shape (in its own frame), even-odd"""
    g = Polygon()
    for r in re.findall(r"M([^Z]+)Z", d):
        pts = [tuple(map(float, q.split())) for q in r.split("L")]
        if len(pts) > 2: g = g.symmetric_difference(Polygon(pts).buffer(0))
    return g.buffer(0)

def d_of(geom):
    """rings as an SVG path in the deck frame; shells and holes wound opposite ways, so nonzero fills keep the holes"""
    out = []
    for g in getattr(geom, "geoms", [geom]):
        g = orient(g, -1.0)                       # y flips into the deck frame, which turns this the other way round
        for r in [g.exterior] + list(g.interiors):
            out.append("M" + "L".join("%d %d" % tuple(round(v) for v in deck(x, y)) for x, y in list(r.coords)[:-1]) + "Z")
    return "".join(out)

def texts(meta, src):
    """every label of the text group: (words, x, y) in the DXF's mm"""
    out = []
    for b in meta["blocks"]:
        if b["group"] != "text": continue
        data = json.load(open(os.path.join(src, b["file"]), encoding="utf-8"))
        defs = data["defs"]
        def walk(di, m):
            d = defs[di]; q = 10 ** -d["q"]
            for run in d["runs"]:
                if run[4] == "i":
                    for ci, ca, cb, cc, cd, ce, cf in run[5]:
                        walk(ci, [m[0] * ca + m[2] * cb, m[1] * ca + m[3] * cb, m[0] * cc + m[2] * cd, m[1] * cc + m[3] * cd,
                                  m[0] * ce + m[2] * cf + m[4], m[1] * ce + m[3] * cf + m[5]])
                elif run[4] == "t":
                    for t in run[5]:
                        X, Y = t[0] * q, t[1] * q
                        out.append((" ".join(str(t[6]).split()), m[0] * X + m[2] * Y + m[4], m[1] * X + m[3] * Y + m[5]))
        walk(data["root"], data["place"]["m"])
    return out

def main(src):
    meta = json.load(open(os.path.join(src, "layers.json"), encoding="utf-8"))
    rooms = json.load(open(os.path.join(src, "rooms.json"), encoding="utf-8"))["rooms"]
    checked = json.load(open(os.path.join(src, "checked.json"), encoding="utf-8"))
    fine = set(checked.get("fine", []))

    # ---- the base plan, as exported (instanced), with the layers it uses
    blocks, used = [], set()
    for b in meta["blocks"]:
        if b["group"] not in GROUPS: continue
        data = json.load(open(os.path.join(src, b["file"]), encoding="utf-8"))
        blocks.append({"group": b["group"], "block": b["block"], "data": data})
        for d in data["defs"]:
            for run in d["runs"]: used.add(run[0])
        used.add(data["place"]["spec"][0])
    layers = {k: v for k, v in meta["layers"].items() if k in used or k == "0"}
    base = {"source": meta.get("sources"), "built": time.strftime("%Y-%m-%d %H:%M"), "origin": [OX, OY],
            "layers": layers, "linetypes": meta.get("linetypes", {}), "ltscale": meta.get("ltscale", 1), "blocks": blocks}
    p = os.path.join(ROOT, "data", "plan-base.js")
    with open(p, "w", encoding="utf-8") as f:
        f.write("/* generated by tools/acko/plan_deck.py from the checked plan export: don't hand-edit */\n")
        f.write("window.PLAN_BASE = " + json.dumps(base, separators=(",", ":")) + ";\n")
    print(f"{p}: {os.path.getsize(p) / 1e6:.1f} MB, {len(blocks)} blocks, {len(layers)} layers")

    # ---- the spaces: the approved hover shapes
    s = open(os.path.join(ROOT, "data", "plan-dxf.js"), encoding="utf-8").read()
    P = json.loads(s[s.index("{"):s.rindex("}") + 1])
    spaces, skipped = [], []
    # a room with no label inside takes the nearest label of its kind outside it (the 2-pax rooms' "2 PAX - 10" stands
    # in the aisle beside them, often over the workhall's hatch), within 2.5 m, each label once
    from shapely.geometry import Point
    stray = [(w, Point(x, y)) for w, x, y in texts(meta, src) if re.search(r"\b\d+ PAX\b", w)]
    bare = [r for r in rooms if r["rings"] and not any(l.strip() for l in r.get("labels", []))]
    stray = [(w, p) for w, p in stray if not any(w in r.get("labels", []) for r in rooms)]
    pairs = sorted((Polygon(r["shape"]).buffer(0).distance(p), r["id"], w) for r in bare if r.get("shape") for w, p in stray)
    given, taken = {}, set()
    for dist, rid, w in pairs:
        if dist > 2500 or rid in given or w in taken: continue
        given[rid] = w; taken.add(w)
    for r in rooms:
        if r["id"] in given: r["labels"] = [given[r["id"]]]
    print(f"  {len(given)} rooms named by a label beside them")
    for r in sorted(rooms, key=lambda r: r["id"]):
        k = r["type"][3:]
        if k in OUT_TYPES or not r["rings"]: continue
        t = LAYER_TYPE.get(k)
        if t is None: skipped.append(r["type"]); continue
        if r["id"] not in fine: print(f"  note: #{r['id']} {t} isn't approved yet")
        g = unary_union([Polygon(q[0], q[1:]).buffer(0) for q in r["rings"]])
        lab = next((l for l in r.get("labels", []) if l.strip()), "")
        name = title(lab) if t in NAMED and lab else t
        x, y = deck(r["x"], r["y"])
        spaces.append({"type": t, "name": name, "colour": COLOUR.get(t, "#E4E2DD"), "m2": r["m2"], "x": round(x), "y": round(y),
                       "d": d_of(g), "id": "r%d" % r["id"]})
    if skipped: print("  types the deck has no name for:", sorted(set(skipped)))

    # ---- the neighbourhood outlines: the export's AC_<zone> polylines, matched to the deck's zones by name
    nb = {}
    for b in meta["blocks"]:
        if b["group"] != "neighbourhoods": continue
        data = json.load(open(os.path.join(src, b["file"]), encoding="utf-8"))
        m, k = data["place"]["m"], None
        for d in data["defs"]:
            q = 10 ** -d["q"]
            for run in d["runs"]:
                if run[4] != "s" or not run[0].startswith("AC_"): continue
                for a in run[5]:
                    pts, x, y = [], a[0], a[1]
                    for i in range(0, len(a), 2):
                        if i: x += a[i]; y += a[i + 1]
                        X, Y = x * q, y * q
                        pts.append((m[0] * X + m[2] * Y + m[4], m[1] * X + m[3] * Y + m[5]))
                    if len(pts) > 3: nb.setdefault(run[0][3:].title(), []).append(Polygon(pts).buffer(0))
    # the 22.10 build's zones were numbered off a self-crossing AC_DRIVE outline: its "04 · Drive" lay in Home and its Travel
    # held Drive's desks too (0 and 186 seats). With the export's outlines each zone's seats are re-counted from the
    # workstation inserts inside it (types[].uses, at their insertion point; one outside every outline goes to the nearest):
    # a zone holding exactly the inserts it held before keeps its count; the others share their old total by the inserts'
    # weight in seats (T1 1, T2 1, T3 4, T4 3: the best fit to the counts of the zones that were right)
    W = {"T1": 1, "T2": 1, "T3": 4, "T4": 3}
    from shapely.geometry import Point
    def polys(Z): return {z["id"]: poly_of(z["zone"]) for z in Z}
    old_polys = polys(P["zones"])
    for z in P["zones"]:
        key = z["name"].split("·")[-1].strip()
        if key not in nb: print(f"  zone {z['name']}: no outline in the export, kept"); continue
        g = max(nb[key], key=lambda g: g.area)
        z["zone"] = d_of(g); z["desks"] = [z["zone"]]
        x0, y0 = deck(g.bounds[0], g.bounds[3]); x1, y1 = deck(g.bounds[2], g.bounds[1])
        z["box"] = [round(x0), round(y0), round(x1), round(y1)]
        z["m2"] = round(g.area / 1e6, 1); z["overlap"] = 1.0
        # its number and seats stay where they were if that's still inside it, else go to a point well inside it
        if not g.contains(Point(z["x"] + OX, OY - z["y"])):
            from shapely.ops import polylabel
            c = polylabel(max(getattr(g, "geoms", [g]), key=lambda q: q.area), 50)
            z["x"], z["y"] = (round(v) for v in deck(c.x, c.y))
            print(f"  {z['name']}: label moved into its outline")
    new_polys = polys(P["zones"])
    def tally(PP):
        out = {k: {} for k in PP}
        for t in P["types"]:
            for u in t["uses"]:
                p = Point(u[5], u[6]); k = min(PP, key=lambda k: PP[k].distance(p))
                out[k][t["t"]] = out[k].get(t["t"], 0) + 1
        return out
    before, after = tally(old_polys), tally(new_polys)
    weight = lambda c: sum(W[t] * n for t, n in c.items())
    moved = [z for z in P["zones"] if before[z["id"]] != after[z["id"]]]
    pool = sum(z["seats"] for z in moved); wsum = sum(weight(after[z["id"]]) for z in moved) or 1
    for z in moved:
        z["seats"] = round(pool * weight(after[z["id"]]) / wsum)
        print(f"  {z['name']}: workstations re-counted, {z['seats']} seats (estimate: check against the PPT)")
    if moved and sum(z["seats"] for z in moved) != pool: moved[-1]["seats"] += pool - sum(z["seats"] for z in moved)
    rows = consts(os.path.join(here, "plan_dxf.py"), "OCC_ROWS")["OCC_ROWS"]
    for z in P["zones"]:
        g, occ = new_polys[z["id"]], [["Workhall", "Workstations", z["seats"]]]
        inside = [sp for sp in spaces if g.contains(Point(sp["x"], sp["y"])) and sp["name"] != sp["type"]]
        for grp, area, rx in rows:
            n = sum((sum(1 for part in sp["name"].split(" / ") if re.search(rx, part, re.I)) if area in ("Phone booth", "Focus room - 2 pax")
                     else int(bool(re.search(rx, sp["name"], re.I)))) for sp in inside)
            if n: occ.append([grp, area, n])
        z["occ"] = occ
    print("  seats:", ", ".join(f"{z['name']} {z['seats']}" for z in P["zones"]), "=", sum(z["seats"] for z in P["zones"]))

    P["spaces"], P["built"] = spaces, time.strftime("%Y-%m-%d %H:%M")
    P["source"] = "plan export " + os.path.basename(os.path.normpath(src)) + " (" + ", ".join(meta.get("sources") or []) + ")"
    p = os.path.join(ROOT, "data", "plan-dxf.js")
    with open(p, "w", encoding="utf-8") as f:
        f.write("/* spaces and neighbourhood outlines by tools/acko/plan_deck.py from the checked plan export (seats, desks, egress,\n"
                "   overlays and pictures from tools/acko/plan_dxf.py's last build): don't hand-edit */\n")
        f.write("window.PLAN_DXF = " + json.dumps(P, separators=(",", ":"), ensure_ascii=False) + ";\n")
    print(f"{p}: {len(spaces)} spaces, {len(P['zones'])} zones")

if __name__ == "__main__":
    main(sys.argv[1])
