# Add a client tracker

How to stand up a new client's apprentice tracker from the shared engine.

## The model (master / instance)

There is **one engine** (`landmark-tracker.html` — the master template) and **one config per client**.
A generator stamps out each client's own tracker file. Clients share the engine and the KSB
reference library; each client's **learner data is fully isolated** (its own `localStorage`
namespace — one client can never read another's data).

Everything client-specific lives in three places, all swapped by the generator:

1. the `CONFIG` object (branding, provider, which standards) — between `//<<CONFIG>>` markers
2. the `DEMO` cohort — between `//<<DEMO>>` markers
3. the logo `<img id="brandLogo">`

> **Golden rule:** edit the **master** (`landmark-tracker.html`) and **regenerate**.
> Never hand-edit a generated `dist/*.html` or the deployed copy — your change will be lost
> on the next regenerate.

---

## Quick start (≈2 minutes)

```bash
cd tracker-build
# 1. copy an existing config and edit it
cp clients/landmark.json clients/acme.json      # then edit clients/acme.json (see schema below)

# 2. generate
python generate-client.py acme                  # -> dist/acme-tracker.html

# 3. deploy dist/acme-tracker.html wherever the client's tracker should live
```

That's it. Open `dist/acme-tracker.html`, click **Load demo cohort** to sanity-check, done.

---

## The client config — `clients/<id>.json`

```jsonc
{
  "clientId": "acme",                 // REQUIRED. localStorage namespace — must be unique &
                                      // stable. Changing it later orphans that client's data.
  "brand": {
    "clientName": "Acme Group",       // used in <title>, report header, review printout
    "appTitle": "Apprentice Tracker",
    "tagline": "Learner reviews & progress · Acme Group",
    "intro": "Log apprentice progress reviews — they feed the tracker & dashboard.",
    "footerName": "Acme Apprentice Tracker",
    "version": "v1.0 · build 2026-07-06",
    "logoAlt": "Acme",
    "logo": null                      // null -> a text placeholder wordmark is generated.
                                      // "keep" -> leave the template's logo.
                                      // "data:image/svg+xml;base64,…" -> the client's own logo.
  },
  "provider": {
    "name": "OneFile",                // the e-portfolio (some providers use "Bud")
    "org": "Ginger Nut Training",     // the training provider
    "heading": "Provider data — OneFile (Ginger Nut Training)",
    "importLabel": "↑ Import OneFile CSV",
    "cardLabel": "OneFile · Ginger Nut"
  },
  "standards": ["ST0384"],            // REQUIRED. ST codes the cohort is on (see below).
  "demo": "keep"                      // "keep" = template's demo, or {reviews:[…],provider:{…}},
                                      // or a filename, or null for an empty demo.
}
```

### Finding a standard's ST code

Standards are keyed by their **ST reference code** (e.g. `ST0384` = Team Leader). To look one up:

```bash
python -c "import json; L=json.load(open('ksb-library.json',encoding='utf-8'))['standards']; \
print([ (c,e['name']) for c,e in L.items() if 'team lead' in e['name'].lower() ])"
```

The library has **257 standards** (every apprenticeship standard that publishes KSBs). Only the
codes you list in `standards` are embedded in that client's file — never all 257 (that's ~2.6 MB).
If a client's standard isn't in the library, it simply shows no KSB panel (honest) until added.

---

## When the engine changes (a feature or fix for everyone)

Edit the **master** `landmark-tracker.html`, then regenerate **all** clients so they inherit it:

```bash
python generate-client.py --all      # regenerates dist/*.html for every clients/*.json
```

Then redeploy each `dist/*.html`. (Engine features — e.g. the review printout, KSB tracking —
propagate automatically; only client-specific bits differ.)

---

## Rebuilding the KSB library (occasionally)

The library is derived from the apprenticeship scraper. Rebuild when the scraper is refreshed:

```bash
python build-library.py              # scraper output -> ksb-library.json (257 standards)
```

---

## Notes & current limits

- **Data isolation** is by `clientId` — keys are `<clientId>_reviews_v1`, `<clientId>_provider_v1`,
  `<clientId>_summary_notes_v1`, `<clientId>_ksb_v1`. Keep `clientId` unique and stable.
- **Palette is shared** (the validated Landmark navy/coral). Per-client colours are a planned
  follow-up — each new palette needs a WCAG-AA contrast check (screen **and** the white report),
  so don't just drop in arbitrary brand colours yet.
- **Logo** is embedded at generate time, so a client's file never carries another client's logo.
- **PII / GDPR:** trackers hold real learner data in the browser on the device. Share the **PDF
  report** externally (read-only), keep the JSON/CSV working-data internal. Cloud sync is a
  separate backend phase.

## Files

| File | What it is |
|---|---|
| `generate-client.py` | the generator: master + `clients/<id>.json` → `dist/<id>-tracker.html` |
| `build-library.py` | builds `ksb-library.json` from the apprenticeship scraper |
| `build-ksb.py` | extracts a KSB subset for given ST codes (used by the generator) |
| `ksb-library.json` | master KSB reference — 257 standards, keyed by ST code |
| `clients/<id>.json` | one config per client |
| `dist/<id>-tracker.html` | generated, deployable client trackers |
