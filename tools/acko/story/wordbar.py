# The option pages' shared parts for "We heard you" (index-heard.html, index-heard-formal.html):
#   chips(h, opts)            the small purple chip naming each option, top left of its page
#   wordbar(words, map, key, start)  a wording bar at the foot of the page: one button per wording sets the headline, label, closing line
#                             and title on every slide in `map` at once, shrinking a headline to its line limit; the choice is
#                             remembered in this browser under `key`; `start` (an id) is shown when nothing is
#   inject(h, extra)          puts the chip style, `extra` and ACKO_WOW in before the engine
# words: (id, headline first part, headline accent, label, closing line, title)
# map:   {slide id: {"title": sel, "kick": sel or None, "head": sel, "hand": sel, "lines": n}}
import json

CHIP_CSS = ('<style>.scene .page > .op-chip { left: 2.2%; top: 3.2%; z-index: 9; padding: calc(var(--pt) * 3) calc(var(--pt) * 9); border-radius: 99px; '
            'background: #5222d0; color: #fff; font-size: calc(var(--pt) * 8); font-weight: 700; letter-spacing: .04em; white-space: nowrap; pointer-events: none; }</style>\n')


def chips(h, opts):
    for sid, label in opts:
        a = h.index('id="%s"' % sid); k = h.index('<div class="page">', a) + len('<div class="page">')
        h = h[:k] + '\n    <div class="op-chip">%s</div>' % label + h[k:]
    return h


def inject(h, extra=""):
    tag = '<script src="assets/js/app.js'
    assert tag in h
    return h.replace(tag, CHIP_CSS + extra + '<script>window.ACKO_WOW = true;</script>\n' + tag, 1)


BAR = """<style>/* the wording bar (option pages only) */
#hw-bar { position: fixed; left: calc(var(--pl) + var(--pw) * .62); bottom: calc(var(--ptop) + var(--ph) * .012); transform: translateX(-50%); z-index: 130;
  display: flex; align-items: center; gap: 3px; padding: 4px 5px 4px 11px; border-radius: 99px; background: rgba(255,255,255,.95);
  box-shadow: 0 2px 14px rgba(20,10,60,.22); font: 600 12px/1 var(--body); color: #26213a; pointer-events: auto; white-space: nowrap; }
#hw-bar .hw-l { margin-right: 5px; font-size: 9.5px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #5222d0; }
#hw-bar button { min-width: 25px; height: 23px; padding: 0 7px; border: 1px solid #d6cdf3; border-radius: 99px; background: #fff; color: #5222d0;
  font: 700 11px/1 var(--body); cursor: pointer; pointer-events: auto; }
#hw-bar button:hover { border-color: #5222d0; }
#hw-bar button.on { background: #5222d0; border-color: #5222d0; color: #fff; }
#hw-bar .hw-now { max-width: 190px; margin: 0 7px; overflow: hidden; text-overflow: ellipsis; color: #26213a; }
</style>
<script>window.HEARD_WORDS = @@WORDS@@; window.HEARD_MAP = @@MAP@@;</script>
<script>
(() => {
  const W = window.HEARD_WORDS, M = window.HEARD_MAP, KEY = @@KEY@@;
  let cur = Math.max(0, W.findIndex((w) => w.id === @@START@@));
  try { const i = W.findIndex((w) => w.id === localStorage.getItem(KEY)); if (i >= 0) cur = i; } catch (e) { /* no storage: start on the first */ }
  const q = (sid, sel) => (sel ? document.querySelector("#" + sid + " " + sel) : null);
  // shrink a headline 5% at a time (to 60% at most) until it keeps to its lines and no word runs over; in deck points, so it scales
  function fit(el, lines) {
    el.style.fontSize = "";
    const page = el.closest(".page"), pt = page ? page.getBoundingClientRect().width / 720 : 1;
    if (!pt) return;
    const n = parseFloat(getComputedStyle(el).fontSize) / pt;
    for (let f = 1; f >= .6; f -= .05) {
      el.style.fontSize = `calc(var(--pt) * ${(n * f).toFixed(2)})`;
      const lh = parseFloat(getComputedStyle(el).lineHeight) || n * f * pt * 1.12;
      if (el.scrollWidth <= el.clientWidth + 1 && el.offsetHeight <= lh * lines + 2) return;
    }
  }
  function apply(i) {
    cur = i; const w = W[i];
    for (const sid in M) {
      const m = M[sid], t = q(sid, m.title), k = q(sid, m.kick), h = q(sid, m.head), c = q(sid, m.hand);
      if (t) t.textContent = w.title;
      if (k) k.textContent = w.kick;
      if (c) c.textContent = w.hand;
      if (h) { h.innerHTML = ""; h.append(w.a + " "); const s = document.createElement("span"); s.textContent = w.b; h.append(s); fit(h, m.lines); }
    }
    document.querySelectorAll("#hw-bar button").forEach((b) => b.classList.toggle("on", +b.dataset.i === i));
    const now = document.querySelector("#hw-bar .hw-now"); if (now) now.textContent = w.a + " " + w.b;
    try { localStorage.setItem(KEY, w.id); } catch (e) { /* not remembered, still shown */ }
  }
  function start() {
    const bar = document.createElement("div");
    bar.id = "hw-bar";
    bar.innerHTML = '<span class="hw-l">Words</span>' + W.map((w, i) => `<button type="button" data-i="${i}" title="${w.a} ${w.b}">${w.id}</button>`).join("") + '<b class="hw-now"></b>';
    bar.addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) { e.stopPropagation(); apply(+b.dataset.i); } });
    document.body.appendChild(bar);
    (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(() => apply(cur));
    addEventListener("resize", () => apply(cur));
  }
  window.__heard = { apply, words: W, map: M };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
</script>
"""


def wordbar(words, sel_map, key, start=None):
    data = json.dumps([dict(zip(("id", "a", "b", "kick", "hand", "title"), w)) for w in words], ensure_ascii=False)
    return BAR.replace("@@WORDS@@", data).replace("@@MAP@@", json.dumps(sel_map)).replace("@@KEY@@", json.dumps(key)).replace("@@START@@", json.dumps(start))
