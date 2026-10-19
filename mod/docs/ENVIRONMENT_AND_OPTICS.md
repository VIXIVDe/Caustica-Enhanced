# Environment, diffraction and participating media

## Optical response

An eight-sided aperture FFT is integrated over 48 wavelengths and filtered by a
2.6-texel sensor footprint. Its integrated luminance remains one. Display-space
support is shortened; each selected source has an exposed-luminance soft knee
of 6–18 during daylight and 16–48 at night. An exponential radial envelope and
smooth support cutoff fade each arm to zero before the texture boundary.
Up to 16 sources contribute.
These are internal scene-linear thresholds, not monitor nits.

Sources are measured in a 4×4 grid over the half-resolution highlight field and
then tracked between frames. Emitter pixels from the raw trace are read at
jitter-compensated coordinates, so sub-pixel camera jitter does not move them.
Each position is the support-weighted centroid of the bright core rather than its
single brightest texel. A measurement is matched to last frame's track after
reprojecting it with its depth and the camera matrices, so camera motion is
removed exactly and only measurement noise is filtered (about 100 ms for
position, 55 ms for intensity and size). A per-track residual motion follows
sources that move on screen by themselves, and view-locked sources such as a
held light are matched directly in screen space. Large changes are followed
immediately. Unmatched tracks coast and fade over a few frames, and ghosts and
halos follow one primary source that changes only when another is 30% brighter.
Frozen offline photographs keep their own single-pass source selection.

Cinematic Lens Effects adds a bloom-fed horizontal streak and three differently
colored internal-reflection ghosts before the SDR/HDR output transform. It
shares the existing bloom and full-frame offline highlight field. Film grain,
vignette, distortion and chromatic aberration retain their own controls.

## End environment

The far environment, internal light and mist share a violet palette. End beams
use three octaves of world-XZ noise, a soft height envelope centered at Y=68,
and a 24-step weighted additive view integral. The field uses absolute world
coordinates and frozen scene time, so view, reflections and offline tiles share
the same pattern. Beam emission remains visible with cloud, light and fog
switches disabled; near and far integration ranges do not overlap. Its emission
also contributes through environment escape paths. The visible vortex is a world-space
participating medium with a lower base density. Vertical
noise stretching, height-dependent rotation (approximately 1/72 radian per
block), erosion, a central cavity and an annular gap shape the volume. Original
Minecraft portal textures remain on the portal surface.

The End view ray uses 32 nonuniform steps over at most 650 blocks, with jitter
shared by film coordinates. Beer-Lambert integration clips at the first actual
surface. Three density probes toward the internal point light approximate
self-shadowing, with a bounded colored multiple-scattering term. Outside the
central region a world-cell flash source contributes magenta illumination.
Its timer and placement are deterministic functions of frozen scene time,
making all offline tiles use the same event. No lightning bolt geometry is
generated. The fog switch controls volume integration and medium shadows.

The same point source and medium shadow function illuminate opaque surfaces
through geometry visibility and the existing BSDF. Ordinary path tracing adds
its diffuse/specular contributions at each bounce; ReSTIR PT evaluates it as
fresh analytic residual lighting rather than inserting a false static emitter
into the reservoir. End indirect-cache storage is disabled for this animated
illumination. Smooth far radiance still supplies escape paths and reflection
backgrounds; a separate cloud/End sky LUT is not implemented.

Overworld mist combines rain and daily height profiles with banks and erosion.
Daily mist is present at dawn, dusk and night and absent at noon. Its sea-level
gradient keeps high mountain peaks clear, while rain follows exposed terrain.
Noise uses integer world anchors, so camera rebasing does not shift the field.
Terrain exposure and camera-depth support suppress roof and deep-cave mist.
The existing Hillaire Rayleigh/Mie/ozone LUTs continue to supply the shared sky,
sun/moon spectrum and finite-distance aerial perspective. Their physical
parameters and exposure/SDR/HDR output curves are retained; Bliss's non-unit
solar-vector adjustment, Purkinje transform and full climate profile system are
not ported. LOD edge blending remains separate from local mist.

Underwater scattering is scaled to approximately 30% of its previous value in
both the direct march and froxel medium. Extinction and water absorption are
unchanged; reducing scattering does not make water optically clear.

## Shared photo atmosphere and LOD ownership

Photo panels default clouds, light and fog to enabled independently of gameplay
switches. Strength and detailed parameters follow current gameplay settings,
rather than saved photo preferences. External parameter changes are detected
before preview or capture. Preview writes mark the resulting configuration so
its own overrides do not feed back into synchronization. Cloud intensity and
the detailed cloud settings remain the shared gameplay configuration.

Photo rendering hides fallback LOD only where full near geometry is ready.
Gameplay reserves the near interior but retains fallback in the outer two-column
loading margin. The radius matches effective near render distance, including
photo overrides. This prevents an empty ring while boundary meshes await neighbors.
Voxy conversion continues without an extra timer delay while work is deferred;
DH selection is refreshed more often and completed GPU uploads publish in
larger batches. CPU and device-memory bounds remain enforced.

Overcast cloud transport multiplies optical depth by up to 3.5 and sharply
reduces the view-ray transmission compensation. Cloud-free rays are unchanged.
Both cloud self-lighting and terrain/cloud shadow paths use the increased
extinction, so this does not merely darken the sun globally.

