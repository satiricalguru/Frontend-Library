# Frontend Library for coding agents

For reference-led frontend work, read [.agents/skills/frontend-library/SKILL.md](.agents/skills/frontend-library/SKILL.md). Search with `python3 scripts/query-library.py "query" --json` before reading large catalogs. `data/library-manifest.json` describes the collections; `data/landing-pages.json` points to local image, video and page evidence.

Distinguish link-only entries, captured case studies, captured landing pages and proposed implementation recipes. Do not claim that a studio's case-study recording captures its client's live website or that a canvas proves Three.js. Record observed/inferred/proposed claims separately. Keep the chosen product and reference direction.

Contributions need `name`, `url`, exact discovery `source`, attribution and a date. Source media keeps its owner's rights; original snippets have their own licence. Never commit authentication data, copied proprietary JS bundles or downloaded paid assets. Respect source crawling rules and record access failures.

After catalog changes run `python3 scripts/build-catalog.py` and `python3 scripts/build-visuals.py`. After captures run `python3 scripts/build-reference-library.py`. Validate with `python3 scripts/validate-data.py`, `python3 scripts/validate-references.py` and `node scripts/check-code.mjs`. Preserve unrelated working-tree edits. Do not push or publish unless requested.
