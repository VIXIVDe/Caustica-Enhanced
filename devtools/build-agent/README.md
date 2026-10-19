# Local build agent (v2)

Runs whitelisted build actions on this PC with the workspace toolchain when a request file appears
in `requests/`. `supervisor.cmd` keeps it running and restarts it after a crash; the
agent does not start with Windows (it deletes any leftover sign-in entry). `START-AGENT.cmd` starts it by hand,
`STOP-AUTOSTART.cmd` removes a leftover autostart entry, and closing the minimized window stops it.

| Request `requests/<id>.json` | Runs |
| --- | --- |
| `{"action":"build"}` | `scripts/build.ps1` (full offline build) |
| `{"action":"fast"}` | `scripts/build.ps1 -Fast` |
| `{"action":"release","release":N}` | `devtools/build-release.ps1 -Release N` |
| `{"action":"test","name":"cloud_math"}` | `mod/native/tests/cloud_math.ps1` with `toolchain/env.ps1` |
| `{"action":"processes"}` | lists workspace build processes in `processes.json` |
| `{"action":"stop-builds"}` | stops other workspace builds (Gradle, build scripts, native compilers) and Gradle daemons |
| `{"action":"stop-gradle"}` | stops this workspace's Gradle daemons |
| `{"action":"restart-agent"}` | reloads `agent.ps1` |

Requests cannot pass commands, paths or scripts. `stop-builds` matches only processes whose command
line contains this workspace and a build tool; a game instance is never matched.

Results: `results/<id>/status.json`, `output.log` (timestamped, written live) and `summary.txt`.
Processed requests move to `done/`. Create `requests/<id>.cancel` to stop a running request; its
Gradle daemons are stopped too. `agent.json` is a heartbeat updated every few seconds.

Builds and releases hold the workspace build lock, so only one runs at a time. A second build,
started manually or by request, is refused with exit code 75 (status `blocked`).
