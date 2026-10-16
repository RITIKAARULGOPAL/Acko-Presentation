"""Explode a DXF plan into aligned 2D data for the web presentation.

Usage: python dxf_to_json.py <in.dxf> <out_json> <out_furniture_png> [--px-per-m 80]

* Every INSERT is exploded recursively; entities on layer "0" inherit the layer
  of the INSERT that placed them.
* Geometry is sorted into groups by layer name / placing block:
  shell (base building block) | partition | glass | door | furniture | plant.
* Coordinates are re-based so the base-building shell's lower-left corner is
  (0, 0), in millimetres, y up. Both options share the same shell block, so
  this aligns OP1 and OP2 exactly.
* Vector groups (shell / partition / glass / door) are written to JSON as
  polylines; furniture + plants are rasterised (white on transparent) into a
  floor texture so the browser doesn't have to draw ~50k tiny paths.
"""
import sys, json, re, logging
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")
logging.disable(logging.WARNING)
import ezdxf
from ezdxf import path as ezpath
from PIL import Image, ImageDraw

SHELL_BLOCKS = {"zw$DF8"}
BIG_BLOCK = 1500  # blocks this large are furniture/plant symbols even if mis-layered (e.g. OP2 "fgbg" on a glass-door layer)
RULES = [  # (group, regex on layer name) - first match wins
    ("glass",     r"GLS|GLSS|GLASS|_GL$|IN_GL"),
    ("door",      r"DOOR|DOR_|DOORWIN"),
    ("partition", r"PART|PRTN|WALL"),
    ("plant",     r"PLANT|Plants|Landscape|TREE|PLNT"),
    ("anno",      r"ANNO|TEXT|DIM|TAGS|Defpoints"),
]
PLANT_BLOCK = re.compile(r"TREE|palm|Palm|plant|Plant|flower|PLANT|12PPLT|A\$C78742900")
VECTOR_GROUPS = ("shell", "partition", "glass", "door")


def group_of(layer, top_block, plant_inst, big_blocks):
    if top_block in SHELL_BLOCKS:
        return "shell"
    if plant_inst is not None:
        return "plant"
    if top_block in big_blocks:
        return "furniture"
    for g, rx in RULES:
        if re.search(rx, layer, re.I):
            return g
    return "furniture"


def is_frame(pts, W, H):
    """Drawing frames / site rectangles: polylines spanning most of the sheet."""
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return (max(xs) - min(xs)) > 0.6 * W and (max(ys) - min(ys)) > 0.6 * H


def eff_layer(entity, inherited):
    try:
        own = entity.dxf.layer
    except Exception:
        own = "0"
    return inherited if own == "0" and inherited else own


def explode(entity, inherited, top_block, plant_inst):
    if entity.dxftype() == "INSERT":
        layer = eff_layer(entity, inherited)
        name = entity.dxf.name
        tb = name if name in SHELL_BLOCKS else (top_block or name)
        if plant_inst is None and (PLANT_BLOCK.search(name) or re.search(r"PLANT|Plants|Landscape|PLNT", layer, re.I)):
            plant_inst = id(entity)
        try:
            children = list(entity.virtual_entities())
        except Exception:
            return
        for ve in children:
            yield from explode(ve, layer, tb, plant_inst)
    else:
        yield entity, eff_layer(entity, inherited), top_block, plant_inst


def flatten(entity, tol):
    t = entity.dxftype()
    if t in ("TEXT", "MTEXT", "ATTRIB", "ATTDEF", "DIMENSION", "POINT", "WIPEOUT", "VIEWPORT", "IMAGE"):
        return []
    if t == "HATCH":
        try:
            if not entity.dxf.solid_fill:
                return []
            return [("fill", [(v.x, v.y) for v in p.flattening(tol)]) for p in ezpath.from_hatch(entity)]
        except Exception:
            return []
    try:
        p = ezpath.make_path(entity)
    except Exception:
        return []
    out = []
    for sp in (p.sub_paths() if p.has_sub_paths else [p]):
        try:
            pts = [(v.x, v.y) for v in sp.flattening(tol)]
        except Exception:
            continue
        if len(pts) >= 2:
            out.append(("line", pts))
    return out


def text_of(e):
    t = e.dxftype()
    try:
        if t == "MTEXT":
            s, ins, h = e.plain_text(), e.dxf.insert, e.dxf.char_height
        elif t in ("TEXT", "ATTRIB"):
            s, ins, h = e.dxf.text, e.dxf.insert, e.dxf.height
        else:
            return None
    except Exception:
        return None
    s = " ".join(s.split())
    return (s, ins.x, ins.y, h) if s else None