## Rain splash coverage

Water-drop billboards retain their center and motion but use one-quarter of the
captured width/height. A splash-only primitive flag selects stochastic texture
coverage rather than treating every texel above the cutout threshold as opaque.
Peak alpha is below 0.5 and average coverage below 0.2. A neutral receiver albedo
is attenuated, preventing large solid white discs under strong illumination.
Other particle types keep their existing material behavior.

## Reconstruction and motion continuity

Image-binding caches are invalidated before resized Vulkan images are destroyed.
Reused Vulkan handles cannot bypass descriptor refresh after a resolution change.
Motion blur samples the reconstructed full-resolution image with hardware linear
filtering. Foreground velocity expands across nearby silhouettes and the final
gather weights actual coverage, rather than rejecting nearly matching velocities.
Subpixel motion fades in smoothly; motion history tolerates longer frame intervals
independently of reconstruction history. Radius follows output resolution.

Living-entity primitives propagate an eligibility marker through the material
guide and optical highlight selection. Their visible emission is preserved,
but diffraction and defocused diffraction omit tagged sources. Other optical
effects retain their normal source selection.

## Visual and technical reference

## Camera, photo mode and post-processing

The aperture selector uses f/1.4, f/2, f/2.8, f/4, f/5.6, f/8, f/11,
f/16 and f/22. The default is f/1.4; exposure remains independent of aperture.
Physical defocus is the default. It derives focal length from the projection
and a 36 mm sensor width, reconstructs axial scene depth in camera-relative
metres, and evaluates the signed thin-lens circle of confusion. A normalized
64–384-tap disc gather weights each source's aperture coverage and footprint area
in scene-linear HDR after reconstruction and motion blur, before tonemapping.
Foreground support can extend over a sharper background. Background support
is bounded at sharper foreground receivers. No sharp/blur layer masks are used.
The footprint is bounded to 96 output pixels for predictable cost; hidden
background geometry is unavailable to a single-depth screen-space gather.
CoC magnitudes are interpolated without cancelling opposite foreground and
background signs. Receiver-sized support and a sampling-footprint prefilter
regularize sparse aperture integration. Depth-order support is continuous rather
than switching source footprints across a hard foreground/background comparison.
Gaussian is the alternative defocus mode.
First-person ownership is carried from captured primitives into the guide image;
hands and held items are excluded from focus metering and both defocus modes.
Other first-person player geometry is omitted from all ray types.

Optical diffraction uses eight rays rotated 22.5 degrees. The measured source
footprint and exposed intensity determine its extent and transverse smoothing.
Its radial envelope fades continuously toward zero. Visible living emission
and the lunar disc do not excite diffraction. Lunar exclusion covers the swept
current-to-previous projection, including reconstruction trails over newly
visible geometry. Anamorphic streaks may activate
at night, with a higher exposed and absolute luminance threshold than daytime.
Cinematic Flare Intensity controls the classic glare and ghost pattern;
zero disables it and 1.00 corresponds to the former 0.02 intensity. Chromatic
aberration, distortion, vignette and film grain have independent controls.
Motion Blur Intensity independently scales shutter integration from zero to
twice its nominal length; its default is 1.00.

Photo Path Bounces uses the gameplay path-bounce count and defaults to eight.
Cloud, light and fog strengths follow gameplay; photo switches default on and
remain independent. Panel footers follow occupied controls at all three sizes.
Photo transitions retain terrain geometry and the material epoch when the
capacity and resource atlas are unchanged. Genuine world/resource changes
still invalidate their dependent data. First-person hand geometry is visible
to primary rays only; it cannot cast secondary-ray shadows or illuminate the
surrounding scene through held-item analytic lights.

Volumetric Fog Intensity controls both local droplet density and finite-distance
Rayleigh/Mie haze. Aerial extinction, scattering and the LOD boundary fade share
the same strength. The froxel and fallback march read the same air coefficients;
zero fog strength removes that fog medium even at noon. Volumetric-light shaft density remains
independent, and End haze uses the same fog-strength control.

## Overworld aurora and rainbows

The Night Aurora switch enables a layered green/purple noise-ridge aurora in
clear Overworld nights. Moonlight reduces its radiance and a soft luminance cap
keeps dark-scene exposure from making it dominate the sky. Low solar
elevation after rain exposes an anti-solar rainbow, with red on its outer edge
and violet on its inner edge. The sky wetness history is independent of the
wet-ground switch and is frozen consistently during tiled photo capture.
These radiance terms share the environment evaluator used by sky misses and
reflections; existing volumetric transport can occlude them. The effects are
independent adaptations of the supplied algorithms, not bundled Complementary
shader source or texture assets.

Bliss Stable's `shaders/lib/end_fog.glsl` and `overworld_fog.glsl` were inspected
for the visual organization of swirl, erosion and layered height fog:
https://github.com/X0nk/Bliss-Shader/tree/Stable

The Bliss license states all rights reserved. Its shader code and assets are
not bundled or directly ported. The procedural field and integration adapters
here are independently authored. Aperture spectral fitting references remain
in `tools/bake_optics_psf.py` and the generated PSF metadata.
