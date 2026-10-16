"""The deck's own click-by-click animation on a slide: each click, and what enters or exits (with its text or picture).
    python tools/acko/deck_anim.py "<deck.pptx>" 5 6 …"""
import re, sys, zipfile
import xml.etree.ElementTree as ET
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
z = zipfile.ZipFile(sys.argv[1])
for i in map(int, sys.argv[2:]):
    root = ET.fromstring(z.read(f"ppt/slides/slide{i}.xml"))
    rels = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="\.\./media/([^"]+)"', z.read(f"ppt/slides/_rels/slide{i}.xml.rels").decode()))
    names = {}
    for el in root.iter():
        nv = el.find(f"./{P}nvSpPr/{P}cNvPr") or el.find(f"./{P}nvPicPr/{P}cNvPr") or el.find(f"./{P}nvGrpSpPr/{P}cNvPr")
        if nv is None:
            continue
        txt = "".join(t.text or "" for t in el.iter(A + "t"))[:46]
        blip = el.find(f".//{A}blip")
        pic = rels.get(blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"), "") if blip is not None else ""
        names[nv.get("id")] = (txt or pic or nv.get("name"))
    seq = root.find(f".//{P}cTn[@nodeType='mainSeq']")
    print(f"--- slide {i}")
    if seq is None:
        print("  (no click sequence)"); continue
    for k, click in enumerate(seq.find(f"./{P}childTnLst"), 1):
        effs = []
        for ctn in click.iter(P + "cTn"):
            cls = ctn.get("presetClass")
            if not cls:
                continue
            tgt = ctn.find(f".//{P}spTgt")
            d = 0
            par = ctn
            effs.append(f"{cls}:{ctn.get('presetID')}:{ctn.get('nodeType')[:5]} {names.get(tgt.get('spid'), tgt.get('spid'))}")
        print(f"  click {k}:"); [print("     ", e) for e in effs]
