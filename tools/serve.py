"""Local server for the presentation that tells browsers not to cache, so edits always show. Every page load
rebuilds index.html from slides/ (tools/build.py), so save a slide or change slides/order.txt and refresh.

usage: python tools/serve.py [port]      (serves this checkout's root on 127.0.0.1; the port can also come from $PORT,
                                          which the preview launcher sets, so every worktree gets its own)
"""
import os, sys
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build


class NoCache(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path.split("?")[0].split("#")[0] in ("/", "/index.html"):
            try:
                body, code = build.write().encode("utf-8"), 200
            except BaseException as e:      # a broken order.txt or slide: say so on the page instead of serving a stale deck
                body, code = f"<pre>index.html could not be built:\n{e}</pre>".encode("utf-8"), 500
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


port = int(os.environ.get("PORT") or (sys.argv[1] if len(sys.argv) > 1 else 8766))
ThreadingHTTPServer(("127.0.0.1", port), partial(NoCache, directory=ROOT)).serve_forever()
