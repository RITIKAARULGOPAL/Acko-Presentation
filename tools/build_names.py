"""The rooms' names as the 09.10 drawings write them: every TEXT / MTEXT on the plan, with its lines, height, rotation and
anchor, in plan mm (the same frame as data/plan-data.js: DXF minus its origin_dxf). Writes data/plan-names.js (window.MX_NAMES).

usage: python tools/build_names.py
"""
import os, sys, json, math, re
import ezdxf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dxf_to_json import explode, group_of, BIG_BLOCK, SHELL_BLOCKS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = {"opt1": "Testfit OP1 - 09.10.26.dxf", "opt2": "Test Fit op2 09.10.2026.dxf", "opt3": "Testfit -14.10.26 combined.dxf"}
txt = open(os.path.join(ROOT, "data", "plan-data.js"), encoding="utf-8").read()
D = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
CAP = 1.39   # DXF text height is the capitals' height; a font's size is ~1.39 x that (Arial)
SKIP = re.compile(r"^(TV|ACD|IT TABLE.*|3'X5'|2000W|2x16A|LAMP)$", re.I)
TEAM = re.compile(r"^(DELIVERY|PRODUCT|SALES|SALES CALLING|HR, FINANCE)\b.*PAX", re.I)


def place(lines, x, y, h, rot, col, row, box_w=0, para=None):
    """each line's baseline point in plan mm, from the block's anchor: col 0/1/2 left/centre/right, row top/mid/bot/base"""
    lh = h * 5 / 3; n = len(lines); blk = h + (n - 1) * lh
    c, s_ = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    # horizontal: a box (MTEXT width) aligns its lines by the paragraph; else the anchor's own column
    if box_w:
        left = -col * box_w / 2
        p = {"l": 0, "c": 1, "r": 2}.get(para, col)
        u, anc = left + p * box_w / 2, ("start", "middle", "end")[p]
    else:
        u, anc = 0, ("start", "middle", "end")[col]
    top = {"top": 0, "mid": blk / 2, "bot": blk, "base": h}[row]   # the block's top, above the anchor
    out = []
    for i, ln in enumerate(lines):
        v = top - h - i * lh
        out.append([ln, round(x + u * c - v * s_), round(y + u * s_ + v * c)])
    return out, anc


out = {}
for o, f in SRC.items():
    doc = ezdxf.readfile(os.path.join(os.path.dirname(ROOT), f))
    X0, Y0 = D[o]["origin_dxf"]; W, H = D[o]["size"]
    big = {b.name for b in doc.blocks if len(b) > BIG_BLOCK and b.name not in SHELL_BLOCKS}
    seen, rows = [], []
    for top in doc.modelspace():
        tb = top.dxf.name if top.dxftype() == "INSERT" else None
        for e, layer, topb, pinst in explode(top, None, tb, None):
            L = doc.layers.get(layer) if doc.layers.has_entry(layer) else None
            if L is not None and (L.is_off() or L.is_frozen()):
                continue
            if group_of(layer, topb, pinst, big) == "anno" and "ANNO" not in layer.upper():
                continue                                             # block attributes and the like (as dxf_to_json)
            t = e.dxftype()
            if t == "MTEXT":
                lines = [" ".join(q.split()) for q in e.plain_text(split=True) if q.strip()]
                if not lines:
                    continue
                h, rot = e.dxf.char_height, e.get_rotation()
                ap = e.dxf.get("attachment_point", 1); col, row = (ap - 1) % 3, ("top", "mid", "bot")[(ap - 1) // 3]
                m = re.search(r"\\p[^;]*q([lcrjd])", e.text)
                para = m.group(1) if m and m.group(1) in "lcr" else None
                ins = e.dxf.insert; x, y = ins.x - X0, ins.y - Y0
                lns, anc = place(lines, x, y, h, rot, col, row, e.dxf.get("width", 0) or 0, para)
            elif t in ("TEXT", "ATTRIB"):
                q = " ".join(e.dxf.text.split())
                if not q:
                    continue
                h, rot = e.dxf.height, e.dxf.get("rotation", 0)
                ha, va = e.dxf.get("halign", 0), e.dxf.get("valign", 0)
                ins = e.dxf.align_point if (ha or va) and e.dxf.hasattr("align_point") else e.dxf.insert
                col = {0: 0, 1: 1, 2: 2, 4: 1}.get(ha, 0); row = "mid" if ha == 4 else {0: "base", 1: "base", 2: "mid", 3: "top"}.get(va, "base")
                x, y = ins.x - X0, ins.y - Y0
                lines = [q]; lns, anc = place(lines, x, y, h, rot, col, row)
            else:
                continue
            if not (0 <= x <= W and 0 <= y <= H) or SKIP.match(" ".join(lines)):
                continue
            # the same text twice within 0.5 m (the drawing has duplicates, e.g. Option 01's BREAKOUT AREA, 0.44 m apart; real neighbours, rooms or a word's letters, sit further apart): kept once
            key = "|".join(lines)
            if len(key) > 1 and any(k == key and math.hypot(x - sx, y - sy) < 500 for k, sx, sy in seen):
                print("  duplicate", o, key, round(x), round(y)); continue
            seen.append((key, x, y))
            rows.append({"l": lns, "f": round(h * CAP), "r": round(rot % 360, 1), "a": anc, "k": "team" if TEAM.match(" ".join(lines)) else ""})
    if o == "opt2":
        # Option 02's drawing writes its rooms smaller (168 / 153 mm capitals against Option 01's 200): matched to Option 01,
        # its notes in proportion; the teams' and the core's labels already match (Sathwick, 13.10)
        for r in rows:
            if r["k"] or r["f"] >= 278:
                continue
            r["f"] = 278 if 200 <= r["f"] <= 240 else round(r["f"] * 278 / 233)
    out[o] = rows
    print(o, len(rows), "texts", sum(1 for r in rows if r["k"]), "team")
with open(os.path.join(ROOT, "data", "plan-names.js"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("/* the drawings' texts with their lines, height, rotation and anchor -- generated by tools/build_names.py, don't hand-edit */\n")
    fh.write("window.MX_NAMES=" + json.dumps(out, separators=(",", ":"), ensure_ascii=False) + ";\n")
