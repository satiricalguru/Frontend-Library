# Translating references into working pages

## Build a motion specification

For each section record: trigger (entry, scroll, hover, click or elapsed time), target, start/end states, duration or scroll interval, easing, pin interval, asset dependency, mobile behavior, and reduced-motion behavior. Measure values in the actual viewport. Record a range when timing cannot be established from the sampled video.

For virtual scrolling, `document.scrollHeight` may describe only the fixed viewport. Inspect the transformed content container and recorded section rectangles. Do not use the page's requested capture progress as camera keyframes without visual confirmation. A screenshot of all DOM content cannot show all time-dependent canvas states.

## WebGL / Three.js implementation choices

These are proposed techniques, not claims about Lusion internals:

| Desired behavior | Suitable starting point | Verify |
|---|---|---|
| Scroll camera journey | PerspectiveCamera + CatmullRomCurve3; interpolate camera position and look-at independently | Framing and transitions at matched checkpoints |
| Many repeated meshes | InstancedMesh with per-instance transform data | Draw calls, fill rate and mobile memory |
| Pointer-reactive hero | Raycaster or normalized pointer uniforms; time-based damping | Touch fallback, pointer exit and reduced motion |
| Scene material transitions | ShaderMaterial uniforms, render targets or simple opacity where sufficient | Shader compile errors, color space, resize and alpha |
| HDR-lit product scene | Licensed glTF + environment map; tone mapping chosen to match evidence | Texture budget, reflections and device exposure |
| Scroll-linked object animation | AnimationMixer with explicit clip time rather than free running playback | Bidirectional scrubbing and endpoint poses |
| Video section | Muted inline video with a poster; user-initiated audio | Rejected autoplay, loading and mobile decoding |

Use [Three.js documentation](https://threejs.org/docs/) and the [responsive rendering guide](https://threejs.org/manual/en/responsive.html) for actual APIs. No Three.js version is inferred from these captures. Keep the project lockfile authoritative.

Map progress explicitly: `p = clamp((scrollPosition - sectionStart) / sectionDuration, 0, 1)`. For frame-rate-independent smoothing, use `alpha = 1 - exp(-damping * deltaSeconds)`. Do not smooth every input and output independently; that creates unintended lag. Prefer one scroll source shared by DOM and canvas.

## Fidelity and performance

Match composition before detail: camera, silhouette, type scale, whitespace, contrast, then lighting and effects. Choose asset formats only after inspecting the target project; an observed `.buf` is a custom binary and should not be presented as a compatible glTF model.

Use one animation loop per scene. Cap pixel ratio, pause hidden/offscreen scenes, dispose GPU resources, and provide a static fallback on context loss. Keep links, navigation, headings and primary actions in semantic DOM. For reduced motion, show a stable representative frame with ordinary navigation instead of long pinned camera travel. Measure frame time on a real lower-powered device before setting a performance claim.

Compare images at identical viewport sizes, scroll states and loading conditions. Canvas randomness and live videos make raw pixel differences noisy; compare stable typography/layout separately from stochastic scenes. Record remaining differences rather than inventing precision.
