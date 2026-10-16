"""Provisional overlay data (zones, events, routes, cameras) for both options.

Traced in pixel space of the deck's colour plans (slide 22 = Opt 01, slide 24 =
Opt 02, both 1914x911 and framed identically) and converted to the CAD's local
millimetre frame produced by dxf_to_json.py (shell lower-left = 0,0; y up).

Replace with the CAD team's MX-* layers once they arrive: same JSON shape.

Usage: python author_zones.py <out.json>
"""
import sys, json, math

# image px -> local mm (fitted on the column grid + facade corners, ~0.3 m accuracy)
def P(px, py):
    return [round(7280 + 34.97 * px), round(32237 - 35.1 * (py - 45))]

def poly(*pts):
    return [P(x, y) for x, y in pts]

def rect(x0, y0, x1, y1):
    return poly((x0, y0), (x1, y0), (x1, y1), (x0, y1))

def area_m2(pts):
    a = 0
    for i in range(len(pts)):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2 / 1e6

def length_m(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)) / 1000

# programme types: label, security tier (0 building core, 1 guest, 2 team, 3 secure)
TYPES = {
    "soc":     ("SOC · Cyber Defence Command", 3),
    "secure":  ("Server · UPS · Battery", 3),
    "arrive":  ("Arrival · Reception & Lounge", 1),
    "board":   ("Boardroom", 1),
    "focus":   ("Workhall", 2),
    "meet":    ("Meeting rooms", 2),
    "collab":  ("Collaboration · Breakout", 2),
    "cafe":    ("Café · Social", 2),
    "studio":  ("Podcast / Content Studio", 2),
    "quiet":   ("Focus booths · Nap", 2),
    "service": ("Service · Store · Prep", 2),
    "core":    ("Building core", 0),
}

CORE = [rect(980, 605, 1515, 893), rect(800, 720, 980, 893), rect(1635, 720, 1815, 893)]

OPT1 = {
    "zones": [
        ("soc", [poly((440, 45), (800, 45), (800, 175), (790, 235), (765, 295), (725, 345), (670, 385), (600, 410),
                      (575, 412), (578, 440), (520, 465), (450, 483), (380, 490), (318, 470), (305, 428), (240, 385), (175, 318))]),
        ("focus", [poly((800, 150), (1495, 150), (1540, 215), (1760, 240), (1770, 385), (1545, 390), (1545, 488), (860, 488), (860, 330), (800, 300)),
                   poly((15, 470), (175, 318), (240, 385), (305, 428), (318, 470), (380, 490), (450, 483), (520, 465), (578, 440),
                        (640, 485), (795, 505), (795, 712), (265, 720))]),
        ("collab", [poly((650, 470), (700, 370), (780, 300), (855, 330), (855, 470)), rect(1092, 512, 1190, 605),
                    rect(395, 575, 445, 700), rect(1400, 50, 1495, 145), rect(1555, 265, 1745, 355)]),
        ("meet", [rect(795, 48, 1375, 145), rect(1778, 48, 1878, 388), rect(800, 512, 1085, 605), rect(1190, 512, 1405, 605),
                  rect(335, 745, 440, 890)]),
        ("board", [rect(445, 745, 750, 893)]),
        ("service", [rect(752, 780, 798, 890), rect(1815, 785, 1875, 893), rect(1375, 50, 1398, 145)]),
        ("arrive", [poly((1500, 45), (1790, 45), (1790, 195), (1730, 235), (1640, 250), (1570, 235), (1535, 200), (1505, 150))]),
        ("cafe", [poly((1555, 515), (1778, 515), (1778, 700), (1635, 712), (1635, 893), (1555, 893))]),
        ("studio", [rect(1780, 515, 1875, 690)]),
        ("quiet", [rect(815, 632, 915, 682), rect(350, 535, 380, 600), rect(1557, 318, 1583, 350), rect(918, 632, 978, 712)]),
        ("secure", [rect(1405, 512, 1505, 600), rect(1778, 390, 1875, 510)]),
        ("core", CORE),
    ],
    "events": {
        "50": dict(poly=poly((1555, 515), (1778, 515), (1778, 700), (1635, 712), (1555, 712)), where="Café",
                   how="Tables fold and nest; the dropdown screen and the pantry counter become stage and bar."),
        "100": dict(poly=poly((800, 160), (1180, 160), (1180, 488), (800, 488), (800, 700), (640, 700), (640, 485), (700, 370), (790, 240)),
                    where="North workhall + breakout", how="Mobile benches roll back to the SOC glass; the SOC wall becomes the backdrop."),
        "200": dict(poly=poly((800, 160), (1495, 160), (1540, 215), (1620, 248), (1700, 232), (1700, 330), (1545, 345), (1545, 488),
                              (800, 488), (800, 700), (640, 700), (640, 485), (700, 370), (790, 240)),
                    where="Entire north workhall", how="Furniture moves out to the storage spine; the full hall faces the SOC as a live stage."),
    },
    "walls": [],
    "routes": {
        "visitor": poly((1590, 25), (1590, 140), (1520, 165), (830, 165), (800, 230), (770, 290), (720, 350), (660, 400), (640, 480),
                        (630, 600), (625, 722), (700, 725), (735, 752)),
        "service": poly((1600, 705), (1545, 600), (1530, 495), (1300, 495)),
    },
    "cameras": {
        "reception": dict(at=P(1586, 77), dir=[0, -1]),
        "breakout": dict(at=P(675, 460), dir=[0.866, 0.5]),
        "meeting6": dict(at=P(1051, 103), dir=[-1, 0]),
        "boardroom": dict(at=P(693, 807), dir=[-1, 0]),
        "soc": dict(at=P(602, 278), dir=[-0.618, 0.786]),
    },
    "signature": {
        "arrival": P(1650, 120), "watchwall": P(720, 330), "commons": P(1660, 610), "onair": P(1825, 600), "lantern": P(300, 230),
    },
    "socGlass": poly((800, 175), (790, 235), (765, 295), (725, 345), (670, 385), (600, 410), (575, 412)),
}

