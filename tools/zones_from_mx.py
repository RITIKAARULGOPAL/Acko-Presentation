"""Build data/zones.json from the CAD team's cleaned MX-* layers.

Usage:
  python zones_from_mx.py <op1.dxf> <op2.dxf> <out zones.json>

Reads, per option (anything missing falls back to the provisional traced data
in author_zones.py, and is reported):

  MX-PROG-<TYPE>        closed polylines, TYPE in SOC WORK MEET BOARD ARRIVE COLLAB
                        CAFE STUDIO QUIET SERVICE SECURE CORE
  MX-EVT-50/100/200     closed polyline = event footprint
  MX-WALL-OPERABLE      open polylines = folding / operable walls (closed position)
  MX-GLASS-SOC          open polyline = SOC viewing glass
  MX-PATH-<NAME>        open polylines, NAME in VISITOR TOUR SERVICE EGRESS
  MX-CAM-<NAME>         LINE from eye point toward view direction (RECEPTION, SOC, ...)
  MX-SIG-<NAME>         POINT or CIRCLE (ARRIVAL WATCHWALL LANTERN COMMONS ONAIR)
  MX-FLOOR              closed polyline = floor-plate outline (annotation)

Coordinates are re-based with the origin that dxf_to_json.py stored in
data/optN.json, so both options and all layers stay aligned.
"""
import os, sys, json, math, logging
sys.stdout.reconfigure(encoding="utf-8")
logging.disable(logging.WARNING)
import ezdxf
from ezdxf import path as ezpath

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import author_zones as AZ  # noqa: E402  (provisional data + shared helpers)

PROG = {"SOC": "soc", "WORK": "focus", "FOCUS": "focus", "MEET": "meet", "BOARD": "board", "ARRIVE": "arrive",
        "COLLAB": "collab", "CAFE": "cafe", "STUDIO": "studio", "QUIET": "quiet", "SERVICE": "service",
        "SECURE": "secure", "CORE": "core"}


def entity_points(e, closed_only=False):
    """Flatten an entity to a list of (x, y)."""
    t = e.dxftype()
    if t == "LINE":
        return [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
    if t in ("POINT",):
        return [(e.dxf.location.x, e.dxf.location.y)]
    if t == "CIRCLE":
        return [(e.dxf.center.x, e.dxf.center.y)]
    try:
        p = ezpath.make_path(e)
        pts = [(v.x, v.y) for v in p.flattening(20)]
    except Exception:
        return []
    if closed_only and len(pts) > 2 and math.dist(pts[0], pts[-1]) > 5:
        is_closed = getattr(e, "closed", False) or getattr(e, "is_closed", False)
        if not is_closed:
            return []
    if len(pts) > 2 and math.dist(pts[0], pts[-1]) < 5:
        pts = pts[:-1]
    return pts


def read_option(dxf_path, origin):
    X0, Y0 = origin
    doc = ezdxf.readfile(dxf_path)
    loc = lambda pts: [[round(x - X0), round(y - Y0)] for x, y in pts]
    out = {"zones": [], "events": {}, "walls": [], "routes": {}, "cameras": {}, "signature": {}, "socGlass": None, "floor": None}
    for e in doc.modelspace():
        L = e.dxf.layer.upper()
        if not L.startswith("MX-"):
            continue
        key = L[3:]
        if key.startswith("PROG-"):
            t = PROG.get(key[5:])
            pts = entity_points(e, closed_only=True)
            if t and len(pts) >= 3:
                out["zones"].append((t, [loc(pts)]))
        elif key.startswith("EVT-"):
            pts = entity_points(e, closed_only=True)
            if len(pts) >= 3:
                out["events"][key[4:]] = loc(pts)
        elif key == "WALL-OPERABLE":
            out["walls"].append(loc(entity_points(e)))
        elif key == "GLASS-SOC":
            out["socGlass"] = loc(entity_points(e))
        elif key.startswith("PATH-"):
            out["routes"][key[5:].lower()] = loc(entity_points(e))
        elif key.startswith("CAM-") and e.dxftype() == "LINE":
            (x1, y1), (x2, y2) = entity_points(e)
            d = math.hypot(x2 - x1, y2 - y1) or 1
            out["cameras"][key[4:].lower()] = {"at": [round(x1 - X0), round(y1 - Y0)], "dir": [round((x2 - x1) / d, 3), round((y2 - y1) / d, 3)]}
        elif key.startswith("SIG-"):
            p = entity_points(e)
            if p:
                out["signature"][key[4:].lower()] = [round(p[0][0] - X0), round(p[0][1] - Y0)]
        elif key == "FLOOR":
            out["floor"] = loc(entity_points(e, closed_only=True))
    return out


def merge(mx, fallback, name):
    """Use MX data where present; keep provisional data (and say so) elsewhere."""
    used, kept = [], []
    opt = {}
    if mx["zones"]:
        opt["zones"] = mx["zones"]; used.append(f"{len(mx['zones'])} zones")
    else:
        opt["zones"] = fallback["zones"]; kept.append("zones")
    opt["events"] = {}
    for lvl, ev in fallback["events"].items():
        if lvl in mx["events"]:
            opt["events"][lvl] = dict(ev, poly=mx["events"][lvl]); used.append(f"event {lvl}")
        else:
            opt["events"][lvl] = ev; kept.append(f"event {lvl}")
    for k in ("walls", "routes", "cameras", "signature"):
        if mx[k]:
            opt[k] = mx[k]; used.append(k)
        else:
            opt[k] = fallback[k]; kept.append(k)
    opt["socGlass"] = mx["socGlass"] or fallback["socGlass"]
    (used if mx["socGlass"] else kept).append("socGlass")
    print(f"{name}: from MX layers -> {', '.join(used) or 'nothing'}")
    print(f"{name}: provisional (not in DXF) -> {', '.join(kept) or 'nothing'}")
    return opt


def main():
    op1, op2, dst = sys.argv[1], sys.argv[2], sys.argv[3]
    fallback = {"opt1": AZ.OPT1, "opt2": AZ.OPT2}
    built, floor = {}, None
    for name, path in (("opt1", op1), ("opt2", op2)):
        origin = json.load(open(os.path.join(ROOT, "data", f"{name}.json")))["origin_dxf"]
        mx = read_option(path, origin)
        floor = floor or mx["floor"]
        built[name] = AZ.build(merge(mx, fallback[name], name))
    annot = dict(AZ.ANNOT)
    if floor:
        annot["outline"] = floor
    out = dict(types={k: dict(label=v[0], tier=v[1]) for k, v in AZ.TYPES.items()},
               opt1=built["opt1"], opt2=built["opt2"], annot=annot, floor_area=round(AZ.area_m2(annot["outline"])))
    json.dump(out, open(dst, "w"), separators=(",", ":"))
    print("wrote", dst, "| floor area", out["floor_area"], "m2")


if __name__ == "__main__":
    main()
