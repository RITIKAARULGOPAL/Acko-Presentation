// The deck online, behind magic links (wrangler.jsonc; links made and revoked with tools/links.py).
//
//   /l/<secret>   a link: if <secret> is a key in the LINKS store, sets a cookie for it and opens the deck
//   anything else needs that cookie, and its link must still be in the store: revoking a link (deleting the key)
//   shuts out everyone who opened it, on their next load (within about a minute: KV reads are cached that long)

const COOKIE = "acko_link";
const SECRET = /^[A-Za-z0-9_-]{20,100}$/;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    const m = url.pathname.match(/^\/l\/([^/]+)\/?$/);
    if (m) {
      if (!SECRET.test(m[1]) || !(await live(env, m[1]))) return closed();
      return new Response(null, { status: 302, headers: {
        Location: "/",
        "Set-Cookie": `${COOKIE}=${m[1]}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=2592000`,
        "Cache-Control": "no-store",
      } });
    }

    const secret = (request.headers.get("Cookie") || "").match(new RegExp(`(?:^|;\\s*)${COOKIE}=([^;]+)`));
    if (!secret || !SECRET.test(secret[1]) || !(await live(env, secret[1]))) return closed();

    const res = await env.ASSETS.fetch(request);
    const out = new Response(res.body, res);
    out.headers.set("X-Robots-Tag", "noindex, nofollow");
    // the page itself is never cached, so a revoked link stops working on the next reload
    if ((out.headers.get("Content-Type") || "").startsWith("text/html")) out.headers.set("Cache-Control", "private, no-store");
    else out.headers.set("Cache-Control", "private, max-age=3600");
    return out;
  },
};

async function live(env, secret) {
  return (await env.LINKS.get(secret, { cacheTtl: 60 })) !== null;
}

function closed() {
  return new Response(
    `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>ACKO · The Loop</title>
<style>html,body{margin:0;height:100%}body{display:grid;place-items:center;font:500 15px/1.5 system-ui,sans-serif;color:#5222d0;background:#fff;text-align:center}
small{display:block;margin-top:.5em;color:#666;font-weight:400}</style></head>
<body><p>ACKO · The Loop<small>This link isn't active. Ask SKV for a new one.</small></p></body></html>`,
    { status: 403, headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store", "X-Robots-Tag": "noindex" } });
}
