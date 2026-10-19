# Building Caustica Enhanced

[简体中文](BUILDING.zh-CN.md) · [Technical report](TECHNICAL_REPORT.md) · [Showcase](SHOWCASE.md)

This repository holds **source code, shaders, small resources and tooling**. It deliberately does **not** contain vendor
SDKs, third-party mod JARs, very large data files or release JARs. This page lists exactly what you must supply, where each
item goes, and how to build.

> Status: the maintained workspace builds this source tree with exit code 0, 66 Java test suites / 231 tests (2 skipped)
> and 56 validated SPIR-V modules ([VERIFICATION.md](VERIFICATION.md)). This exact build has not been run on a GPU or inside the
> game. A successful build proves that the code compiles and its unit tests pass — not that the renderer looks or performs correctly.

## 1. Repository layout

| Path | Contents |
| --- | --- |
| `mod/` | **Gradle root.** `build.gradle`, `src/main/java`, `src/test/java`, `shaders/` (Slang), `native/` (C++ bridges + GPU smoke tests), `resources/` and `src/main/resources/`, `tools/` (Python asset bakers), `docs/` (developer notes) |
| `docs/` | Technical report, showcase, this page |
| `devtools/` | Validation harness, helper scripts, local build agent (Windows) |
| `scripts/` | `build.ps1` — offline build wrapper for the maintainer workspace |
| `toolchain/` | *Not in the repo.* Local SDK folder (see §3) |
| `reference/` | *Not in the repo.* Pinned reference payloads (see §3.6) |

## 2. Host requirements

| Item | Requirement |
| --- | --- |
| OS | **Windows x64** for a complete build (the Vulkan reconstruction bridge with XeSS / FSR / NRD is built for Windows x64 only). `build.gradle` also contains a Linux x64 path for the NGX shim, but the full feature set is only built on Windows. |
| JDK | JDK **25 or newer** (`sourceCompatibility = 25`). The maintainer workspace uses JDK 26.0.2. |
| Gradle | The wrapper pins **Gradle 9.5.0** and downloads it on first use. Fabric Loom 1.17.21, Minecraft 26.2, Fabric Loader 0.19.5, Fabric API 0.153.0+26.2 (see `mod/gradle.properties`) |
| Vulkan SDK | `VULKAN_SDK` must point at an SDK that provides `slangc` and `spirv-val` (or both must be on `PATH`). Shaders are written in Slang and compiled to SPIR-V at build time; `spirv-val --target-env vulkan1.2` validates every module |
| C++ | CMake and an MSVC command-line environment (the build uses the `NMake Makefiles` generator), C++17 |
| NVIDIA DLSS SDK | `DLSS_SDK` environment variable (see §3.2) |
| Network | The first build downloads Minecraft, mappings, Fabric and NightConfig through Gradle. The maintainer workspace afterwards builds with `--offline` from a populated Gradle home |
| Python | Only for the optional asset tools in §6: Python 3.14 (`mod/pyproject.toml`) with NumPy, OpenColorIO, OpenEXR; the starmap decoder needs `zstandard` |

## 3. What you must supply

### 3.1 Groovy build sources

`mod/buildSrc/src/main/groovy/dev/comfyfluffy/caustica/build/` contains three Groovy classes imported by `build.gradle`:
`CompileShaderWork.groovy`, `GenerateRtBindings.groovy`, `GenerateShaderRecords.groovy`. See
`_COPY_GROOVY_FILES_HERE.txt` in that folder if they are missing from your checkout; `build.gradle` cannot configure
without them.

### 3.2 NVIDIA DLSS / NGX SDK (`DLSS_SDK`)

Download the DLSS SDK from NVIDIA under NVIDIA's licence and set `DLSS_SDK` to its root. The build copies the DLSS runtimes
from `lib/Windows_x86_64/<rel|dev>/` (`nvngx_dlss.dll`, `nvngx_dlssd.dll`, `nvngx_dlssg.dll`) into the JAR and builds the
small NGX shim (`mod/native/ngx_shim`) with CMake. `-PngxVendorConfig=rel|dev` selects the runtime flavour (default `rel`,
`dev` for `runClient`); `-PngxShimConfig=release|debug` selects the shim configuration; `-PngxPlatforms=windows-x64` (or
`linux-x64`, or both, comma-separated) selects the platforms.

### 3.3 Reconstruction SDKs (`toolchain/`)

By default the native reconstruction bridge (`mod/native/reconstruction`) looks in `../toolchain` relative to `mod/`
(override with `-PreconstructionSdkRoot=<dir>`):

