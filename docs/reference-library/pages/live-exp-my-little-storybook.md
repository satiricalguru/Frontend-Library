# Exp My Little Storybook — live experience

[Source](https://exp-my-little-storybook.lusion.co/) · [Discovery page](https://labs.lusion.co/exp/covid-spike) · [Raw record](../../../captures/lusion/live-exp-my-little-storybook/page.json)

Captured `2026-11-12T08:18:36.248Z` at **1440 × 900**. Type: **interactive-experience**. Status: **needs-review**.

[Play/download the recorded browser traversal](../../../captures/lusion/live-exp-my-little-storybook/traversal.mp4) (5.4 seconds, muted). This is a browser recording, not an extracted source video.

## Visual checkpoints

Each percentage is requested capture progress, not a verified animation timeline. Check the recorded URL and visible section IDs.

![Checkpoint 0 at 0.0s](../../../captures/lusion/live-exp-my-little-storybook/checkpoint-00.jpg)

Frame `0` · `0.0s` · requested progress `0` · [actual route](https://exp-my-little-storybook.lusion.co/).

![Checkpoint 5 at 1.0s](../../../captures/lusion/live-exp-my-little-storybook/checkpoint-01.jpg)

Frame `5` · `1.0s` · requested progress `0.22` · [actual route](https://exp-my-little-storybook.lusion.co/).

![Checkpoint 9 at 2.0s](../../../captures/lusion/live-exp-my-little-storybook/checkpoint-02.jpg)

Frame `9` · `2.0s` · requested progress `0.39` · [actual route](https://exp-my-little-storybook.lusion.co/).

![Checkpoint 14 at 3.2s](../../../captures/lusion/live-exp-my-little-storybook/checkpoint-03.jpg)

Frame `14` · `3.2s` · requested progress `0.61` · [actual route](https://exp-my-little-storybook.lusion.co/).

![Checkpoint 18 at 4.2s](../../../captures/lusion/live-exp-my-little-storybook/checkpoint-04.jpg)

Frame `18` · `4.2s` · requested progress `0.78` · [actual route](https://exp-my-little-storybook.lusion.co/).

![Checkpoint 23 at 5.4s](../../../captures/lusion/live-exp-my-little-storybook/checkpoint-05.jpg)

Frame `23` · `5.4s` · requested progress `1` · [actual route](https://exp-my-little-storybook.lusion.co/).

## Observed structure

| Section ID | Initial y | Height |
|:--|--:|--:|
| `app` | 0 | 900 |
| `preloader` | 0 | 900 |
| `intro` | 0 | 900 |
| `story` | 0 | 900 |
| `ending` | 0 | 0 |
| `about-exit` | 0 | 0 |
| `about-container` | 0 | 0 |
| `about-plants` | 0 | 0 |

## Implementation boundary

This package records the route above. A studio case study may show videos of a client website; it does not establish that client's runtime or interactions. Inspect the outbound links in the record before choosing a live project as a target.

- A recorded browser traversal, not an offline copy of the site.
- Shader source, models, textures and original media are inventoried by URL only.
- Audio is muted. Scroll checkpoints do not enumerate every possible interaction.
- A canvas does not by itself prove Three.js or any particular rendering technique.
- Fixed-canvas scene sequence: wheel input was sampled, but complete scene coverage cannot be measured from document geometry.
- An ENTER onboarding state was visible, followed by a blank final frame; the entered experience remains unverified.

Reference screenshots and recordings of Lusion work; original rights retained. No reusable asset licence granted.

[Agent workflow](../../../.agents/skills/frontend-library/SKILL.md) · [Implementation guidance](../../../.agents/skills/frontend-library/references/implementation.md)
