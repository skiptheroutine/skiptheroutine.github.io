# App Index

A static, personal-info-free directory for your Streamlit apps, grouped by
category. Pure HTML/CSS/JS — no build step, no framework, no server.

## 1. Publish it

1. Create a new **public** GitHub repo (e.g. `app-index`).
2. Push everything in this folder to the repo's default branch.
3. In the repo: **Settings → Pages → Build and deployment → Source: Deploy
   from a branch** → branch `main`, folder `/ (root)` → Save.
4. Your site is live at `https://<username>.github.io/<repo>/` within a
   minute or two.

That's it — no GitHub Action, no dependency install, nothing to keep
maintained. The `.nojekyll` file just tells Pages to serve the files as-is.

## 2. Add a new app (the only thing you ever touch)

Open `apps.json` and add one entry to the `apps` array:

```json
{
  "name": "Your App Name",
  "category": "steel",
  "url": "https://your-app.streamlit.app",
  "description": "One sentence describing what it does."
}
```

Commit and push. The site rebuilds automatically (GitHub Pages redeploys on
every push) — no local build, no script to run. That's the "minimal effort"
part: one JSON entry per app.

## 3. Add a new category

Add an entry to the `categories` array in `apps.json`:

```json
{ "id": "geotech", "code": "GEO", "label": "Geotechnical" }
```

`id` is the internal key you reference from an app's `"category"` field.
`code` is the short tag shown on each app's marker (keep it 3 letters, but
it's not enforced). `label` is the section heading. Categories with zero
apps are simply not rendered, and any app whose `category` doesn't match a
known `id` gets grouped under an automatic "Uncategorized" section instead
of disappearing — so a typo never silently hides an app.

## 4. About "zero effort" auto-discovery

There's no public API for Streamlit Community Cloud that lists everything
deployed under an account, so there's no reliable way to have this site
notice a new deployment on its own without you telling it. The `apps.json`
approach is the lowest-effort alternative: one small, versioned edit per
app, no credentials or scraping involved. If Streamlit ever ships an
account-level API, this is the one file you'd need to auto-generate instead
of hand-editing.

## 5. Set up the "uses" counter

Each app card shows a hit counter, backed by a tiny Cloudflare Worker (free
tier) instead of a third-party service, so it doesn't quietly die on you.

1. Install wrangler and log in: `npm install -g wrangler && wrangler login`.
2. From `worker/`, create the KV namespace: `wrangler kv namespace create USE_COUNTS`.
3. Paste the returned `id` into `worker/wrangler.toml`.
4. Set `ALLOWED_ORIGIN` in `worker/wrangler.toml` to your GitHub Pages origin
   (e.g. `https://you.github.io`, no trailing slash or path).
5. Deploy: `cd worker && wrangler deploy`. Note the `*.workers.dev` URL it prints.
6. In `script.js`, set `COUNTER_API_BASE` to that URL.
7. Commit and push.

If the counter ever stops updating again, open the browser console on the
site — failures are now logged there (`Failed to record/load a use for...`)
instead of being swallowed silently, and unloaded counts show `— uses`
rather than a misleading `0 uses`.

## Files

- `index.html` — page shell
- `style.css` — all styling
- `script.js` — reads `apps.json` and renders the grouped, filterable grid
- `apps.json` — **the only file you edit day-to-day**
- `worker/` — Cloudflare Worker + KV backing the "uses" counter
- `.nojekyll` — tells GitHub Pages to skip Jekyll processing