| Path under the SDK root | What it is |
| --- | --- |
| `xess-3.0.2/` | Intel XeSS SDK 3.0.2: `inc/`, `lib/libxess.lib`, `bin/libxess.dll`, `libxess_fg.dll`, `libxell.dll` |
| `fsr-vulkan/` | AMD FidelityFX SDK 1.1.4 `ffx-api` Vulkan backend: `ffx-api/include`, `ffx-api/bin/amd_fidelityfx_vk.lib` and `.dll`. (FSR's newer ML/DX12 runtime is **not** a substitute.) |
| `NRD/` | NVIDIA NRD 4.17.3: `Include/`, `Integration/`, `_Bin/NRD.lib`, `NRD.dll`, `NRI.lib`, `NRI.dll` |
| `NRD-build/_deps/nri-src/` | The NRI sources NRD pins (`Include/`) |

Build NRD with `NRD_NRI=ON`, `NRD_NORMAL_ENCODING=4`, `NRD_ROUGHNESS_ENCODING=1`, `NRD_EMBEDS_DXIL_SHADERS=OFF`,
`NRD_EMBEDS_DXBC_SHADERS=OFF`, `NRI_ENABLE_D3D11_SUPPORT=OFF`, `NRI_ENABLE_D3D12_SUPPORT=OFF`. Details:
[`mod/native/reconstruction/README.md`](../mod/native/reconstruction/README.md). Vendor binaries are bundled unmodified and
their licence texts are embedded in the JAR (`META-INF/licenses`).

### 3.4 Voxy (compile-only)

Place the Voxy **0.2.19-beta (Minecraft 26.2)** JAR at `devtools/dependencies/voxy/voxy-0.2.19-beta.jar`.
Expected SHA-256: `A06E4D93DB88DC22D6CDE6DFE1E58D8428AE271D1F432BBB430735336F4B5C12`. Voxy is *All Rights Reserved* —
it is used only as a compile-time reference and is neither bundled nor redistributable, so this repository does not carry it.

### 3.5 Distant Horizons (compile and test)

Place `DistantHorizons-3.3.3-26.2-fabric-neoforge.jar` at
`toolchain/reference-dh-3.3.3-26.2/DistantHorizons-3.3.3-26.2-fabric-neoforge.jar`, or pass `-PdhJar=<path to jar>`.

### 3.6 Prime star map (regenerated binary)

`mod/src/main/resources/assets/caustica/sky/prime-starmap.bin` (about 179 MB, NASA Deep Star Maps in BC6H) is *generated*, not
stored. Obtain the pinned `prime-starmap-0.1.0.ktx2` from the Prime project (commit and credits in
[`THIRD_PARTY_NOTICES.md`](../mod/THIRD_PARTY_NOTICES.md)), put it at `reference/prime-starmap-0.1.0.ktx2`
(SHA-256 `64bcda4bf9068dae0591bf26f7bd363ec289d3cc95eb528e687a21cc2c355a02`), install `zstandard`
(`pip install --target devtools/dependencies zstandard==0.25.0`) and run:

```powershell
python devtools/decode_prime_starmap.py
```

The script verifies the hash and layout (16384×8192, 15 BC6H mips) and writes the `.bin`. **Do this before building a JAR you want to run:**
`RtStarMap.load` throws `missing star map resource` when the file is absent, so a JAR built without it is not usable in the game.
(Compiling and the unit tests do not need it.)

### 3.7 Photo codec archives (optional)

`caustica/codecs/windows-x64.zip` (ImageMagick 7.1.2-33 portable Q16) and `caustica/codecs/heif-windows-x64.zip`
(MSYS2 libheif 1.23.6 / x265 4.3) are classpath resources under `mod/src/main/resources/`. They provide HEIC / AVIF / JPEG XL
export in offline photography. They are not in this repository. Without them the mod still runs and those three formats report
"unavailable" (PNG, JPEG, TIFF and OpenEXR do not depend on them). **Caveat for the build:** on Windows the unit test
`RtOfflineImageTest.jpegXlLosslessPreservesEverySdrAndHdrSample` opens `windows-x64.zip` from the classpath and fails if it is
missing, which makes `gradlew build` fail at `test`. Either supply the archive or build with `-x test` (e.g. `gradlew build -x test`).

## 4. Build

Set the environment first (PowerShell shown):

```powershell
$env:JAVA_HOME   = 'C:\Program Files\Java\jdk-26.0.2'      # any JDK >= 25
$env:VULKAN_SDK  = 'C:\VulkanSDK\<version>'                # slangc + spirv-val in Bin\
$env:DLSS_SDK    = 'C:\SDKs\DLSS'                          # NVIDIA DLSS SDK root
# CMake and the MSVC environment (vcvars64.bat) must be active in the same shell

cd mod
.\gradlew.bat build
```

Common variants:

| Goal | Command (run in `mod/`) |
| --- | --- |
| Full build (shaders, natives, tests, JAR, sources JAR) | `gradlew build` (add `-x test` if the codec archives of §3.7 are absent) |
| Tests + JAR without recompiling shaders (only when the compiled shaders already match the sources) | `gradlew test jar -x compileShaders -x sourcesJar` |
| Offline build from a populated Gradle home | add `--offline` |
| Run a development client | `gradlew runClient` (see `runClient.ps1`; uses the `dev` DLSS runtime) |

The JAR is written to `mod/build/libs/Caustica Enhanced v.<N>.jar` (`<N>` is the last component of `mod_version`, e.g. `76`)
next to a sources JAR. A full shader compile took roughly 15–25 minutes in the maintainer workspace. **Do not run `gradlew clean`
casually** — it deletes the generated SPIR-V and native build trees.

The JAR is large (about 423 MB) because it bundles the NGX/XeSS/FSR/NRD runtimes, SPIR-V modules and the star map.
Publish it through **GitHub Releases** (up to 2 GiB per asset), not through git history.

### Maintainer workspace wrappers (optional, Windows)

- `scripts/build.ps1 [-Fast] [-JavaHome <jdk>]` loads `toolchain/env.ps1` (a local script *not* in the repo that sets up MSVC,
  CMake, Vulkan SDK, `DLSS_SDK`, an offline Gradle home), then runs `gradlew -p mod build --offline` (`-Fast` = `test jar` without
  shader compilation).
- `devtools/build-release.ps1 -Release <N>` sets `mod_version`, runs the full build and writes a release record folder
  (JAR copy, `SHA256SUMS.txt`, `verification.json`, log) under `releases/` in the maintainer workspace.
- `devtools/build-agent/` is a Windows file-queue agent that runs these whitelisted actions (see its README).
- `devtools/BUILD-WORKFLOW.md` records the fast/slow build rules, including how to compile a single shader while editing.

## 5. Tests

- `gradlew test` runs the JUnit 5 suites in `mod/src/test/java` (66 suites / 231 tests, 2 skipped).
- `mod/native/tests/*.ps1` are standalone GPU / maths smoke tests (cloud maths, cache, emitter sampling, focus, LOD, motion …) that
  compile a Slang kernel and run it on a Vulkan device. They need a GPU and were **not** part of the build record.
- [`VERIFICATION.md`](VERIFICATION.md) records what the build verified and what it does not establish.
- `devtools/` holds a synthetic-world validation and performance-capture harness. It was written for an earlier renderer that still had a
  ReSTIR GI mode and references it in places; treat it as a starting point, not a maintained gate.

## 6. Regenerating baked assets

| Asset | Tool | Notes |
| --- | --- | --- |
| ACES 2.0 display LUTs + packaged LMT | `mod/tools/bake_display_lut.py` | OCIO config `cg-config-v4.0.0_aces-v2.0_ocio-v2.5`; one SDR LUT and HDR LUTs for 500 / 1000 / 2000 / 4000 nit |
| Aperture PSF | `mod/tools/bake_optics_psf.py` | Linear, unit-energy spectral PSF |
| Cloud noise pack | `mod/tools/pack_radiance_noise.py` | From `mod/tools/radiance-noise-source/` (attribution in its `NOTICE.md`) |
| Star map | `devtools/decode_prime_starmap.py` | §3.6 |

The Python environment for the first three is described by `mod/pyproject.toml` / `mod/uv.lock` (`uv sync`).

## 7. Continuous integration

`mod/.github/workflows/ci.yml` is inherited from the upstream Caustica project. It only builds the Windows NGX shim (it checks out
`NVIDIA/DLSS` and installs the Vulkan SDK on a hosted runner), and its paths assume the Gradle project is the repository root.
GitHub only runs workflows from `<repo root>/.github/workflows`, so **it does not run for this layout**. To use it, move it to the
repository root and prefix its paths with `mod/`. A full CI build would additionally need the SDKs in §3 and, for the native GPU tests, a GPU —
i.e. a self-hosted Windows runner.

## 8. Licence

GPL-3.0-only for the combined work; original Caustica files keep LGPL-3.0-or-later headers. Third-party components keep their own
terms: [`mod/THIRD_PARTY_NOTICES.md`](../mod/THIRD_PARTY_NOTICES.md), [`LICENSE`](../LICENSE).
