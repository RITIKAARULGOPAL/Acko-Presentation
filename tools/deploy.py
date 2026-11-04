"""Builds dist/site/ (tools/build.py --site) and uploads it to Cloudflare as the acko-the-loop Worker (static assets only).

Only dist/site/ goes up: index.html and the files it uses; nothing else of the repo (tools/, the DXF work, the docs).
The settings are in wrangler.jsonc at the repo root.

usage:
  npx wrangler@4 login                   once per machine: signs in to Cloudflare in the browser
  python tools/deploy.py                 builds and uploads
  python tools/deploy.py --dry-run       builds and checks the upload without sending anything
"""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WRANGLER = ["npx", "--yes", "wrangler@4"]


def run(args):
    print("> " + " ".join(args))
    subprocess.run(args, cwd=ROOT, check=True, shell=os.name == "nt")   # npx is a .cmd on Windows


if __name__ == "__main__":
    run([sys.executable, os.path.join("tools", "build.py"), "--site"])
    run(WRANGLER + ["deploy"] + (["--dry-run"] if "--dry-run" in sys.argv else []))