OPT2 = {
    "zones": [
        ("soc", [poly((105, 558), (232, 432), (430, 345), (655, 568), (655, 893), (440, 893))]),
        ("meet", [poly((15, 470), (330, 155), (405, 255), (232, 432), (105, 555)), rect(1785, 50, 1870, 210),
                  poly((1175, 225), (1300, 150), (1370, 180), (1555, 375), (1555, 425), (1490, 490), (1420, 490), (1240, 300)),
                  rect(1065, 50, 1200, 185), poly((1140, 50), (1250, 50), (1200, 140), (1140, 140)), rect(795, 605, 978, 712)]),
        ("focus", [poly((330, 160), (440, 45), (745, 45), (745, 240), (420, 240)),
                   poly((470, 245), (1170, 245), (1400, 470), (1320, 560), (690, 560), (470, 340)),
                   poly((1530, 215), (1875, 215), (1875, 555), (1505, 555), (1560, 430), (1560, 370), (1500, 300))]),
        ("board", [rect(745, 50, 1065, 235)]),
        ("service", [rect(1065, 190, 1130, 235), rect(1230, 50, 1295, 95), rect(1815, 785, 1875, 893)]),
        ("quiet", [rect(1335, 50, 1520, 95)]),
        ("arrive", [rect(1520, 50, 1785, 200), rect(1400, 140, 1530, 230)]),
        ("cafe", [poly((1500, 585), (1875, 585), (1875, 715), (1640, 720), (1640, 893), (1500, 893))]),
        ("studio", [rect(658, 628, 752, 738)]),
        ("secure", [rect(658, 740, 752, 808), rect(658, 808, 795, 893)]),
        ("core", CORE),
    ],
    "events": {
        "50": dict(poly=rect(1500, 585, 1875, 715), where="Café",
                   how="By day a café, at four a training room: tables stack, the dropdown screen lowers."),
        "100": dict(poly=poly((1505, 380), (1875, 380), (1875, 715), (1500, 715), (1500, 555), (1560, 430)), where="Café + east workhall",
                    how="The acoustic folding wall between café and east workhall stacks away; desks are mobile."),
        "200": dict(poly=poly((330, 160), (440, 45), (745, 45), (745, 245), (1170, 245), (1400, 470), (1320, 560), (690, 560), (470, 340), (420, 240)),
                    where="Central network hall + NW workhall", how="The central 'network' hall opens end to end; the SOC display wall is the stage."),
    },
    "walls": [poly((1505, 570), (1875, 570))],
    "routes": {
        "visitor": poly((1590, 25), (1590, 150), (1480, 215), (1300, 240), (1100, 245), (1050, 232)),
        "tour": poly((1100, 245), (700, 250), (520, 330), (640, 500), (680, 560)),
        "service": poly((1600, 650), (1450, 580), (1200, 560)),
    },
    "cameras": {},
    "signature": {
        "arrival": P(1650, 120), "watchwall": P(540, 450), "commons": P(1690, 650), "onair": P(705, 680), "lantern": P(300, 760),
    },
    "socGlass": poly((430, 345), (655, 568)),
}

ANNOT = {
    "outline": poly((15, 470), (440, 45), (1878, 45), (1878, 893), (440, 893)),
    "labels": [
        dict(t="Main entrance", at=P(1590, 20), kind="entry"),
        dict(t="Lifts · fire stair · toilets", at=P(1150, 760), kind="core"),
        dict(t="AHU", at=P(890, 805), kind="core"),
        dict(t="AHU", at=P(1725, 805), kind="core"),
        dict(t="West façade · 50 m of glass", at=P(1150, 45), kind="facade", rot=0),
        dict(t="South-west façade", at=P(220, 255), kind="facade", rot=-45),
        dict(t="South-east façade", at=P(220, 690), kind="facade", rot=45),
        dict(t="East façade (core side)", at=P(1150, 893), kind="facade", rot=0),
    ],
    "columns": "≈ 10.8 m × 9.7 m column grid",
    "north_deg": 0,  # drawing north points to +x (right) on the test-fit
}


def build(opt):
    zones = []
    for t, polys in opt["zones"]:
        for k, p in enumerate(polys):
            zones.append(dict(type=t, poly=p, area=round(area_m2(p), 1)))
    ev = {}
    for k, e in opt["events"].items():
        a = area_m2(e["poly"])
        ev[k] = dict(e, area=round(a))
    routes = {k: dict(pts=v, m=round(length_m(v), 1)) for k, v in opt["routes"].items()}
    return dict(zones=zones, events=ev, walls=opt["walls"], routes=routes, cameras=opt["cameras"],
                signature=opt["signature"], socGlass=opt["socGlass"])


def main():
    out = dict(types={k: dict(label=v[0], tier=v[1]) for k, v in TYPES.items()},
               opt1=build(OPT1), opt2=build(OPT2), annot=ANNOT,
               floor_area=round(area_m2(ANNOT["outline"])))
    json.dump(out, open(sys.argv[1], "w"), separators=(",", ":"))
    for k in ("opt1", "opt2"):
        o = out[k]
        by = {}
        for z in o["zones"]:
            by[z["type"]] = by.get(z["type"], 0) + z["area"]
        print(k, {t: round(a) for t, a in by.items()})
        print("   events", {e: v["area"] for e, v in o["events"].items()}, "routes", {r: v["m"] for r, v in o["routes"].items()})
    print("floor outline area m2", out["floor_area"])


if __name__ == "__main__":
    main()
