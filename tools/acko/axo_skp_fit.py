"""The axo debug page's model into A day in ACKO (Ritika: "now the axo model is updated in tis branch.. bring in the model
changes.. retain the style as it is here").
Usage:  python -I tools/acko/axo_skp_fit.py   (after tools/acko/axo_skp_28.py and tools/acko/axo_debug.py)
Reads tools/_work/axo-debug/debug.json (axo_debug.py) and Ritika's calls on its segments (tools/acko/axo-debug-calls.json), and
writes "fit" into data/axo-skp.js's "changes":
  shift   the floor plan onto the model (plan mm), as the page walks data/plan-base.js
  pieces  every piece the page draws (not the ones rebuild leaves out), each as the page draws it: [type, height (m), rings (plan
          mm, y down: its outline, then its holes)], a phone booth with its component and placement [.., unit, 12 floats];
          type is the call on it, else a door the plan draws in it, else its own: wall, solid, glass, door, column, facade,
          rail, booth
  place   the plan's furniture the model hasn't (its workstations and plants: axo_debug.missing_from_plan), as changes.place
assets/js/axo-skp.js draws them in the slide's own materials, in place of the model's walls, glass and façade."""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    D = json.load(open(os.path.join(ROOT, "tools", "_work", "axo-debug", "debug.json")))
    calls = json.load(open(os.path.join(ROOT, "tools", "acko", "axo-debug-calls.json"), encoding="utf-8"))
    pieces, n = [], {}
    for pc in D["pieces"]:
        if pc.get("cut"): continue
        ty = calls.get(pc["key"]) or ("door" if pc.get("door") else pc["ty"])           # (the page's eff())
        q = [ty, pc["h"], pc["rings"]]
        if ty == "booth": q += [pc["unit"][0], pc["m"]]
        pieces.append(q); n[ty] = n.get(ty, 0) + 1
    fit = {"shift": D["shift"], "pieces": pieces, "place": D["add_place"]}
    path = os.path.join(ROOT, "data", "axo-skp.js")
    s = open(path, encoding="utf-8").read(); body = s.rstrip().rstrip(";")
    cut = body.rfind(',"changes":'); assert cut > 0 and body.endswith("}}")
    chg = json.loads(body[cut + len(',"changes":'):-1])
    chg["fit"] = fit
    s2 = body[:cut] + ',"changes":' + json.dumps(chg, separators=(",", ":")) + "};\n"
    open(path, "w", encoding="utf-8", newline="\n").write(s2)
    print(f"{len(pieces)} pieces {dict(sorted(n.items()))}, {len(fit['place'])} placements; data/axo-skp.js {len(s2) / 1e6:.2f} MB")


if __name__ == "__main__": main()
