# Caustica Enhanced

**Vulkan hardware path tracing for Minecraft 26.2 (Fabric).**
Real light for the block world: sun, moon, torches, clouds, rain, fog and water all light each other by physical rules.

<img width="3840" height="2160" alt="Minecraft Vice City" src="https://github.com/user-attachments/assets/5b6a595a-c87c-427c-8fdf-9ab64fcbab44" />

[简体中文](README.zh-CN.md) · [Showcase & comparison](docs/SHOWCASE.md) · [Technical report](docs/TECHNICAL_REPORT.md) · [Building](docs/BUILDING.md)

| | |
| --- | --- |
| Game | Minecraft **26.2**, Fabric Loader ≥ 0.19.5, Fabric API, Java 25+ |
| Renderer | Vulkan hardware ray tracing (acceleration structures, ray-tracing pipeline, ray queries) |
| Licence | GPL-3.0-only (original Caustica files keep LGPL-3.0-or-later notices) |

> **Honest status.** This source tree builds completely and passes 66 test suites / 231 Java unit tests; its shaders were compiled and
> validated offline. **This exact build has not been run on a GPU or inside the game.** The documents describe what the source implements — they
> make no claim about image quality or frame rate on your machine. See [Status and limits](#status-and-limits).

## What it is

Caustica Enhanced replaces Minecraft's world renderer with a ray tracer. It traces primary rays and multiple bounces per pixel,
then turns the noisy result into a clean image with **NVIDIA DLSS Ray Reconstruction**, or with **NRD ReBLUR plus DLSS / FSR /
XeSS upscaling**. The interface, blocks and resource packs stay vanilla; only the lighting changes.

It builds on the open-source [Caustica](https://github.com/ComfyFluffy/Caustica) (ComfyFluffy) and
[Caustica-RTX](https://github.com/AriesAlex/Caustica-RTX) (AriesAlex), with algorithms and assets from Radiance / MCVR, Prime PT and others
(see [`mod/THIRD_PARTY_NOTICES.md`](mod/THIRD_PARTY_NOTICES.md)).

## Highlights

- **Light transport** — traced diffuse, glossy reflection and transmission; glass, ice and water are refractive volumes. Always-on RIS
  emitter sampling, optional **ReSTIR DI** (many small lights) and **ReSTIR PT Enhanced** (full-path resampling).
- **Sky and weather** — Hillaire atmospheric scattering, physically sized sun and moon, NASA star maps, aurora, rainbows, Radiance
  volumetric clouds, froxel volumetric light, weather-driven fog, wet ground, refractive rain, a violet volumetric End.
- **Light in your hands** — a real light source in each hand (torch, lava bucket, glowstone …) with true shadows.
- **Materials** — LabPBR resource packs, bounded height-field parallax, per-pack JSON overrides for emission, refractive index and dispersion.
- **Water** — Performance / Balanced / Quality modes; Quality is a 32-component wave spectrum whose caustics derive from the visible ripples.
- **Distant terrain** — Voxy and Distant Horizons terrain converted into traceable geometry.
- **Camera** — physical depth of field (f/1.4–f/22), motion blur, aperture diffraction, lens flare, grain; exposure in cd/m² / EV100.
- **Display** — ACES 2.0 output, SDR and **HDR (PQ, 500–4000 nit)**, three looks (Vanilla / GTA VI / Kodak 2383 Inspired).
- **Frame generation** — DLSS, FSR and XeSS providers (2×–4×; 3×/4× needs RTX 50) with NVIDIA Reflex.
- **Offline photography** — tiled accumulation up to 7680 × 7680 px; PNG / JPEG / TIFF / OpenEXR / HEIC / AVIF / JPEG XL with capture metadata.

The full, source-verified feature description is the [technical report](docs/TECHNICAL_REPORT.md) (28 sections, implemented features only).
How the project compares with Caustica-RTX, Radiance, Rethinking Voxels, SEUS PTGI, Minecraft RTX and BetterRTX is in the
[showcase](docs/SHOWCASE.md).

## Requirements

- A GPU and driver with Vulkan ray-tracing support. NVIDIA RTX gets DLSS Ray Reconstruction and DLSS upscaling; other vendors use the NRD ReBLUR + FSR route.
- Windows x64 (the bundled native reconstruction library is Windows x64).
- The **Vulkan** graphics backend selected in Minecraft's video settings.
- VRAM: path tracing is memory-hungry; ReSTIR PT Enhanced alone needs about 736 bytes per internal pixel (≈ 1.42 GiB at 1920×1080).
- Optional: Voxy 0.2.19-beta (with Sodium) or Distant Horizons ≥ 3.3.3 for distant terrain; an HDR display for HDR output.

## Install

1. Set up Minecraft 26.2 with Fabric Loader and Fabric API; choose the **Vulkan** backend in video settings.
2. Put the built Caustica Enhanced JAR into `mods` (only one Caustica JAR). Built JARs belong under this repository's **Releases** (a JAR is ~400 MB, so it is not stored in git);
   to build your own see [docs/BUILDING.md](docs/BUILDING.md).
3. On first world entry the driver compiles the ray-tracing pipeline and a progress panel is shown; the result is cached.
4. Settings are on the **Caustica Enhanced** page in video settings. Config, caches and exports live in a `Caustica Enhanced/` folder
   inside the game directory.

## Documentation

| Document | Purpose |
| --- | --- |
| [docs/TECHNICAL_REPORT.md](docs/TECHNICAL_REPORT.md) · [简体中文](docs/TECHNICAL_REPORT.zh-CN.md) | What the renderer implements, in detail (no roadmap) |
| [docs/SHOWCASE.md](docs/SHOWCASE.md) · [简体中文](docs/SHOWCASE.zh-CN.md) | User-facing overview and comparison with other projects |
| [docs/BUILDING.md](docs/BUILDING.md) · [简体中文](docs/BUILDING.zh-CN.md) | Toolchain, what is not in the repo, build commands |
| [mod/THIRD_PARTY_NOTICES.md](mod/THIRD_PARTY_NOTICES.md) | Third-party code, algorithms, SDKs and licence boundaries |
| [mod/docs/](mod/docs) | Developer notes: release validation, offline photography, performance capture, Voxy compatibility, … |
| [docs/VERIFICATION.md](docs/VERIFICATION.md) · [简体中文](docs/VERIFICATION.zh-CN.md) | What the build verified (and what it does not establish) |

## Repository layout

```
Caustica-Enhanced/
├── mod/        Gradle root: Java sources, Slang shaders, C++ bridges, resources, Python asset tools
├── docs/       Technical report, showcase, build guide
├── devtools/   Validation harness, helper scripts, local build agent (Windows)
└── scripts/    Offline build wrapper for the maintainer workspace
```

Vendor SDKs, the Voxy/Distant Horizons JARs, the star-map binary, the photo-codec archives and release JARs are intentionally **not**
in the repository; [docs/BUILDING.md](docs/BUILDING.md) says where each comes from.

## Status and limits

- This build was only compiled and unit-tested: no GPU run, no in-game run, no published performance numbers.
- Frame generation raises presented frames, not simulation or tracing speed; multi-frame presentation is still experimental.
- Parallax is a bounded height field, not displaced geometry. Distant terrain is limited to what Voxy / Distant Horizons provide.
- ReSTIR PT needs a lot of VRAM; reuse is approximate; froxel resolution is finite.
- The GTA VI and Kodak 2383 looks are artistic interpretations, not licensed or measured replicas.
- Minecraft **26.2 Java only**; not Bedrock.

## Licence

The combined work is **GPL-3.0-only** ([`LICENSE`](LICENSE)); original Caustica files retain their LGPL-3.0-or-later notices
([`mod/LICENSE.md`](mod/LICENSE.md), [`mod/COPYING.LESSER`](mod/COPYING.LESSER), [`mod/MCVR-LICENSE.md`](mod/MCVR-LICENSE.md)).
Third-party components keep their own terms. NVIDIA, Intel, AMD, Minecraft and other names belong to their owners; this project is
not affiliated with or endorsed by them.
