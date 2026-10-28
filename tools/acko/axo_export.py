"""The axo builder's input (tools/acko/axo_dxf.py) from the checked plan export, in place of the DXF plan toolkit's output.

axo_dxf.py reads a toolkit run: instanced.svg (each block's geometry once, classed "<s|f> <wall|glass|door|furn|green|base|
shade|anno>", placed by <use transform="matrix(...)">, plus loose paths) and rooms.json (the space-plan outlines: the
terrace, what is not in contract). This writes the same from plan_vector.py's export (tools/_work/plan-28), in the deck's
frame (x - OX, OY - y; plan_deck.py's), so axo_dxf.py runs on it unchanged:

    python tools/acko/axo_export.py tools/_work/plan-28 tools/_work/axo-in
    python tools/acko/axo_dxf.py tools/_work/axo-in

Nested blocks are flattened: a definition with geometry of its own becomes one <g> per class context (layer-0 and
BYLAYER entities take the layer they are placed on), and every placement of it, composed down from the model space, one
<use>. Class by layer, as assets/js/plan-canvas.js draws the plan.
"""
import sys, os, re, json

OX, OY = -185842, -211384
GLASS = re.compile(r"GLASS|GLSS|GLS|GLAZ|_IN_GL\b", re.I); GREEN = re.compile(r"PLANT|PLNT|GRASS|LANDSCAP|TREE|SHRUB|VEG", re.I)
DOOR = re.compile(r"DOOR|_DOR_|DOR-", re.I); WALL = re.compile(r"WALL|PART|PRTN|COLS|S-COL|CORE|STRU", re.I)
FURN = re.compile(r"FURN|\bFUR\b|_FUR_|CHAIR|TABLE|SEAT|SOFA|STORAGE|TV UNIT|^AC_WS_|EQPM|MLWK|FIXT|PLBG|ELEV", re.I)
SHADE = re.compile(r"SHADE|PATT|HATCH", re.I); ANNO = re.compile(r"ANNO|TEXT|DIM|TAG|IDEN", re.I)

def cls(layer, group, veg):
    return ("green" if veg or group == "vegetation" or GREEN.search(layer) else "glass" if GLASS.search(layer) else
            "door" if DOOR.search(layer) else "wall" if WALL.search(layer) else "furn" if FURN.search(layer) else
            "shade" if SHADE.search(layer) else "anno" if ANNO.search(layer) else "base")

def pts(a, k):
    out, x, y = [], a[0], a[1]
    for i in range(0, len(a), 2):
        if i: x += a[i]; y += a[i + 1]
        out.append((x * k, y * k))
    return out

def d_of(rings, close):
    return "".join("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in r) + ("Z" if close else "") for r in rings if len(r) > 1)

def main(src, out):
    meta = json.load(open(os.path.join(src, "layers.json"), encoding="utf-8"))
    L = meta["layers"]
    blocks, uses, loose = {}, [], []
    for b in meta["blocks"]:
        if b["group"] not in ("base", "vegetation"): continue
        data = json.load(open(os.path.join(src, b["file"]), encoding="utf-8"))
        defs, group = data["defs"], b["group"]
        def resolve(spec, ctx):
            return {"layer": spec[0] or ctx["layer"], "veg": ctx["veg"]}
        def walk(di, M, ctx, top):
            d = defs[di]; k = 10 ** -d["q"]
            if d.get("veg"): ctx = dict(ctx, veg=True)
            a, bb, c, e, f, g = M
            geo = []                                     # (kind, cls, rings) in the definition's own coordinates
            for run in d["runs"]:
                l, col, lt, lw, kind, items = run
                st = resolve([l], ctx)
                if kind == "i":
                    if L.get(st["layer"], {}).get("frozen"): continue
                    for ci, ca, cb, cc, cd, ce, cf in items:
                        walk(ci, [a * ca + c * cb, bb * ca + e * cb, a * cc + c * cd, bb * cc + e * cd, a * ce + c * cf + f, bb * ce + e * cf + g], st, False)
                    continue
                lay = L.get(st["layer"], {})
                if lay.get("off") or lay.get("frozen") or kind not in ("s", "f"): continue
                # inside a furniture block, what is drawn on layer 0 is the toolkit's "base" (a pod's desk tops: axo_dxf.py
                # closes them across the breaks its chairs leave)
                c_ = cls(st["layer"], group, st["veg"])
                if c_ == "furn" and not top and not l: c_ = "base"
                for it in items:
                    geo.append((kind, c_, [pts(r, k) for r in ([it] if kind == "s" else it)]))
            if not geo: return
            # deck frame: (x, y) -> (x - OX, OY - y) after the placement
            m = [a, -bb, c, -e, f - OX, OY - g]
            if top:                                       # model space's own lines: loose, already placed
                for kind, c_, rings in geo:
                    pl = [[(m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]) for x, y in r] for r in rings]
                    loose.append((f"{kind} {c_}", d_of(pl, kind == "f")))
                return
            key = (group, di, ctx["layer"], ctx["veg"])
            if key not in blocks:
                blocks[key] = ("b%d" % len(blocks), [(f"{kind} {c_}", d_of(rings, kind == "f")) for kind, c_, rings in geo])
            uses.append((blocks[key][0], m))
        root = {"layer": "0", "veg": False}
        walk(data["root"], data["place"]["m"], resolve(data["place"]["spec"], root), True)

    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "instanced.svg"), "w", encoding="utf-8") as fh:
        fh.write('<svg xmlns="http://www.w3.org/2000/svg"><defs>')
        for bid, paths in blocks.values():
            fh.write(f'<g id="{bid}">' + "".join(f'<path class="{c}" d="{d}"/>' for c, d in paths) + "</g>")
        fh.write("</defs>")
        for bid, m in uses:
            fh.write(f'<use href="#{bid}" transform="matrix({" ".join(f"{v:.6f}" if i < 4 else f"{v:.1f}" for i, v in enumerate(m))})"/>')
        for c, d in loose: fh.write(f'<path class="{c}" d="{d}"/>')
        fh.write("</svg>")

    # rooms.json: the terrace, and the floor outside the contract (the hotel band and its cores), as the toolkit named them
    rooms = json.load(open(os.path.join(src, "rooms.json"), encoding="utf-8"))["rooms"]
    def dd(r):
        return "".join("M" + "L".join(f"{x - OX:.0f} {OY - y:.0f}" for x, y in ring) + "Z" for q in r["rings"] for ring in q)
    spaces = [{"name": "Terrace", "layer": "AC_TERRACE", "m2": r["m2"], "d": dd(r)} for r in rooms if r["type"] == "AC_TERRACE"]
    spaces += [{"name": "Not in contract", "layer": "AC_OUT_OF_SCOPE", "m2": r["m2"], "d": dd(r)} for r in rooms if r["type"] == "AC_OUT_OF_ZONE"]
    json.dump({"spaces": spaces}, open(os.path.join(out, "rooms.json"), "w", encoding="utf-8"))
    print(f"{out}: {len(blocks)} blocks, {len(uses)} placements, {len(loose)} loose paths; {len(spaces)} spaces in rooms.json")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
