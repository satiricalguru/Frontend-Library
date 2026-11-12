# Capture methodology and limits

The capture plan starts with the 19 project and 17 Labs URLs already discovered in the Lusion catalogs, plus the home, about, projects and Labs index pages. It expands to observed links to live experiences on Lusion subdomains, with a separate mobile homepage pass. It does not guess URLs. Source robot policies were checked on 2026-11-12.

## What is collected

An isolated Chrome session opens each public route sequentially. The recorder measures rendered content height, which may differ from native document height, sends wheel and pointer input, samples screenshots and captures computed layout/type facts. It stores six visual checkpoints and encodes the sampled frames as an MP4 with variable frame durations based on wall-clock timestamps. Screenshot sampling is not guaranteed to reach 60 fps or show every transient state.

`scroll.coverage` compares measured final movement with the requested page travel. For fixed-canvas `scene-sequence` experiences, wheel input is recorded but coverage is null: document geometry cannot establish all scene states. It does not establish that every interaction or canvas scene was visited. Content can load after measurement, auto-navigate, use a custom scroll scale or require a click/drag. Check checkpoint URLs, visible IDs and limitations. Browser recordings can include loading, runtime failure, unsupported WebGL or a static experiment cover. A status of `captured` describes the capture pipeline completing, not an independently verified replica specification.

Resource inventories contain observed first-party response URLs, MIME types and response status codes. They exclude tracking hosts and query parameters. They do not contain HTTP headers, cookies, user identifiers, response bodies, copied scripts, font binaries, models, textures or original videos. SHA-256 hashes verify the local evidence files, not the site's original assets. Sources which require unavailable assets, XR, audio permissions or additional user interaction may remain incomplete; the recorder does not bypass them.

## Why full-page screenshots are insufficient

Lusion uses a fixed viewport and transformed content. In the inspected desktop homepage, native document height was one viewport while the content extended for tens of thousands of pixels. Ordinary `scrollTo` and full-page screenshot tools can capture only the top scene. The recorder compares actual content movement with the desired traversal and saves multiple viewport states. The homepage deep dive includes additional section checkpoints and a menu recording when available.

## Access and provenance

Lusion's robots file allows public paths. Labs returns an HTML application for `/robots.txt`; this absence of parsed directives is recorded as `htmlFallback`, not represented as an explicit grant. Refero's robots file disallows named AI crawlers, including GPTBot. After that policy was discovered, no new Refero style detail pages were crawled. Existing Refero records and the initially obtained public sitemap metadata remain link indexes. The sitemap contained 1,342 style URLs at inspection, matching the existing catalog; a marketing headline describing 2,000+ systems is not evidence for additional locally captured entries.

Access blocks, sign-in, paid resources and browser security warnings are not bypassed. Contributors can supply their own permissively licensed reference packages or exports they are entitled to share.

## Reproduction and rights

Screenshots and recordings show third-party designs for reference and attribution. They do not convey a reuse licence for branding, source code, models, shaders, fonts or other assets. Implement original code with appropriately licensed assets. Exact appearance and behavior cannot be guaranteed from a sampled browser traversal. Agent guidance distinguishes observed facts, inferred technique and proposed implementation.
