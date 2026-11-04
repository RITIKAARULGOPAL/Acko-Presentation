"""Makes, lists and revokes the deck's magic links (worker/index.js lets in only links that are in the LINKS store).

usage:
  python tools/links.py new "ACKO leadership"              a new link; prints its URL
  python tools/links.py new "Ritika review" --days 7       one that switches itself off after 7 days
  python tools/links.py list                               the live links
  python tools/links.py revoke "ACKO leadership"           switches a link off (by label or secret); anyone who opened it
                                                           is shut out on their next load, within about a minute
  add --local to any of these to work on the local store that `wrangler dev` uses
"""
import datetime, json, os, secrets, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://acko-the-loop.cko--resentation.workers.dev"   # the address tools/deploy.py prints
if "--local" in sys.argv: SITE = "http://localhost:8787"
WRANGLER = ["npx", "--yes", "wrangler@4"]
WHERE = ["--local"] if "--local" in sys.argv else ["--remote"]


def wrangler(*args):
    r = subprocess.run(WRANGLER + ["kv", "key", *args, "--binding", "LINKS", *WHERE], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", shell=os.name == "nt")   # npx is a .cmd on Windows
    if r.returncode: raise SystemExit(r.stdout + r.stderr)
    return r.stdout


def links():
    out = wrangler("list")
    return json.loads(out[out.index("["):])


def day(t):
    return datetime.datetime.fromtimestamp(t).strftime("%d %b %Y %H:%M") if t else "never"


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--local"]
    cmd = args[0] if args else "list"
    if cmd == "new" and len(args) >= 2:
        label, secret = args[1], secrets.token_urlsafe(24)
        meta = {"label": label, "created": int(time.time())}
        extra = []
        if "--days" in args:
            extra = ["--expiration", str(int(time.time() + float(args[args.index("--days") + 1]) * 86400))]
        wrangler("put", secret, label, "--metadata", json.dumps(meta, separators=(",", ":")), *extra)
        print(f"{label}: {SITE}/l/{secret}" + (f"  (until {day(int(extra[1]))})" if extra else ""))
    elif cmd == "list":
        rows = links()
        if not rows: print("no live links")
        for k in rows:
            m = k.get("metadata") or {}
            print(f"{m.get('label', '?'):<28} made {day(m.get('created'))}   ends {day(k.get('expiration'))}\n    {SITE}/l/{k['name']}")
    elif cmd == "revoke" and len(args) >= 2:
        hits = [k["name"] for k in links() if args[1] in (k["name"], (k.get("metadata") or {}).get("label"))]
        if not hits: raise SystemExit(f"no live link is labelled or named '{args[1]}'")
        for name in hits: wrangler("delete", name)
        print(f"revoked {len(hits)} link(s): {args[1]}")
    else:
        raise SystemExit(__doc__)
