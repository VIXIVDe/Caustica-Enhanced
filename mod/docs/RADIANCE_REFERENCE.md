# Radiance references and implementation scope

Radiance-derived components retain their upstream notices and GPL license. See THIRD_PARTY_NOTICES.md and MCVR-LICENSE.md for source commits, dependencies and licensing.

## Volumetric lighting

The Default / Radiance selector preserves the existing camera ray-march method in Default mode. Radiance mode adapts the froxel mapping and integration structure from [Shaderpack-Advanced, commit bf26252](https://github.com/Minecraft-Radiance/Shaderpack-Advanced/tree/bf26252f952d75398edd66ca9db9c5e31c9e618f/volume).

- Direct lighting: 256 × 128 × 64 camera grid, world visibility queries and the current celestial spectrum.
- Indirect lighting: 128 × 64 × 32 grid, phase-function samples of sky and celestial-lit diffuse surfaces with two surface bounces. Artificial surface emitters are excluded from this atmospheric signal.
- Nonlinear slices cover 50 blocks. Checkerboard updates, reprojected history, spatial filtering and analytic segment integration reduce repeated work.
- History limits are 16 samples for direct lighting and 64 for indirect lighting. Camera discontinuities, world, medium and lighting changes invalidate unsuitable history.
- The cumulative integral is sampled at visible surface depth. Existing water absorption remains separate to avoid applying it twice.

This adapter uses Caustica's Slang shaders, emitter tables, scene-linear ACEScg signals and Vulkan scheduling. It allocates approximately 136 MiB for volume grids while active. Beyond the grid range it uses a constant-medium continuation approximation. Transparent hits terminate the diffuse indirect probe. It does not reproduce every Radiance feature or claim matching appearance or performance.

## Clouds

The cloud selector contains Off / Vanilla / Radiance. Legacy Volumetric values migrate to Radiance.

Radiance clouds have separate world-shadow and BVH switches. The BVH option inserts a procedural cloud bound and evaluates density during shadow traversal; it does not create an opaque cloud mesh. Camera and reflection cloud rendering, including celestial-disc attenuation, remain independent of the world-shadow switch.

## Delivery status

The maintained validation tools and current small evidence reports are in [devtools](../../devtools/README.md). They cover numerical signal contracts and a synthetic Minecraft 26.2 scene. Matched Radiance image-quality and frame-time comparisons have not been performed; a successful compilation alone does not establish runtime or visual equivalence.
