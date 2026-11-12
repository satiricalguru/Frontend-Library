# Contribute a reference package

Use a pull request to add a reference or upload original/permitted evidence files. Start with one clear target and its exact discovery source.

## Reference metadata

```json
{
  "id": "publisher-page-name",
  "name": "Page or demo name",
  "url": "https://example.com/actual-page",
  "source": "https://example.com/page-where-you-found-it",
  "collected": "YYYY-MM-DD",
  "kind": "landing-page",
  "tags": ["scroll", "webgl", "product"],
  "evidence": "Describe what was actually inspected",
  "rights": "Owner, evidence permissions and any applicable licence"
}
```

Choose a precise kind: `landing-page`, `case-study`, `lab-case-study`, `interactive-experience`, `demo-repository`, `article-reference`, `design-analysis` or a provider/tool category. A studio write-up and its live project need separate records.

## Useful evidence

- Viewport width/height, device pixel ratio, capture date and page status.
- Opening, middle and closing screenshots plus a short traversal or interaction recording.
- Section IDs/geometry, scene states, input sequence and observed media/resource URLs.
- Reduced-motion and mobile evidence where available.
- Clear limits: missing assets, failed loads, untested interactions and inferred techniques.

Store a package under a clear collection folder and index it in the matching JSON catalog. Follow the [capture record schema](../../.agents/skills/frontend-library/references/records.md) for Lusion-style page packages. Include file hashes for committed media and upstream commit/hash attribution for imported documents.

## Before opening a pull request

Inspect every screenshot: loading screens, errors and unsupported renderers should be flagged. Only label complete travel when you measured it; fixed-canvas scene sequences often cannot expose a reliable total through the DOM. A successful request is not proof of a working page.

Contribute original code or files whose licences permit redistribution. Preserve applicable licence notices. Link to proprietary models, shaders, fonts and media instead of uploading them. Stock-provider listings are not licences for individual footage.

Run the checks in [CONTRIBUTING.md](../../CONTRIBUTING.md). In the PR, state what the package lets a builder or agent inspect and which states remain unverified.
