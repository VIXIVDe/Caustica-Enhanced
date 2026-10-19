# Caustica Enhanced

### Vulkan hardware path tracing for Minecraft 26.2

> Give the block world real light: sun, moon, torches, clouds, rain, fog and water all light each other by physical rules.
> Client-side mod · Fabric · GPL-3.0-only

[简体中文](SHOWCASE.zh-CN.md) · [Technical report](TECHNICAL_REPORT.md) · [Building](BUILDING.md)

---

## In one minute

Caustica Enhanced replaces Minecraft 26.2's world renderer. It traces real light paths with Vulkan ray-tracing hardware, then uses NVIDIA DLSS Ray Reconstruction (or NRD ReBLUR with DLSS / FSR / XeSS upscaling) to turn one sample per pixel into a clean image. You keep the vanilla interface, vanilla blocks and your resource packs — only the light changes.

It builds on the open-source Caustica and Caustica-RTX and adds a whole set of systems that make a world feel like a world: weather, volumetric clouds and light, the End, aurora, distant terrain, camera optics, HDR and an offline photography mode that renders up to 8K.

---

## What you get

**Real indirect light and reflections.** Primary rays and multiple bounces are traced per pixel — diffuse, glossy reflection and transmission together. Glass, ice and water are refractive volumes with an index of refraction, not textures.

**Smart sampling for lots of lights.** Always-on RIS emitter sampling (at least 8 candidates), plus optional **ReSTIR DI** (many small lights, such as a row of torches) and **ReSTIR PT Enhanced** (full-path resampling). Choosing DI also selects the SHARC indirect cache.

**A sky and weather that breathe.** Hillaire atmospheric scattering, physically sized sun and moon, NASA star maps, night aurora, post-rain rainbows; Radiance volumetric clouds (casting shadows, optionally part of ray traversal), froxel volumetric light, fog that follows weather and time, wet ground that pools, refractive rain; the End has its own violet volumetric beams and vortex.

**Light in your hands is real light.** A light source in each hand (torch, lava bucket, glowstone …) lights its surroundings and casts true shadows.

**PBR and relief that pops.** LabPBR resource packs and a bounded height-field parallax; packs can override a material's emission, refractive index and dispersion with a small JSON file.

**Water.** Three modes (Performance / Balanced / Quality); Quality is a 32-component directional wave spectrum whose caustics come from the same field as the visible ripples.

**See far.** Voxy and Distant Horizons terrain is converted into traceable geometry and takes part in reflections and lighting.

**Camera control like a photographer.** Physical depth of field from f/1.4 to f/22, motion blur, eight-sided aperture diffraction stars, lens flare and prism leak, film grain; exposure measured in real cd/m² and EV100; **ACES 2.0** output with **HDR (PQ, 500–4000 nit)**; three looks: Vanilla / GTA VI / Kodak 2383 Inspired.

**Frame generation.** DLSS, FSR and XeSS providers (2×–4×; 3×/4× multi-frame generation needs RTX 50), plus NVIDIA Reflex.

**Offline photography.** Press `Y` for a panel; tiled accumulation up to **7680 × 7680** px, output as PNG / JPEG / TIFF / OpenEXR / HEIC / AVIF / JPEG XL with full capture metadata; HDR and EXR exports automatically get an SDR companion.

---

## How it compares

The short answer: **there is no one-size-fits-all choice.** These projects solve different problems on different platforms and GPUs. The tables list only what each project says in its **own public description**; "not listed" means the page does not mention it — it does not mean the project lacks it.

### A. Comparable Vulkan hardware ray-tracing mods

