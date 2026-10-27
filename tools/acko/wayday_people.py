"""A day in ACKO's people (Ritika, 27 Oct: "make sure there are tiny humans doing activity in each space when we zoom to that
particular space ... instead we'll have a day in acko and only show spaces with human activity in it ... humans can be in
monochromatic dark grey").

Usage:  python -I tools/acko/wayday_people.py
        (after tools/acko/axo_skp.py, whose route check leaves the floor's walking layers in tools/_work/axo-skp/route.npz)

  seats   every chair of the layout (data/axo-dxf.js: the blocks' chairs placed by their uses, and the loose ones), facing the
          nearest desk or table within 1.2 m, else its space's middle; shifted onto the SketchUp model's own walls (the fine
          fit of AXO_DXF's walls onto route.npz's, as tools/acko/wayday_marks.py does for her marks)
  who     by the space each seat is in (data/plan-dxf.js): workhalls 60% taken; meeting rooms (departmental, quick sprint,
          collaboration huddle, visitor hub, training) about half in session, nearly full with a presenter at one end, the rest
          empty; the boardroom in session; the cafeteria 45% with pairs standing; Reception a receptionist and visitors at
          the desk; the open Collabs a standing huddle; Zen rooms one person on the floor; the terraces pairs; phone booths
          half; cabins one. A fixed seed, so a build repeats.
  garden  the Acker Garden on the west tip's deck (from her workhall 2.skp): one in the swing, two in the chairs over the chess,
          one on the pouf, one at the punching bag, two at the foosball (drawn by the slide: not in that file), all on the deck
  walk    about 40 people walking the corridors, each an A* path (axo_skp.Walker) there and back
Writes the `const PEOPLE = {...};` line in slides/s-wayday.html (plan mm, y down; angles in centiradians, plan frame:
{sit, stand, present, yoga: [[x, y, a(, h)]], walk: [[[x, y], ...]], props: {foosball: [x, y, a, h]}}; h, what they sit or
stand on, mm) and tools/_work/wayday/people.png to check.
"""
import json, math, os, re, sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import axo_skp
import wayday_marks

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, "tools", "_work", "wayday")
SLIDE = os.path.join(ROOT, "slides", "s-wayday.html")
IN_SESSION = {"Departmental Rooms 18 PAX - 01", "Boardroom 35 PAX"}      # the day's own meeting rooms: always in use
ROOMS = ("Departmental room", "Quick sprint", "Collaboration huddle", "Visitor hub", "Training room", "Boardroom")
# the Acker Garden on the west tip's raised deck (Ritika, 27 Oct: "for collab area, do the exact furniture and raised flooring
# that's there in the skp ... add punch bags and all"; her workhall 2.skp): its pieces in SketchUp metres (x, y), and who uses
# them; the foosball is in her view of the model but not in that file, so the slide draws one where it stands (PEOPLE.props)
DECK = 130                                                            # the deck's top, mm over the floor
GARDEN = {"swing": (7.72, 29.87), "bag": (7.78, 31.44), "chairs": [(7.71, 32.05), (8.90, 33.15)], "chess": (8.23, 32.70),
          "pouf": (8.01, 30.74), "foosball": (9.90, 32.50), "inside": (9.80, 31.00)}


def js(name, var):
    s = open(os.path.join(ROOT, "data", name), encoding="utf-8").read()
    return json.loads(s[s.index(f"window.{var} = ") + len(f"window.{var} = "):].strip().rstrip(";"))


def centroid(ring):
    P = np.asarray(ring, float); x, y = P[:, 0], P[:, 1]; x1, y1 = np.roll(x, -1), np.roll(y, -1)
    cr = x * y1 - x1 * y; A = cr.sum() / 2
    if abs(A) < 1e3: return P.mean(axis=0)
    return np.array([((x + x1) * cr).sum() / (6 * A), ((y + y1) * cr).sum() / (6 * A)])


def inring(p, ring):
    c = False
    for i in range(len(ring)):
        (x1, y1), (x2, y2) = ring[i], ring[i - 1]
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < (x2 - x1) * (p[1] - y1) / (y2 - y1) + x1: c = not c
    return c


def spaces():
    """the plan's spaces: (type, name, rings, middle, area m2, box), smallest first (a room inside a workhall is found first)"""
    out = []
    for q in js("plan-dxf.js", "PLAN_DXF")["spaces"]:
        rings = [[tuple(map(float, p.strip().split())) for p in m[1:].rstrip("Z").split("L")] for m in re.findall(r"M[^MZ]+Z?", q["d"])]
        R = np.concatenate([np.asarray(r) for r in rings])
        out.append((q["type"], q["name"], rings, np.array([q["x"], q["y"]], float), float(q["m2"]), (*R.min(axis=0), *R.max(axis=0))))
    return sorted(out, key=lambda s: s[4])


