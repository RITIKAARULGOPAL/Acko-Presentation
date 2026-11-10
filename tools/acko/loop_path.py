"""The Loop on the real floor: one ordered path through the seven stops, in the Loop slide's order, on the employees' route.

From data/axo-layers.js (AXO_LAYERS.routes.employee: 19 branching runs of [x, y, d], AXO frame, plan mm y down; AXO_LAYERS.stops)
to data/loop-path.js (window.ACKO_LOOP), in the deck plan's frame (PLAN_DXF: x + 185842, y - 182802):
  sweep  [[x, y], ...]  the same route west to east through the stops as they lie (for the ribbon's morph), sweepStops
  path   [[x, y], ...]  the walk, Arrival → Café → Board Room → Meeting Rooms → Collab → Work → Wellness, shortest legs on the route
  stops  [{name, i, x, y}]  each stop and its index on path
  nodes  [[x, y], ...], edges [[a, b], ...]  the route as a graph (the people's ways to their desks)
  entries [[x, y], [x, y]]
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
}
open(os.path.join(ROOT, "data", "loop-path.js"), "w", encoding="utf-8", newline="\n").write(
    "/* " + out["about"] + " */\nwindow.ACKO_LOOP = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
print("sweep %d points; " % len(spts) + "path %d points, %.1f m; stops at %s; %d nodes, %d edges" % (len(pts), L / 1000, idx, len(nodes), len(edges)))