| | **Caustica Enhanced** | Caustica-RTX | Radiance |
| --- | --- | --- | --- |
| Minecraft versions | 26.2 (Fabric) | 26.2 (Fabric) | 1.20.1 / 1.21.1 / 1.21.4 (Fabric, Forge, NeoForge); 26.x port in progress, no builds yet |
| Rendering | Vulkan hardware path tracing | Vulkan hardware path tracing | Vulkan hardware ray tracing |
| DLSS Ray Reconstruction | ✅ | ✅ | ✅ |
| Non-NVIDIA route | ✅ NRD ReBLUR + FSR | to-do (unchecked in README) | ✅ NRD + FSR |
| Frame generation | DLSS / FSR / XeSS, 2×–4× | DLSS FG, RTX 50 multi-frame up to 4× (experimental) | DLSS and FSR frame generation where supported |
| ReSTIR | ✅ DI and PT Enhanced | to-do | not mentioned |
| Clouds / volumetric light / fog / weather | ✅ Radiance clouds, froxel volumetric light, weather fog, rain and wetness, End, aurora, rainbow | to-do | atmosphere, clouds, fog, water, rain-driven wetness |
| Distant terrain | ✅ Voxy and Distant Horizons | to-do | Distant Horizons 3.3.0–3.3.2 (older version lines) |
| Indirect cache | Radiance Cache or SHARC | not listed | not listed |
| HDR output | ✅ ACES 2.0, 500–4000 nit | ✅ | not listed |
| Offline high-resolution photography | ✅ up to 7680 px, many formats + metadata | not listed | not listed |
| Licence | GPL-3.0-only (original Caustica files keep LGPL-3.0+) | LGPL-3.0+ | GPL-3.0 |

*Caustica-RTX is an RTX-oriented fork of Caustica; its README lists ReSTIR, End sky, weather, volumetric fog/clouds, NRD + FSR and LOD as not-yet-done to-dos, whereas those parts are implemented in Caustica Enhanced's source. Radiance's strength is its **wider version range** (1.20.1–1.21.4, several loaders).*

### B. Other routes: shader packs and Bedrock

| | Platform | Approach | One-line positioning |
| --- | --- | --- | --- |
| **Rethinking Voxels** | Java, Iris shader pack (1.19.2+) | Voxelisation + coloured lights with ray-traced shadows (an edited Complementary Reimagined) | Low barrier, vanilla-leaning look, no Vulkan RT mod needed |
| **SEUS PTGI** | Java, shader pack | Software path-traced global illumination, no RT cores needed | Path-traced GI without RT cores |
| **Minecraft RTX** | Bedrock (official) | Official path tracing + DLSS | Official and turnkey, but **Bedrock only** |
| **BetterRTX** | Bedrock (community) | Edits the official RTX shaders: physical sky, water parallax, puddles, caustics, depth of field, motion blur … | For staying on Bedrock RTX and improving it |

### Is it for you?

- ✅ You play **Java 26.2**, your GPU supports Vulkan ray tracing (NVIDIA gets the full DLSS suite; non-NVIDIA uses NRD + FSR), you want **near-offline-quality global lighting** and accept the performance cost: choose **Caustica Enhanced**.
- ✅ You want **multi-version, multi-loader** hardware ray tracing: look at **Radiance**.
- ✅ You have no ray-tracing hardware, or want something light and vanilla-leaning: **Rethinking Voxels** or another shader pack fits better.
- ✅ You play Bedrock: **Minecraft RTX** (+ BetterRTX).

---

## Requirements

| Item | Requirement |
| --- | --- |
| Game | Minecraft **26.2** (Java), Fabric Loader ≥ 0.19.5, Fabric API, **Java 25** |
| Graphics | The **Vulkan** backend; GPU and driver must support Vulkan ray tracing (acceleration structures, ray-tracing pipeline, ray queries, position fetch …) |
| DLSS / Ray Reconstruction | NVIDIA RTX GPU and a supported driver |
| Multi-frame generation (3×/4×) | RTX 50 series |
| Non-NVIDIA | NRD ReBLUR + FSR route (XeSS upscaling is offered on NVIDIA devices only) |
| OS | The bundled native reconstruction library is **Windows x64** (the NGX shim also has a Linux build script) |
| VRAM | Ray tracing itself is memory-hungry; ReSTIR PT Enhanced needs about 736 bytes per internal pixel (about 1.42 GiB at 1920×1080, plus other buffers) |
| Optional | **Voxy 0.2.19-beta** (with Sodium) or **Distant Horizons ≥ 3.3.3** for distant terrain; HDR needs an HDR display and OS HDR mode |

