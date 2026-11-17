"""The Loop on the real floor: one ordered path through the seven stops, in the Loop slide's order, on the employees' route.

From data/axo-layers.js (AXO_LAYERS.routes.employee: 19 branching runs of [x, y, d], AXO frame, plan mm y down; AXO_LAYERS.stops)
to data/loop-path.js (window.ACKO_LOOP), in the deck plan's frame (PLAN_DXF: x + 185842, y - 182802):
  sweep  [[x, y], ...]  the same route west to east through the stops as they lie (for the ribbon's morph), sweepStops
  path   [[x, y], ...]  the walk, Arrival → Café → Board Room → Meeting Rooms → Collab → Work → Wellness, shortest legs on the route
  stops  [{name, i, x, y}]  each stop and its index on path
  nodes  [[x, y], ...], edges [[a, b], ...]  the route as a graph (the people's ways to their desks)
  entries [[x, y], [x, y]]
  ring   [[x, y], ...]  the Loop as ONE closed route (16 Nov concept note): the main street out and back, round the meeting island at
         each end; ringKind (each point's stretch), ringDash (the lane 02A has yet to open), ringStops (both arrivals, the seven stops)
usage: python tools/acko/loop_path.py            (from the checkout's root)
"""
import heapq, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DX, DY = 185842, -182802                       # AXO_LAYERS → PLAN_DXF (checked on the six zone rings and PLAN_BASE.origin)
ORDER = ["Arrival", "Café", "Board Room", "Meeting Rooms", "Collab", "Work", "Wellness"]
JOIN = 1500                                     # mm: points of different runs this close meet (the runs branch off one another)

s = open(os.path.join(ROOT, "data", "axo-layers.js"), encoding="utf-8").read()
A = json.loads(s[s.index("{"): s.rindex("}") + 1])
runs = A["routes"]["employee"]

nodes, edges = [], set()
for run in runs:
    prev = None
    for x, y, _d in run:
        nodes.append((x + DX, y + DY))
        k = len(nodes) - 1
        if prev is not None: edges.add((prev, k))
        prev = k
dist = lambda a, b: math.hypot(nodes[a][0] - nodes[b][0], nodes[a][1] - nodes[b][1])
# where the runs meet: each point joins the nearest point of every other run within JOIN
run_of = []
for ri, run in enumerate(runs): run_of += [ri] * len(run)
for a in range(len(nodes)):
    best = {}
    for b in range(len(nodes)):
        if run_of[a] == run_of[b]: continue
        d = dist(a, b)
        if d <= JOIN and d < best.get(run_of[b], (1e18,))[0]: best[run_of[b]] = (d, b)
    for _d, b in best.values(): edges.add((min(a, b), max(a, b)))
adj = {i: [] for i in range(len(nodes))}
for a, b in edges: adj[a].append(b); adj[b].append(a)

# one piece? join any stray piece to its nearest point elsewhere
def comps():
    seen, out = set(), []
    for i in range(len(nodes)):
        if i in seen: continue
        st, c = [i], []
        seen.add(i)
        while st:
            u = st.pop(); c.append(u)
            for v in adj[u]:
                if v not in seen: seen.add(v); st.append(v)
        out.append(c)
    return out
cs = comps()
while len(cs) > 1:
    cs.sort(key=len)
    small, rest = cs[0], [i for c in cs[1:] for i in c]
    a, b = min(((a, b) for a in small for b in rest), key=lambda p: dist(*p))
    print("joining a stray piece of %d points (%.1f m)" % (len(small), dist(a, b) / 1000))
    edges.add((min(a, b), max(a, b))); adj[a].append(b); adj[b].append(a)
    cs = comps()

def dijkstra(src):
    D, P, q = {src: 0}, {src: None}, [(0, src)]
    while q:
        d, u = heapq.heappop(q)
        if d > D[u]: continue
        for v in adj[u]:
            nd = d + dist(u, v)
            if nd < D.get(v, 1e18): D[v] = nd; P[v] = u; heapq.heappush(q, (nd, v))
    return D, P
near = lambda x, y: min(range(len(nodes)), key=lambda i: math.hypot(nodes[i][0] - x, nodes[i][1] - y))
stops = {st["name"]: st for st in A["stops"]}
def walk(names):
    seq = [near(stops[n]["x"] + DX, stops[n]["y"] + DY) for n in names]
    path, idx = [seq[0]], [0]
    for a, b in zip(seq, seq[1:]):
        _D, P = dijkstra(a)
        leg, u = [], b
        while u is not None: leg.append(u); u = P[u]
        leg.reverse()
        path += leg[1:]; idx.append(len(path) - 1)
    return seq, path, idx
