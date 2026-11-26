# Ann Summers Eligibility Checker: handover

**Status:** v1 complete and final-tested on 26 Nov 2026. Anything further is version 2.

## Links

| What | Link |
|---|---|
| Live app | https://acgroup21.github.io/Levy-Calculator/as-eligibility-r8v3k.html |
| Live app with developer tools | add `?dev=1` to the link above (turn off with **Exit dev**) |
| Build Hub entry | https://acgroup21.github.io/Levy-Calculator/hub-t7r4x2.html (External lane) |
| Design concept pages | listed on the Build Hub "Ann Summers — Design concepts" card |

All pages are unlisted and `noindex`.

## Files

| File | Purpose |
|---|---|
| `src.html` | **The master. Edit this, never `index.html` or the deployed copy.** |
| `build.py` | Builds `index.html` from `src.html`: injects the Ann Summers logo (traced vectors), Fundable and AC Digital marks, and the standards list. |
| `make_ui_options.py` | Builds `ui-options.html` (style switcher page). |
| `assets/as-logo.json` | Ann Summers logo traced to vectors (made by `trace_logo.py`). |
| `assets/standards-slim.json` | 322 standards with funding bands and statuses (Skills England, 28 Jun 2026). |
| `*-concept.html`, `*-src.html` | Design concept pages and their sources. |

## Rebuild and deploy

```powershell
cd C:\Users\omari\.claude\ann-summers-eligibility
python -I build.py ../levy-calc-deploy/as-eligibility-r8v3k.html
python -I make_ui_options.py ../levy-calc-deploy/as-ui-options-r8v3k.html
cd ..\levy-calc-deploy
git add as-eligibility-r8v3k.html as-ui-options-r8v3k.html
git commit -m "describe the change"
git push
```

GitHub Pages takes about a minute. Check the live link, not just the push.

## Developer tools (`?dev=1`)

- **UI:** Current / Boardroom (Boardroom is the default for everyone).
- **Complete form:** fills a typical eligible case and jumps to the result.
- **JD: good match / bad match:** runs the job description matcher at about 77% and 0%.
- **BG:** preview Stars / Dots / Plain (only applies in dev mode; everyone else gets starlights).
- **`&asof=YYYY-MM-DD`:** pretend today is another date, to test the rules-watch notices.

## Rules and data: when to refresh

| Source | Version in the app | Refresh when |
|---|---|---|
| Apprenticeship funding rules | 2026 to 2027, version 3 (checked 25 Nov 2026) | New rules are published (usually summer). The app shows a notice from 1 Aug 2027. |
| England bank holidays (GOV.UK) | to 26 Dec 2028 | Before 2028 ends. The app warns when dates pass the list. |
| Standards and bands (Skills England) | 28 Jun 2026 | Yearly. The app warns when the data is over a year old. |
| Milburn Review | a proposal, not law | If the government adopts it. |

## What stays in the browser

Nothing is sent anywhere. Saved in the viewer's browser only: display settings (`asElig.display.v1`), splash seen (`asElig.entered.v1`), and dev-mode choices. Saved checks are files the user downloads. Report signatures are kept in memory only and never saved.

## Version 2 (paused)

A white-label version (a separate copy per brand, built from brand files, with a colour-contrast check and a brand builder page) is scoped but not started. See the project memory note for the inventory of brand-specific parts.

## About this backup

This folder (`ann-summers-eligibility-src/` in the `ACGroup21/Levy-Calculator` repo) is a backup of the editable source, taken 26 Nov 2026. The working copy lives in `C:\Users\omari\.claude\ann-summers-eligibility\`.

- Generated files (`index.html`, `ui-options.html` and the built concept pages) are left out: rebuild them with `build.py` / `make_ui_options.py`.
- `build.py` reads four logos from `..\arthur-curtis-site\assets\`. Copies are in `external-assets/`; to rebuild from this backup alone, put them at that path (or point `build.py` at `external-assets/`).
- After changing the working copy, refresh this backup by copying the same files across and committing.
