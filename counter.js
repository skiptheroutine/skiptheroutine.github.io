// Cloudflare Worker: simple per-app "uses" hit counter backed by KV.
// Replaces the old, dead api.countapi.xyz dependency in script.js.
//
// Routes:
//   GET /hit/<slug>  -> increments and returns { value }
//   GET /get/<slug>  -> returns { value } without incrementing
//
// Requires a KV namespace bound as USE_COUNTS (see wrangler.toml) and
// ALLOWED_ORIGIN set to the site's origin (e.g. https://you.github.io).

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get('Origin') || '';
    const corsHeaders = buildCorsHeaders(origin, env.ALLOWED_ORIGIN);

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    if (request.method !== 'GET') {
      return new Response('Method not allowed', { status: 405, headers: corsHeaders });
    }

    const match = url.pathname.match(/^\/(hit|get)\/([a-z0-9-]+)$/i);
    if (!match) {
      return json({ error: 'not found' }, corsHeaders, 404);
    }
    const [, action, slug] = match;
    const key = `app-${slug}`;

    if (action === 'get') {
      const value = parseInt(await env.USE_COUNTS.get(key), 10) || 0;
      return json({ value }, corsHeaders);
    }

    // "hit": read-increment-write. KV writes to the same key are capped at
    // ~1/sec, which is fine for a low-traffic internal app index.
    const current = parseInt(await env.USE_COUNTS.get(key), 10) || 0;
    const value = current + 1;
    await env.USE_COUNTS.put(key, String(value));
    return json({ value }, corsHeaders);
  },
};

function buildCorsHeaders(origin, allowedOrigin) {
  const allow = allowedOrigin && origin === allowedOrigin ? origin : allowedOrigin || '';
  return {
    'Access-Control-Allow-Origin': allow,
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Vary': 'Origin',
  };
}

function json(obj, headers, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...headers, 'Content-Type': 'application/json' },
  });
}