def main():
    src, out_json, out_png = sys.argv[1], sys.argv[2], sys.argv[3]
    px_per_m = 80.0
    if "--px-per-m" in sys.argv:
        px_per_m = float(sys.argv[sys.argv.index("--px-per-m") + 1])
    doc = ezdxf.readfile(src)
    big_blocks = {b.name for b in doc.blocks if len(b) > BIG_BLOCK and b.name not in SHELL_BLOCKS}
    raw = defaultdict(list)          # group -> [(kind, pts)]
    plants = defaultdict(list)       # plant instance -> pts
    texts = []
    for top in doc.modelspace():
        tb = top.dxf.name if top.dxftype() == "INSERT" else None
        for e, layer, topb, pinst in explode(top, None, tb, None):
            L = doc.layers.get(layer) if doc.layers.has_entry(layer) else None
            if L is not None and (L.is_off() or L.is_frozen()):
                continue
            g = group_of(layer, topb, pinst, big_blocks)
            tx = text_of(e)
            if tx:
                if g != "anno" or "ANNO" in layer.upper():
                    texts.append((tx, layer))
                continue
            for kind, pts in flatten(e, 12.0):
                if len(pts) < 2:
                    continue
                raw[g].append((kind, pts))
                if pinst is not None:
                    plants[pinst].extend(pts)

    # origin = lower-left of the base-building shell
    sx = [x for _, pts in raw["shell"] for x, _ in pts]
    sy = [y for _, pts in raw["shell"] for _, y in pts]
    X0, Y0, X1, Y1 = min(sx), min(sy), max(sx), max(sy)
    W, H = X1 - X0, Y1 - Y0
    inside = lambda x, y: -2000 <= x - X0 <= W + 2000 and -2000 <= y - Y0 <= H + 2000

    for g in raw:
        raw[g] = [(k, pts) for k, pts in raw[g] if not is_frame(pts, W, H)]
    vec = {g: [] for g in VECTOR_GROUPS}
    fills = []
    for g in VECTOR_GROUPS:
        for kind, pts in raw[g]:
            if not any(inside(x, y) for x, y in pts):
                continue
            flat = [round(c) for x, y in pts for c in (x - X0, y - Y0)]
            (fills if kind == "fill" and g == "shell" else vec[g]).append(flat)

    # furniture + plant raster (supersampled 2x for smooth lines)
    ss = 2
    s = px_per_m / 1000.0 * ss
    img = Image.new("L", (int(W * s) + 1, int(H * s) + 1), 0)
    dr = ImageDraw.Draw(img)
    for g, val in (("furniture", 200), ("plant", 255)):
        for kind, pts in raw[g]:
            if not any(inside(x, y) for x, y in pts):
                continue
            xy = [((x - X0) * s, (Y1 - y) * s) for x, y in pts]
            if kind == "fill" and len(xy) > 2:
                dr.polygon(xy, fill=val // 3)
            else:
                dr.line(xy, fill=val, width=ss)
    img = img.resize((img.width // ss, img.height // ss), Image.LANCZOS)
    rgba = Image.merge("RGBA", (Image.new("L", img.size, 255),) * 3 + (img,))
    rgba.save(out_png)

    plant_list = []
    for pts in plants.values():
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        if inside(cx, cy):
            plant_list.append([round(cx - X0), round(cy - Y0), round(max(max(xs) - min(xs), max(ys) - min(ys)) / 2)])

    seen = set(); tlist = []
    for (s_, x, y, h), layer in texts:
        key = (s_, round(x / 100), round(y / 100))
        if key in seen or not inside(x, y):
            continue
        seen.add(key)
        tlist.append(dict(t=s_, x=round(x - X0), y=round(y - Y0), h=round(h)))

    fx = [v for p in vec["shell"] for v in p[0::2]]; fy = [v for p in vec["shell"] for v in p[1::2]]
    data = dict(size=[round(W), round(H)], origin_dxf=[X0, Y0],
                floor=[min(fx), min(fy), max(fx), max(fy)],
                raster=dict(file=out_png.replace("\\", "/").split("/")[-1], px_per_m=px_per_m,
                            w=rgba.width, h=rgba.height),
                vec=vec, fills=fills, plants=plant_list, texts=tlist)
    json.dump(data, open(out_json, "w"), separators=(",", ":"))
    print("size(mm)", data["size"], "| vec", {g: len(v) for g, v in vec.items()},
          "| fills", len(fills), "| plants", len(plant_list), "| texts", len(tlist),
          "| raster", rgba.size)


if __name__ == "__main__":
    main()
