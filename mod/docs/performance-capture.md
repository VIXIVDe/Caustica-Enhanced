# Renderer performance capture

Enable `-Dcaustica.rt.gpuTimings=<output.csv>` and optionally
`-Dcaustica.rt.frameStats=true`. Normal rendering does not allocate timestamp
pools, query budgets, or write these diagnostic files.

The graphics timestamp ring is collected only after its graphics-use timeline
value completes. Queries never use `VK_QUERY_RESULT_WAIT_BIT`. Optional passes
carry a written-query mask; absent PT passes are `NaN`, rather than stale timings.

## Signals and units

| CSV fields | Measured work |
| --- | --- |
| `primary_ms` | Camera tracing, material evaluation and primary guide generation |
| `di_temporal_ms` | DI temporal dispatch, when enabled |
| `gi_ms` | Legacy column kept in the CSV layout; ReSTIR GI is not part of the renderer, so ignore it |
| `indirect_ms` | Continuation tracing/cache work, or the complete PT sequence |
| `pt_*_ms` | Initial, temporal, shifts, spatial and resolve dispatches within PT |
| `entity_blas_ms`, `cloud_bvh_ms`, `tlas_ms` | Inline graphics AS work and its required barriers |
| `sky_lut_ms`, `froxel_ms` | Atmosphere LUT updates and the separate froxel pipeline |
| `reconstruction_ms` | Selected reconstruction, including its required transitions |
| `stars_ms`, `exposure_ms`, `bloom_ms`, `display_ms`, `copy_ms` | Output effects, mapping and output copy |
| `graphics_measured_ms` | The entire measured graphics region; excludes presentation and other Minecraft work |
| `cpu_gpu_wait_ms` | Host timeline completion waits between captures |
| `cpu_build_submission_wait_ms` | Host waiting for the build thread to submit its work |
| `cpu_context_wait_ms` | Caustica synchronous fence/device-idle host waits, including lock acquisition |
| `device_heap_usage_bytes`, `device_heap_budget_bytes` | VMA device-local heap usage and budget, with the driver's memory-budget extension when supported |
| `caustica_allocated_bytes` | Live allocations in Caustica's allocator; excludes Minecraft and native reconstruction allocators |

`volume_ms` is the aggregate between DI and indirect tracing, including both
froxel work. `total_ms`, `recorded_ms` and `post_ms` retain their aggregate
meaning. Do not add an aggregate to its own component measurements.

`<output.csv>.build.csv` measures upload/AS batches on the compute queue, read
after the executor's existing completion wait. No additional wait is inserted.
Uploads and builds share a batch; its duration is not pure BLAS time and can
overlap graphics execution. It must not be added to graphics frame duration.

The metadata sidecar records timestamp period, valid bits and the device.
Start/end ticks permit gap analysis. Such gaps contain Minecraft work,
presentation, scheduling and waits; they do not prove that the GPU was idle.
Host wait milliseconds are also not GPU idle milliseconds.

## Fused shader work

Material evaluation and inline cloud/fog cannot be separated with command-buffer
timestamps. POM on/off and cloud on/off captures measure incremental dispatch
costs. With timestamps enabled, `-Dcaustica.rt.profileMaterialBypass=true` bypasses
height, normal and PBR page evaluation while retaining geometry and base albedo.
It is ignored outside diagnostics and has no UI option.

Compare the **primary** pass on a fixed opaque scene for that material ablation.
Its camera ray walk does not sample a BSDF, so it avoids the changed indirect
paths caused by replacing material parameters. The delta remains an estimate:
cache state, compiler execution and memory overlap prevent interpreting it as
exclusive material instruction time. Cutouts, water and glass require a separate
shader-level profile. Nsight Graphics Shader Profiler can attribute samples to
closest-hit/any-hit/miss shaders; the CSV does not replace that analysis.

## Reproducible isolated capture

From the workspace, after building with the local toolchain:

```powershell
python devtools/setup_validation.py --output devtools/work/profile-new --profile --compile
python devtools/run_profile.py devtools/work/profile-new --java "C:/Program Files/Java/jdk-26.0.2/bin/java.exe"
python devtools/summarize_performance.py devtools/work/profile-new/instance
```

The fixture uses SPBR-22, 1 SPP, two bounces, fixed exposure, an opaque PBR room
and outdoor weather scenes. Vsync and frame generation are disabled. The helper
marks warmed-up steady intervals and resets warmup after a long render-thread
stall. POM, material bypass, DI/PT, NRD/RR, clouds, fog and post effects are
captured separately. Shader creation, signal readback and mode transitions are
outside the marked intervals. The isolated helper overrides desktop AFK/minimized
throttling only in performance mode and checks the limiter before accepting an
interval. Each scene receives ten seconds of warmup and twenty-five seconds of
measurement. `--resume-rr` resumes the last eight scenes; `combine_performance.py`
can combine unique completed intervals, retaining the run provenance. System-wide NVIDIA telemetry records utilization,
memory, power, clocks and temperature, not per-process GPU execution.

This synthetic six-chunk fixture does not establish Distant Horizons or a large
city world's performance. Keep its results separate from a full-distance world
capture and from converged image-quality comparisons.
# Sampled transport work

After a successful current production build, seal its inputs with
`devtools/build_transport_diagnostics.py <production.jar> --seal`, then build
the optional instrumented JAR with
`devtools/build_transport_diagnostics.py <production.jar> <new devtools/work/output>`
and add `-Dcaustica.rt.transportCounters=<absolute CSV path>` to an isolated capture.
The production JAR compiles all shader counter operations out and allocates no
counter buffers. The diagnostic JAR instruments ten raygen stages in ordinary
fallback NRD, DI and PT; cache/RR/SER indirect variants remain uninstrumented.
Ten raygen stages count rotating 32×32 pixel strata;
each pixel participates once per 1024 frames. Readback uses the existing push-slot
completion wait and a shader-to-host barrier. It never introduces a new fence wait.

The CSV contains **sampled** work. Divide summed calls by summed sampled pixels;
do not assume partial edge strata contain exactly 1/1024 of all pixels. Short or
moving captures need multiple repeats because they do not visit every stratum.
PT adapter counters cover actual surface rays, material-retrace entries, BSDF
evaluator calls, emitter marginal-PDF queries/nodes/charts, candidates, fresh paths,
replay and shift entries, and explicit environment evaluations. Shared tracing adds
radiance/guide rays, visibility calls and inline opaque pretests; shared RIS adds
candidate counts. Hit/miss shader invocations do not inherit raygen counter state,
so these are not complete texture-access or shader-instruction counts. Visibility
entries and their inline pretests overlap and must not be added as separate rays.

Use the production artifact for formal GPU times. Compare diagnostics with counters
off and on to measure both compiler/instrumentation and atomic-count overhead.
`devtools/run_profile.py --transport-only --counters` captures
the focused four-scene subset; `devtools/summarize_transport.py` summarizes it.
The original complete matrix remains available. The helper excludes asynchronous
pipeline compilation from its steady-state warmup. `setup_validation.py --jar`
selects a frozen comparison artifact without changing source or build properties.
Preparation records the actual artifact version and SHA-256. Launch rejects a
changed artifact and rejects requested counters on a production build. Summaries
reject requested captures with absent counters or missing expected stages.
`devtools/run_transport_comparison.py` runs three pairs in reversed version order;
do not run shader compilation or another GPU workload during these captures.
