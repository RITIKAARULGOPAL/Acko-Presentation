"""Local server for the presentation that tells browsers not to cache, so edits always show. Every page load
rebuilds index.html from slides/ (tools/build.py), and an open page reloads itself (on the same slide and beat) when a file under
slides/, assets/css, assets/js or data/ changes: the server adds a small watcher to the page it serves, never to the build.
/?only=s-loop,s-site serves just those slides, joined (as build.py --only).

usage: python tools/serve.py [port]      (serves this checkout's root on 127.0.0.1; the port can also come from $PORT,
                                          which the preview launcher sets, so every worktree gets its own)
"""
import os, sys
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build


WATCH = ("slides", os.path.join("assets", "css"), os.path.join("assets", "js"), "data")
SKIP = {os.path.join(ROOT, "assets", "js", "shell.js")}                        # written by the build itself


def stamp():
    """the newest change under the watched folders; the open page reloads when it moves"""
    t = 0
    for d in WATCH:
        for r, _, fs in os.walk(os.path.join(ROOT, d)):
            for f in fs:
                p = os.path.join(r, f)
                if p in SKIP: continue
                try: t = max(t, os.stat(p).st_mtime_ns)
                except OSError: pass
    return str(t)


RELOAD = """<script>/* tools/serve.py (local only): reload when a slide, style, script or data file changes */
(() => { const s0 = "%s"; let busy = false;
  setInterval(() => { if (busy || document.hidden) return; busy = true;
    fetch("/__stamp", { cache: "no-store" }).then((r) => r.text()).then((t) => { if (t && t !== s0) location.reload(); }).catch(() => {}).finally(() => (busy = false)); }, 1000);
})();
</script>
"""


class NoCache(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_text(self, body, code=200, kind="text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        if "/__stamp" not in str(args[0] if args else ""): super().log_message(fmt, *args)

    def do_GET(self):
        if self.path.split("?")[0] == "/__stamp":
            return self.send_text(stamp().encode(), kind="text/plain")
        if self.path.split("?")[0].split("#")[0] in ("/", "/index.html"):
            q = self.path.split("?", 1)[1] if "?" in self.path else ""
            only = [v for k, _, v in (p.partition("=") for p in q.split("&")) if k == "only"]
            s0 = stamp()
            try:
                html, code = (build.build(only[0].split(","), "preview.html") if only else build.build()), 200
            except BaseException as e:      # a broken order.txt or slide: say so on the page instead of serving a stale deck
                html, code = f"<pre>index.html could not be built:\n{e}</pre>", 500
            i = html.rfind("</body>")
            html = html[:i] + RELOAD % s0 + html[i:] if i >= 0 else html + RELOAD % s0
            return self.send_text(html.encode("utf-8"), code)
        super().do_GET()


port = int(os.environ.get("PORT") or (sys.argv[1] if len(sys.argv) > 1 else 8766))
ThreadingHTTPServer(("127.0.0.1", port), partial(NoCache, directory=ROOT)).serve_forever()
