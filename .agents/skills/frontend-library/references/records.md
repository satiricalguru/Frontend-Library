# Reading and contributing records

`data/library-manifest.json` lists available collections. Each catalog is JSON with an `items` array. Existing catalogs retain their own fields. Search results normalize only name, URL, source, type and local evidence paths.

`data/landing-pages.json` indexes locally captured routes. Its `record` points to `captures/lusion/<id>/page.json`, which contains:

- `version`, `id`, `url`, `source`, `kind`, `capturedAt`, `viewport`, `status`, `rights`, `limitations`.
- `initial` and `final`: title, section IDs/rectangles, computed typography, canvases, media URLs and outbound links. No copy of compiled scripts or full page prose.
- `scroll`: native, virtual or a fixed-canvas `scene-sequence`, requested travel and measured movement when available. Scene-sequence coverage is null because geometry cannot establish every state. This is input coverage, not proof of every interaction.
- `checkpoints`: screenshot path relative to the record, frame/time, requested progress, actual URL, content transform and visible IDs.
- `resources`: observed first-party response URLs, MIME types and status. Query parameters and tracking hosts are excluded. These URLs are not bundled assets or permission to reuse them.
- `video`: locally recorded browser traversal with wall-clock timing. It is not the original source video.
- `files`: byte sizes and SHA-256 hashes for the screenshots and recording.
- `runtimeErrors`: runtime exceptions, if observed. A successful HTTP response does not guarantee a working WebGL scene; check the pictures and status.

IDs are stable kebab-case strings. Every new reference needs its own URL, exact discovery source and a capture date. Do not label an unvisited live client site as captured because its case study was recorded. Use `needs-review` or `failed` when appropriate and preserve evidence of the limitation.

For refreshes, run `node scripts/capture-pages.mjs --id <id> --force` from the checkout and then `python3 scripts/build-reference-library.py`. The capture plan contains discovered URLs, not guessed routes. Review robots policy before extending it to a new host. Do not bypass login, paywalls or access controls. See the repository's `CONTRIBUTING.md` for pull requests and checks.

The additional `design-md`, `codrops` and `media-resources` catalogs preserve upstream commits and discovery sources. `localDesignPath` points to a licensed local analysis; `designMarkdownUrl` points to its pinned raw source. Demo and provider metadata do not imply a page was visually captured or all linked assets are licensed for reuse.