seq, path, idx = walk(ORDER)
pts = [nodes[i] for i in path]
# the sweep: the same route west to east through the stops in the order they lie (the Loop ribbon's left to right, on the floor)
WE = sorted(ORDER, key=lambda n: stops[n]["x"])
_s, spath, sidx = walk(WE)
spts = [nodes[i] for i in spath]
L = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))

# ---- the ring (16 Nov concept note: "a path with two ends is a corridor with dead ends"): the Loop as ONE closed route. The middle
# of the floor is too narrow for two lanes, so it runs as a main street both lift lobbies open onto, out and back (a drawing offsets
# the two directions to either side), then rings the meeting island at each end and comes back. Legs are either the people's route
# (graph, as above) or open floor traced off the plan (straight, metres). Clockwise on the plan (y down): out east on the street,
# round the east island, back west, round the west island (and out to the Acker Garden on the west tip's deck), east again.
# The strip between the west island's north-east rooms and the huddle rooms (x ≈ 52.4–53.9 m) has no lane in 02A yet: it is the
# one dashed stretch ("02A tweak: open a lane round the meeting island to close the ring").
LOBBY = [(81478, 30607), (172028, 30607)]
def graph_leg(p, q):
    a, b = near(*p), near(*q)
    _D, P = dijkstra(a)
    leg, u = [], b
    while u is not None: leg.append(nodes[u]); u = P[u]
    return leg[::-1]
M = lambda *xy: [(x * 1000, y * 1000) for x, y in xy]
def cap(c, r, start, cw=True, n=14):
    """a small turn round the point c (metres): from the angle nearest `start`, a full circle, so a spur can come back"""
    a0 = math.atan2(start[1] - c[1] * 1000, start[0] - c[0] * 1000)
    s = 1 if cw else -1
    return [(c[0] * 1000 + r * 1000 * math.cos(a0 + s * 2 * math.pi * k / n), c[1] * 1000 + r * 1000 * math.sin(a0 + s * 2 * math.pi * k / n)) for k in range(n + 1)]
S, E = (53.0, 31.0), (224.6, 42.1)                 # the street's west end (where it meets the west island) and its east end
LEGS = [  # (kind, points), in order round the ring
    ("street", M(S, (60.0, 31.1), (67.6, 31.1), (75.0, 31.0)) + graph_leg((78500, 30800), LOBBY[0])),   # past the café's door to Arrival 1
    ("street", graph_leg(LOBBY[0], (stops["Board Room"]["x"] + DX, stops["Board Room"]["y"] + DY))),
    ("street", graph_leg((stops["Board Room"]["x"] + DX, stops["Board Room"]["y"] + DY), (stops["Meeting Rooms"]["x"] + DX, stops["Meeting Rooms"]["y"] + DY))),
    ("street", graph_leg((stops["Meeting Rooms"]["x"] + DX, stops["Meeting Rooms"]["y"] + DY), LOBBY[1])),
    ("street", graph_leg(LOBBY[1], (E[0] * 1000, E[1] * 1000))),
    # the east island (neighbourhood 01): up its west side and north-west lane, round its north-east end, back along its south side
    # (the traced route cuts across the island's rooms here; the ring keeps to the corridor: up the west band, into the north-west lane)
    ("east", M((225.9, 41.5), (225.9, 35.0), (226.5, 32.6), (227.9, 30.1), (229.9, 28.4), (231.9, 26.8)) + graph_leg((233000, 25500), (247900, 29600))),
    ("east", M((247.1, 30.9), (245.0, 31.45), (241.3, 31.45), (238.0, 33.6), (235.2, 35.9), (232.4, 38.2), (230.2, 40.2), (228.6, 41.9), (226.2, 42.2))),
    ("back", None),                                  # the street, west again (the "street" legs reversed)
    # the west island (neighbourhood 06): along its south-east face, up its south-west end, out to the Acker Garden and back, along its
    # north-west lane past Wellness, then the strip down to the street (dashed)
    ("west", M(S, (49.5, 31.0), (46.1, 30.8), (43.8, 32.2), (40.8, 34.2))),   # hugging the island's face, clear of the workhall's corner
    ("west", graph_leg((40000, 34700), (35400, 29500)) + M((34.0, 29.2), (32.6, 29.4), (32.0, 28.0), (31.8, 26.0), (31.8, 24.0))),
    ("garden", graph_leg((31800, 24000), (18400, 17700))),
    ("west", graph_leg((31800, 24000), (52500, 18300))),
    ("dash", M((53.1, 18.9), (53.15, 24.0), (53.15, 28.5), S)),
]
ring, kinds = [], []
def add(ps, kind):
    for x, y in ps:
        if ring and math.hypot(ring[-1][0] - x, ring[-1][1] - y) < 200: continue   # the joins between legs
        ring.append((x, y)); kinds.append(kind)
