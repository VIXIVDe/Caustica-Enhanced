# Verification record

[简体中文](VERIFICATION.zh-CN.md) · [Technical report](TECHNICAL_REPORT.md) · [Building](BUILDING.md)

This page states what was checked for this source tree, and what that does and does not establish.

## What was checked

| Check | Result |
| --- | --- |
| Full offline Gradle build (Slang shaders, native bridges, Java, tests, JAR, sources JAR) | Exit code 0; about 22.5 minutes in the maintainer workspace |
| Java unit tests (JUnit 5) | 66 suites, 231 tests: 0 failures, 0 errors, 2 skipped |
| Shader modules | 56 SPIR-V modules compiled by `slangc` and validated with `spirv-val --target-env vulkan1.2` |
| Built JAR | 423,612,915 bytes; SHA-256 `563ccc2072565c583cad6af5ef2960e3bce28749afc24f3e4dae6e520d7109e0` |
| Installed into a game instance | No |
| Run on a GPU / in the game | **No** — this exact build has not been run |

The JAR is not stored in this repository. If you publish it as a GitHub Release asset, this SHA-256 identifies the artifact that was
built and tested. A rebuild from source will not be byte-identical.

## What this establishes

- The source compiles with the documented toolchain, the shaders compile and pass SPIR-V validation, and the unit tests pass.
- The documentation in this repository (the [technical report](TECHNICAL_REPORT.md) in particular) describes behaviour that the source
  implements, checked against the source.

## What it does not establish

- That the renderer produces correct or good-looking images, or that any specific feature works on a given GPU and driver.
- Any frame rate, memory figure or other performance claim. None is published.
- Behaviour on non-NVIDIA hardware, HDR displays, large Voxy / Distant Horizons worlds, offline captures at the largest sizes, or
  3×/4× multi-frame generation. These need dedicated testing on real hardware.
- Anything about other builds or forks.

Earlier development builds were exercised on the maintainer's machine (an RTX 3060 Laptop). Those runs do not transfer to this build.