def main():
    os.makedirs(WORK, exist_ok=True)
    A = js("axo-dxf.js", "AXO_DXF"); z = np.load(os.path.join(ROOT, "tools", "_work", "axo-skp", "route.npz"))
    layers = {k: z[k] for k in ("wall", "furn", "plant", "grass", "corridor")}
    wk = axo_skp.Walker(layers, z["lo"], float(z["res"]), float(z["CX"]), float(z["CY"]))
    rng = np.random.default_rng(27)

    # the layout's chairs and desks, in plan mm
    chairs, desks = [], []
    def put(k, r):
        if k == "chair": chairs.append(np.asarray(r, float))
        elif k == "desk": desks.append(np.asarray(r, float))
    for u in A["uses"]:
        bid, a, b, c, d, e, f = u
        for k, r in A["blocks"].get(bid, []): put(k, [[a * x + c * y + e, b * x + d * y + f] for x, y in r])
    for k, r in A["loose"]: put(k, r)
    # desk edges every 50 mm, for the nearest table a seat faces
    edge = []
    for r in desks:
        for i in range(len(r)):
            p, q = r[i - 1], r[i]; n = max(1, int(np.linalg.norm(q - p) / 50))
            edge.append(p + (q - p) * np.linspace(0, 1, n + 1)[:, None])
    edge = np.concatenate(edge)
    from scipy.spatial import cKDTree
    tree = cKDTree(edge)

    # the fine shift onto the SketchUp model's walls
    shift, after, before = wayday_marks.refine([r for w in A["walls"] for r in w], (0.0, 0.0), z)      # each wall: its rings
    print(f"onto the SketchUp walls: shift {shift.round(0).tolist()} mm, walls within 10 cm {before:.0%} -> {after:.0%}")

    reg = js("axo-skp.js", "AXO_SKP")["registration"]; RA, RS = np.array(reg["A"], float), np.array(reg["shift_m"], float)
    skp = lambda q: 1000 * (RA @ np.asarray(q, float) + RS)           # SketchUp metres -> plan mm, on the model
    SP = spaces()
    def space_of(p):
        return next((s for s in SP if s[5][0] <= p[0] <= s[5][2] and s[5][1] <= p[1] <= s[5][3] and sum(inring(p, r) for r in s[2]) % 2), None)

    seats = []                                                        # (x, y, angle, space)
    for r in chairs:
        p = centroid(r); sp = space_of(p)
        if sp and sp[0] in ("Not in contract", "Washroom", "Server, UPS & battery"): continue
        dist, i = tree.query(p, distance_upper_bound=1200)
        tgt = edge[i] if np.isfinite(dist) else (sp[3] if sp else None)
        a = math.atan2(tgt[1] - p[1], tgt[0] - p[0]) if tgt is not None else rng.uniform(-math.pi, math.pi)
        seats.append((p, a, sp))
    print(f"{len(chairs)} chairs, {len(desks)} desks; {len(seats)} seats in spaces we people")

    def free_mm(p, grass=False):
        """a plan-mm point a person can stand on (the walking grid, shifted onto the model): clear of walls, furniture and
        plants; on the terraces' grass too if asked"""
        rc = wk.cell(wk.to_w(p + shift))
        if grass: return wk.inside(rc) and not (wk.block[rc] or wk.furn[rc] or wk.plant[rc])
        return wk.free(rc)
    def free_near(c, r0, r1, tries=60):
        for _ in range(tries):
            t, rr = rng.uniform(0, 2 * math.pi), rng.uniform(r0, r1)
            p = c + np.array([math.cos(t), math.sin(t)]) * rr
            if free_mm(p): return p
        return None

    P = {"sit": [], "stand": [], "present": [], "yoga": []}
    gs = space_of(skp(GARDEN["swing"]) - shift); garden = gs[1] if gs else None
    print("the Acker Garden is in:", gs[0] if gs else "-", garden)
    add = lambda k, p, a: P[k].append([int(round(p[0] + shift[0])), int(round(p[1] + shift[1])), int(round(a * 100))])

    # rooms in session (and which are not)
    by_space = {}
    for p, a, sp in seats: by_space.setdefault(sp[1] if sp else None, []).append((p, a, sp))
    session = {}
    for name, ss in by_space.items():
        sp = ss[0][2]; t = sp[0] if sp else None
        if t in ROOMS: session[name] = name in IN_SESSION or (t == "Training room") or rng.random() < 0.5
    for name, ss in by_space.items():
        sp = ss[0][2]; t = sp[0] if sp else None
        if name == garden: continue                                   # the drawing's chairs are not the garden's: below
        if t in ROOMS: p_take = 0.9 if session[name] else 0.0
        elif t == "Workhall": p_take = 0.6
        elif t == "Cafeteria": p_take = 0.45
        elif t == "Collab": p_take = 0.7
        elif t in ("Phone booth", "Reception", "Hub room", "Studio", "Coffee corner"): p_take = 0.5
        elif t == "Executive corner cabin": p_take = 0.0                 # one, below
        elif t in ("Nap room", "Prayer room", "Medical room", "Mother's room", "Zen room", "Mail room", "Lift lobby", "Entry"): p_take = 0.0
        else: p_take = 0.3
        for p, a, _ in ss:
            if rng.random() < p_take: add("sit", p, a)
        if t == "Executive corner cabin" and ss:
            p, a, _ = min(ss, key=lambda s: tree.query(s[0])[0]); add("sit", p, a)
        # a presenter at one end of a room in session, facing its middle
        if t in ROOMS and session[name] and sp[4] > 12 and len(ss) >= 4:
            R = np.array([q[0] for q in ss]); m = R.mean(axis=0); w, v = np.linalg.eigh(np.cov((R - m).T)); ax = v[:, 1]
            sg = 1 if rng.random() < 0.5 else -1; end = m + ax * sg * (((R - m) @ ax * sg).max() + 900)
            q = end if free_mm(end) else free_near(end, 200, 900)
            if q is not None: add("present", q, math.atan2(m[1] - q[1], m[0] - q[0]))

    # the spaces' own scenes
    for t, name, rings, m, area, _box in SP:
        if t == "Reception":                                          # visitors at the reception desk
            ds = [r for r in desks if inring(centroid(r), rings[0])]
            if ds:
                dsk = max(ds, key=lambda r: np.ptp(r[:, 0]) * np.ptp(r[:, 1])); c = centroid(dsk)
                for _ in range(int(rng.integers(3, 5))):
                    q = free_near(c, 1300, 2600)
                    if q is not None: add("stand", q, math.atan2(c[1] - q[1], c[0] - q[0]))
        elif t == "Collab" and area > 10 and name != garden:          # a standing huddle where there is room for one
            best = None
            for _ in range(150):
                c = m + rng.normal(0, 1, 2) * math.sqrt(area) * 200
                if not (any(inring(c, r) for r in rings) and free_mm(c)): continue
                ok = []
                for _ in range(60):                                       # up to five round it, 0.6-1.1 m out, apart
                    t1, r1 = rng.uniform(0, 2 * math.pi), rng.uniform(600, 1100); q = c + np.array([math.cos(t1), math.sin(t1)]) * r1
                    if free_mm(q) and all(np.linalg.norm(q - o) > 550 for o in ok): ok.append(q)
                    if len(ok) == 5: break
                if best is None or len(ok) > len(best[1]): best = (c, ok)
                if len(ok) == 5: break
            if best and len(best[1]) >= 3:
                for q in best[1]: add("stand", q, math.atan2(best[0][1] - q[1], best[0][0] - q[0]))
        elif t == "Zen room":                                         # one on the floor
            c = m if free_mm(m) else free_near(m, 200, 1200)
            if c is not None: add("yoga", c, rng.uniform(-math.pi, math.pi))
        elif t in ("Terrace", "Cafeteria", "Workhall"):               # pairs talking
            g = t == "Terrace"
            n = (int(rng.integers(3, 6)) if area > 50 else 1) if g else 6 if t == "Cafeteria" else int(area // 60)
            for _ in range(n):
                c = None
                for _ in range(120):
                    q = m + rng.normal(0, 1, 2) * math.sqrt(area) * 250
                    if any(inring(q, r) for r in rings) and free_mm(q, g): c = q; break
                if c is None: continue
                t1 = rng.uniform(0, 2 * math.pi); off = np.array([math.cos(t1), math.sin(t1)]) * 400
                for q, a in ((c - off, t1), (c + off, t1 + math.pi)):
                    if free_mm(q, g): add("stand", q, a)
        elif t == "Lift lobby":                                       # waiting for a lift
            for _ in range(int(rng.integers(2, 4))):
                q = free_near(m, 500, 3500)
                if q is not None: add("stand", q, rng.uniform(-math.pi, math.pi))
        elif t == "Coffee corner" and rng.random() < 0.6:
            q = free_near(m, 200, 1200)
            if q is not None: add("stand", q, rng.uniform(-math.pi, math.pi))

    # the Acker Garden: in the swing, in the two chairs over the chess, on the pouf, at the punching bag, at the foosball; on the
    # deck (a 4th value: what they sit or stand on, mm)
    props = {}
    if garden:
        G = {k: (skp(v) if isinstance(v, tuple) else [skp(q) for q in v]) for k, v in GARDEN.items()}
        face = lambda p, q: math.atan2(q[1] - p[1], q[0] - p[0])
        put = lambda k, p, a, h: P[k].append([int(round(p[0])), int(round(p[1])), int(round(a * 100)), int(h)])
        put("sit", G["swing"], face(G["swing"], G["inside"]), 150)
        for c in G["chairs"]: put("sit", c, face(c, G["chess"]), 30)
        put("sit", G["pouf"], face(G["pouf"], G["chess"]), DECK)
        d = G["inside"] - G["bag"]; q = G["bag"] + d / np.linalg.norm(d) * 650; put("present", q, face(q, G["bag"]), DECK)
        f = G["foosball"]; ax = skp(np.array(GARDEN["foosball"]) + [0.0, 1.0]) - f; ax /= np.linalg.norm(ax); nx = np.array([-ax[1], ax[0]])
        for sg in (-1, 1): q = f + nx * sg * 750; put("stand", q, face(q, f), DECK)
        props["foosball"] = [int(round(f[0])), int(round(f[1])), int(round(math.atan2(ax[1], ax[0]) * 100)), DECK]

    # walkers: corridor to corridor, 10-25 m, there and back
    corr = np.argwhere(wk.corr & ~wk.block & ~wk.furn)
    walks = []
    for _ in range(400):
        if len(walks) >= 40: break
        a = wk.world(corr[rng.integers(len(corr))]); b = wk.world(corr[rng.integers(len(corr))])
        L = float(np.linalg.norm(b - a))
        if not 10 < L < 25: continue
        ra, rb = wk.cell(a), wk.cell(b); m_ = int(5 / wk.g)
        box = (max(0, min(ra[0], rb[0]) - m_), max(0, min(ra[1], rb[1]) - m_), min(wk.H, max(ra[0], rb[0]) + m_), min(wk.W, max(ra[1], rb[1]) + m_))
        path = wk.astar(a, b, box, door=0.0)
        if not path: continue
        plen = sum(float(np.linalg.norm(path[i] - path[i - 1])) for i in range(1, len(path)))
        if plen > 1.6 * L: continue
        walks.append([[int(round(v)) for v in wk.to_mm(q)] for q in path])
    out = dict(P, walk=walks, props=props)
    print("people:", {k: len(v) for k, v in out.items()}, "walking", sum(len(w) for w in walks), "points")

    # the slide's generated line
    s = open(SLIDE, encoding="utf-8").read()
    line = "  const PEOPLE = " + json.dumps(out, separators=(",", ":")) + ";\n"
    s2, n = re.subn(r"^  const PEOPLE = .*;\n", lambda _: line, s, count=1, flags=re.M)
    if not n: sys.exit("no `const PEOPLE = ...;` line in slides/s-wayday.html")
    open(SLIDE, "w", encoding="utf-8", newline="").write(s2)
    print("wrote PEOPLE in slides/s-wayday.html", f"({len(line) / 1000:.0f} kB)")

    # to check: the west wing, 25 px/m: walls, furniture, chairs; seated blue (a tick for the facing), standing green,
    # presenters red, yoga purple, walkers orange
    x0, x1, y0, y1, k = 8000, 116000, 8000, 52000, 0.025
    im = Image.new("RGB", (int((x1 - x0) * k), int((y1 - y0) * k)), "white"); dr = ImageDraw.Draw(im)
    W = lambda p: ((p[0] - x0) * k, (p[1] - y0) * k)
    rr, cc = np.nonzero(wk.wall | wk.furn)
    for r_, c_ in zip(rr[::3], cc[::3]):
        q = wk.to_mm(wk.world((r_, c_))); col = (90, 90, 90) if wk.wall[r_, c_] else (215, 205, 190)
        if x0 < q[0] < x1 and y0 < q[1] < y1: dr.point(W(np.array(q) - shift), fill=col)
    for r in chairs: dr.polygon([W(q) for q in r], outline=(150, 150, 170))
    for kk, col in (("sit", (40, 90, 220)), ("stand", (30, 160, 60)), ("present", (220, 30, 30)), ("yoga", (140, 40, 200))):
        for x, y, a, *_ in out[kk]:
            p = np.array([x, y], float) - shift; q = W(p); dr.ellipse([q[0] - 4, q[1] - 4, q[0] + 4, q[1] + 4], fill=col)
            dr.line([q, W(p + np.array([math.cos(a / 100), math.sin(a / 100)]) * 450)], fill=col, width=2)
    for w in walks: dr.line([W(np.array(q, float) - shift) for q in w], fill=(240, 140, 0), width=2)
    im.save(os.path.join(WORK, "people.png")); print("check:", os.path.join(WORK, "people.png"))


if __name__ == "__main__":
    main()