street = []
for kind, ps in LEGS:
    if kind == "street": street += ps; add(ps, kind)
    elif kind == "back": add(street[::-1], kind)
    elif kind == "garden":
        add(ps, kind); add(cap((18.4, 18.3), 1.6, ps[-1]), kind); add(ps[::-1], kind)
    else: add(ps, kind)
if math.hypot(ring[-1][0] - ring[0][0], ring[-1][1] - ring[0][1]) < 200: ring.pop(); kinds.pop()   # closed: the last point is the first
# the dashed stretch, as index ranges [from, to] (its own points, and the step into the first of them)
dash, k = [], 0
while k < len(ring):
    if kinds[k] == "dash":
        j = k
        while j + 1 < len(ring) and kinds[j + 1] == "dash": j += 1
        dash.append([max(k - 1, 0), j + 1 if j + 1 < len(ring) else 0]); k = j + 1
    else: k += 1
nearest = lambda x, y, only=None: min((i for i in range(len(ring)) if only is None or kinds[i] in only), key=lambda i: math.hypot(ring[i][0] - x, ring[i][1] - y))
RSTOPS = [{"name": "Arrival 1", "kind": "arrival", "i": nearest(*LOBBY[0], only=("street",))},
          {"name": "Arrival 2", "kind": "arrival", "i": nearest(*LOBBY[1], only=("street",))}]
for n in ORDER:                                     # the seven stops, each on its own stretch of the ring (the street's outward lane)
    x, y = stops[n]["x"] + DX, stops[n]["y"] + DY
    only = {"Collab": ("garden",), "Wellness": ("west",), "Work": ("east",)}.get(n, ("street",))
    RSTOPS.append({"name": n, "kind": "stop", "i": nearest(x, y, only)})
RL = sum(math.hypot(ring[(i + 1) % len(ring)][0] - ring[i][0], ring[(i + 1) % len(ring)][1] - ring[i][1]) for i in range(len(ring)))
out = {
    "about": "the Loop on the floor: the employees' route walked through the seven stops in the Loop slide's order; PLAN_DXF mm, y down (tools/acko/loop_path.py)",
    "length": round(L / 1000, 1),
    "path": [[round(x), round(y)] for x, y in pts],
    "stops": [{"name": n, "i": i, "x": round(nodes[seq[k]][0]), "y": round(nodes[seq[k]][1])} for k, (n, i) in enumerate(zip(ORDER, idx))],
    "sweep": [[round(x), round(y)] for x, y in spts],
    "sweepStops": [{"name": n, "i": i} for n, i in zip(WE, sidx)],
    "nodes": [[round(x), round(y)] for x, y in nodes],
    "edges": sorted([list(e) for e in edges]),
    "entries": [[round(x + DX), round(y + DY)] for x, y in A["entries"]],
    # the closed Loop (16 Nov concept note): ring is closed (the last point joins the first); ringKind names each point's stretch
    # (street = the main street eastward, back = westward, east / west = round the islands, garden = out to the Acker Garden and back,
    # dash = the lane 02A still has to open); ringDash the dashed index ranges; ringStops both arrivals and the seven stops on it
    "ring": [[round(x), round(y)] for x, y in ring],
    "ringKind": kinds,
    "ringDash": dash,
    "ringStops": RSTOPS,
    "ringLength": round(RL / 1000, 1),
}
open(os.path.join(ROOT, "data", "loop-path.js"), "w", encoding="utf-8", newline="\n").write(
    "/* " + out["about"] + " */\nwindow.ACKO_LOOP = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
print("ring %d points, %.1f m, dashed %s, stops %s" % (len(ring), RL / 1000, dash, [(q["name"], q["i"]) for q in RSTOPS]))
print("sweep %d points; " % len(spts) + "path %d points, %.1f m; stops at %s; %d nodes, %d edges" % (len(pts), L / 1000, idx, len(nodes), len(edges)))
