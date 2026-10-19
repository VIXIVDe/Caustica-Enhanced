# Fast build & iteration workflow (maintainer workspace, Windows)

Workspace root = the directory that contains `mod/`, `devtools/`, `scripts/` and a local `toolchain/`. Everything below runs through `toolchain\env.ps1`
(a local script, not in the repository: MSVC, SDKs, Slang, Vulkan, DLSS_SDK, offline Gradle) with JDK 26 (the maintained build used 26.0.2).
Never use a random global Gradle/JDK. **Never `clean`** — it throws away generated shaders and native builds.

| Situation | Command (via build agent request) | Typical time |
| --- | --- | --- |
| Java/UI-only change, existing `.spv` match the sources | `{"action":"fast"}` = `scripts\build.ps1 -Fast` (`test jar -x compileShaders -x sourcesJar`) | minutes |
| Any `.slang` change | `{"action":"build"}` or `{"action":"release","release":N}` (runs `compileShaders`) | ~25 min today |
| Syntax/interface check of one shader while editing | compile that single stage file with the Gradle flags below into `devtools\work\`, then `spirv-val` | seconds |
| Release package | `{"action":"release","release":N}` — wait for `BUILD SUCCESSFUL` before copying/hashing | |

Single-shader flags (must match `build.gradle`):
`slangc <file> -target spirv -profile spirv_1_5 -matrix-layout-column-major -warnings-as-errors all -warnings-disable 41012 -g`
plus `-I` for the file's folder and every folder that contains a `.slang` file; then
`spirv-val --target-env vulkan1.2 <out.spv>`. Variants add `-O3 -g1` (restir_pt_*, closest_hit) or
`-D...`/`-capability ...` (indirect.rgen). Manual compiles only locate errors; the final JAR always comes from Gradle.

Rules that save time and avoid corruption
- Do not hand-edit `.spv`, generated shader records or RT bindings; push-data/layout/binding changes must re-run
  `generateShaderRecords` / `generateRtBindings` (automatic in the Java dependency chain) and the Java side must be checked too.
- Keep the first `slangc` command and diagnostic when a shader fails; never relax warnings-as-errors or skip `spirv-val`.
- The JAR is ~420–440 MB: wait for `BUILD SUCCESSFUL` before opening/copying it (concurrent reads break NestJarsAction).
- One build at a time (workspace mutex). Poll `results\<id>\status.json`; the heartbeat is `agent.json`.
- Plan the order: do the quick Java build first to catch compile errors, then the long shader build once.
