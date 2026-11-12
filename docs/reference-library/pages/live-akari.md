# Akari — live experience

[Source](https://akari.lusion.co/) · [Discovery page](https://labs.lusion.co/exp/choochoo) · [Raw record](../../../captures/lusion/live-akari/page.json)

Captured `2026-11-12T08:18:07.229Z` at **1440 × 900**. Type: **interactive-experience**. Status: **needs-review**.

[Play/download the recorded browser traversal](../../../captures/lusion/live-akari/traversal.mp4) (5.2 seconds, muted). This is a browser recording, not an extracted source video.

## Visual checkpoints

Each percentage is requested capture progress, not a verified animation timeline. Check the recorded URL and visible section IDs.

![Checkpoint 0 at 0.0s](../../../captures/lusion/live-akari/checkpoint-00.jpg)

Frame `0` · `0.0s` · requested progress `0` · [actual route](https://akari.lusion.co/).

![Checkpoint 5 at 1.8s](../../../captures/lusion/live-akari/checkpoint-01.jpg)

Frame `5` · `1.8s` · requested progress `0.22` · [actual route](https://akari.lusion.co/).

![Checkpoint 9 at 2.5s](../../../captures/lusion/live-akari/checkpoint-02.jpg)

Frame `9` · `2.5s` · requested progress `0.39` · [actual route](https://akari.lusion.co/).

![Checkpoint 14 at 3.5s](../../../captures/lusion/live-akari/checkpoint-03.jpg)

Frame `14` · `3.5s` · requested progress `0.61` · [actual route](https://akari.lusion.co/).

![Checkpoint 18 at 4.2s](../../../captures/lusion/live-akari/checkpoint-04.jpg)

Frame `18` · `4.2s` · requested progress `0.78` · [actual route](https://akari.lusion.co/).

![Checkpoint 23 at 5.2s](../../../captures/lusion/live-akari/checkpoint-05.jpg)

Frame `23` · `5.2s` · requested progress `1` · [actual route](https://akari.lusion.co/).

## Observed structure

| Section ID | Initial y | Height |
|:--|--:|--:|
| `preloader` | 153 | 16 |
| `ui` | 153 | 593 |

## Implementation boundary

This package records the route above. A studio case study may show videos of a client website; it does not establish that client's runtime or interactions. Inspect the outbound links in the record before choosing a live project as a target.

- A recorded browser traversal, not an offline copy of the site.
- Shader source, models, textures and original media are inventoried by URL only.
- Audio is muted. Scroll checkpoints do not enumerate every possible interaction.
- A canvas does not by itself prove Three.js or any particular rendering technique.
- Final visual QA found a mostly blank viewport. Interactive scene entry and complete behavior remain unverified.
- Opening fixed-viewport/pointer state only; zero native travel does not establish complete interaction or scroll coverage.

Reference screenshots and recordings of Lusion work; original rights retained. No reusable asset licence granted.

[Agent workflow](../../../.agents/skills/frontend-library/SKILL.md) · [Implementation guidance](../../../.agents/skills/frontend-library/references/implementation.md)