> RTX 20/30: SER, OMM and DLSS frame generation are off by default; DLSS Ray Reconstruction still works, and FSR / XeSS frame generation remain available.

## Installation

1. Set up Minecraft 26.2 with Fabric Loader and Fabric API, and select the **Vulkan** graphics backend in video settings.
2. Put the built Caustica Enhanced JAR into `mods` (**only one Caustica JAR**). Pre-built JARs come from the repository's Releases; to build it yourself see [BUILDING.md](BUILDING.md).
3. For distant terrain, also install Voxy 0.2.19-beta (and its Sodium dependency) or Distant Horizons ≥ 3.3.3.
4. On first world entry the driver compiles the ray-tracing pipeline and a "Preparing shaders / Compiling world pipeline" progress panel appears; vanilla rendering stays available meanwhile and the result is cached for faster later launches.
5. Settings live on the **Caustica Enhanced** page in video settings. Mod data (config, caches, exports) is in a `Caustica Enhanced/` folder inside your game directory.

## FAQ

**Do I need an RTX card?** You need a GPU with Vulkan ray-tracing support. DLSS features need NVIDIA RTX; non-NVIDIA GPUs use the NRD ReBLUR + FSR route.

**Will it be heavy?** Path tracing is heavy by nature. The project offers cost-saving options (Performance water, PT stages compiled on demand, DLSS/FSR/XeSS upscaling, frame generation), but **we publish no frame-rate numbers** — judge by your own machine.

**Can I combine it with a shader pack?** No. It replaces the world renderer wholesale.

**Why are some distant areas empty?** Distant terrain comes from Voxy / Distant Horizons, which supply only **visited or generated** terrain; this mod cannot make unknown chunks appear.

**How do I enable HDR?** Turn on HDR in the OS, then enable it on the *HDR Display* page; peak brightness can be 500 / 1000 / 2000 / 4000 nit.

## Honest status and limits

We would rather say this up front:

- **This source tree builds completely and passes 66 test suites / 231 Java unit tests; shaders were compiled and validated offline. This exact build has not been run on a GPU or in the game.** The documents describe behaviour the source **implements**, not image quality or performance "proven on your machine".
- Multi-frame-generation presentation is still experimental; frame generation does **not** lower shading cost or input latency.
- Parallax is a bounded height field with no real displaced geometry; distant terrain is a voxel approximation without near-field plant animation.
- ReSTIR PT uses a lot of VRAM; cache reuse is approximate; froxel resolution is finite.
- The looks (GTA VI / Kodak 2383) are **artistic inspiration**, not licensed or measured film/engine replicas, and are unrelated to any company.
- **26.2 only**; not Bedrock.

## Credits and licence

Caustica Enhanced is released under **GPL-3.0-only** (original Caustica files keep their LGPL-3.0-or-later notices) and contains or follows code and algorithms from the projects below; their licences and credits are in [THIRD_PARTY_NOTICES.md](../mod/THIRD_PARTY_NOTICES.md): Caustica (ComfyFluffy), Caustica-RTX (AriesAlex), Radiance / MCVR / Shaderpack-Advanced, Prime PT, NVIDIA DLSS / NRD / NRI / SHARC / STBN, Intel XeSS, AMD FidelityFX, NASA Deep Star Maps. Voxy is not bundled.

---

### Sources for the comparison (accessed 18 Oct 2026; may have changed)

- Caustica-RTX README — <https://github.com/AriesAlex/Caustica-RTX>
- Radiance README — <https://github.com/Minecraft-Radiance/Radiance>
- Rethinking Voxels README — <https://github.com/gri573/rethinking-voxels>
- SEUS PTGI overview — PCGamesN, <https://www.pcgamesn.com/minecraft/sonic-ether-shader>
- Minecraft RTX release notes — NVIDIA, <https://www.nvidia.com/en-us/geforce/news/minecraft-rtx-dlss-official-release/>
- BetterRTX — <https://github.com/BetterRTX>

Descriptions of other projects rely only on the pages above; "not listed" means the page does not mention a capability, not that the project lacks it. Trademarks belong to their owners.
