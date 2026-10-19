# devtools

Maintainer tooling for Caustica Enhanced. Most of it targets the author's Windows workspace and is published for transparency and
reuse, not as a turnkey developer experience. For building the mod see [`../docs/BUILDING.md`](../docs/BUILDING.md).

## Contents

| Item | Purpose |
| --- | --- |
| `build-agent/` | Windows file-queue agent that runs whitelisted build actions (`build`, `fast`, `release`, `test`, …) from request files. See its [README](build-agent/README.md). Start it by hand with `START-AGENT.cmd`; it does not autostart. |
| `build-release.ps1` | Sets `mod_version`, runs the full offline build and writes a release record folder under `releases/` in the maintainer workspace (JAR copy, `SHA256SUMS.txt`, `verification.json`, log). |
| `BUILD-WORKFLOW.md` | Fast vs. full build rules, compiling a single shader while editing. |
| `decode_prime_starmap.py` | Verifies the pinned Prime KTX2 and unpacks it to `prime-starmap.bin` (needs `reference/prime-starmap-0.1.0.ktx2` and `zstandard`; see [BUILDING.md §3.6](../docs/BUILDING.md)). |
| `setup_validation.py`, `check_signals.py`, `exr_reader.py` | Synthetic-world validation harness: prepares a copy of a fixture, launches it, then checks that raw/reconstructed signals are finite. |
| `run_profile.py`, `summarize_performance.py`, `combine_performance.py`, `check_profile_names.py` | Performance-capture scene matrix and summaries (see [`../mod/docs/performance-capture.md`](../mod/docs/performance-capture.md)). |
| `build_transport_diagnostics.py`, `run_transport_comparison.py`, `summarize_transport*.py`, `test_transport_helpers.py` | Transport-comparison diagnostics. |
| `templates/` | Helper-mod sources and the runtime manifest used by the validation harness (`ValidationClient`, `PerformanceClient`, probes, mixins). |

## Status of the validation harness

The harness was written for an earlier renderer that still had a ReSTIR GI mode, which is no longer part of the renderer. As a result:

- `templates/ValidationProbe.java` still reads a `restirGi` field, and `setup_validation.py` still looks for a `gi_probe` shader that was
  absent from this repository together with the GI sources — both need adapting before the harness runs against the current renderer;
- `templates/runtime.json` pins dependency JARs from a local Gradle cache and has no Minecraft assets path: pass `--assets <Minecraft assets directory>`;
- it needs a built JAR, the local `toolchain/`, a fixture world (not in this repository) and a GPU.

Nothing in the [build record](../docs/VERIFICATION.md) depends on it. Treat it as a starting point.

## Usage sketch (maintainer workspace)

```powershell
. ./toolchain/env.ps1
python ./devtools/setup_validation.py --repo ./mod --jar "./mod/build/libs/<built JAR>" --assets "<assets dir>" --compile
python ./devtools/check_signals.py ./devtools/work/current/instance/signals-locked --expected 10
```

`--repo`, `--toolchain`, `--assets` and `--output` select explicit paths; use a fresh `--output` for each run (setup refuses to overwrite).
Python 3 with NumPy is required. Results land under `devtools/work/`, which is git-ignored.

`exr_reader.py` supports the renderer's uncompressed scanline RGBA half-float exports. Measurements produced by these tools are diagnostic
results, not controlled FPS benchmarks or image-quality proofs.
