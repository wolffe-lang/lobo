# ws63 — the pin at 0.2.29

Wave 53, lane ws63 (Opus). Written 2026-10-13 on lobo trunk `af0fa41`
(ws62's head), after the inputs below were re-derived and measured and
before any edit to `src/`, `tools/`, `tests/`, `docs/` or
`wolf-toolchain.toml`. The planning contract is
`sprints/wws/32-the-pin-0229/ws63-the-pin-0229.md` in `wolffe-lang/wolf`
(planning commit `a35b2fe`); rules are `sprints/wave-53.md` down to
`wave-45.md`. The oracle is the pinned nginx 1.30.4 (ws47's copy,
`65595ac2…`), run, never read.

One deliverable: lobo pinned to wolf 0.2.29 / lupin 0.1.52 in a commit
of its own, and what that release changes for lobo:

1. the pin;
2. the connection ceiling, measured before and after (s231, #713);
3. the pid file written with `os_pid` (ws62's finding (d),
   wolf-lang#126);
4. signals by name;
5. the parity and memory gates re-taken.

Then lobo#81 and lobo#82 if in reach, otherwise why not.

## 1. Forbidden, absolutely

- **Nothing here deploys or serves anything public.** lobo serves no
  site of ours; lupp.us is nginx on almanta (`sprints/HOSTING.md`).
  Never almanta, any Cloudflare tunnel or its configuration, DNS, or
  host ports 8080 and 8088; never a listing of `cloudflared`'s
  arguments. Every server this lane starts binds 127.0.0.1 on a
  kernel-chosen port or one of 18800–18849, and is stopped through its
  control endpoint or by its recorded pid.
- No release, no tag, no Homebrew tap or AUR change. No merge. No
  issue filed or closed (they are listed in the report).
- The pin is taken from the published release archives by digest, each
  digest read twice: never wolf-lang trunk, a clone, Homebrew or
  `~/.local/bin`.
- No literal signal bit and no host signal number in lobo's source: a
  meaning is named by its `std.signal` function
  (`[os.signal.set.stable]`).
- nginx behaviour only from the pinned oracle; no server's, libc's or
  kernel's source is read.
- No `rm` outside `~/lanes/ws63/` (nomad-1 and kasumi); no scratch in
  `/tmp`; no `git add -A`; nothing under `~/.claude`; no package
  installs; no commit trailers or PR attribution of any kind; the
  branch asserted before every commit; no `2>/dev/null` on a checkout.
- No build on nomad-1 (macOS gates run in CI). kasumi: remote commands
  in `bash -c`, `setsid` with a pid file, kill by recorded pid only
  (never a name, a pattern or a process group), outputs pruned.
- Strict evidence (wolf-lang#571): `WOLF_PAIRING_REQUIRE_SIBLING=1`,
  stdout and stderr together, every SKIP line counted; a `wolf build`
  that exits 2 is a compile error; process-spawning, worker and
  ceiling rows also under `taskset -c 0-3`; SigBlk/SigIgn read before
  a signal row is called red. No "seen red" without a run id, sha,
  path or digest. Checksums carry a trailing `…`.
- The ceiling measurement loads the host no further than it needs:
  loopback only, the applied load and its duration written beside each
  number.
- At most two CI runs of this lane at once; never cancel another
  lane's. If the harness refuses an action, stop and report.

## 2. Inputs, verified (re-derived 2026-10-13)

| input | what was found |
|---|---|
| lobo trunk | `af0fa4128b2e…` (ws62's head, PR #80); no later commit |
| wolf 0.2.29 | tag `v0.2.29` → wolf-lang `6ffe7c6056ee…`; release 411040788, not a draft, 4 assets. Digests read twice from the API (`nomad-1:~/lanes/ws63/ev/api-digests-2.txt`): linux x86-64 `ae466e85…` (78,902,948 B), macOS arm64 `a79928ba…`, linux aarch64 `584b8fc2…`, windows `e8a37a7f…`. Staged on kasumi, `sha256sum -c` twice (`kasumi:~/lanes/ws63/dl/digest-check.txt`): `wolf` 07f12158…, `libwolf_rt.a` fa0a0ae5…, `wolf-cimport-worker` ebd3b809…; `wolf 0.2.29 (wolfgang, pin 6ffe7c6)`; GLIBC_2.34; the archive's `std/STD-REV` is `d7c2968c…` |
| lupin 0.1.52 | tag `v0.1.52` → wolf-interp `025428b725a3…`; release 410845419, 5 assets; linux x86-64 `f5194b74…` (2,943,200 B), macOS arm64 `66dc74d8…`. `lupin` 74043b0a… (r34's bytes), `lupin 0.1.52 (wolf-interp, reference interpreter at pin 294d626)` |
| 0.2.28 beside it | re-staged by digest twice for the before-measurements: `wolf` 39644daa…, `libwolf_rt.a` d856cb81…, `lupin` 583c573b… (ws62's bytes) |
| 0.2.29's CHANGELOG, r34's evidence | read at the tag. The lobo line: "the toolchain digests; a server holding a task per connection no longer stops past eight a core (s231)". Five new prelude names (`os_signal_ignored`, `os_signal_send`, `os_signal_number`, `os_pid`, `os_ppid`); lobo declares none |
| **drift: the lane the contract names** | the contract credits the worker cap to s235. s235 is `wolf lsp` finding std (#724). The cap went with **s231** (wolf-lang#713): the pool grows a worker per parked task |
| **drift: "0.2.29's meanings" have no names in the compiler** | the prelude declares no constant for any meaning at 0.2.29 (r34's evidence; the spec's `[os.signal.set.stable]` says so in a parenthetical). The names are `std.signal`'s functions: nine in the archive's bundled std (`d7c2968`), twenty listenable and eight send-only on wolf-std trunk `9e5bd6b` (sc60, the std at 0.2.29). lobo's `[std]` pin `14f0ab2` has no `std/signal` at all (52 files; `d7c2968` and `9e5bd6b` have 54), so naming a meaning moves `[std]` |
| trunk at 0.2.29 | `src/` at `af0fa41` builds on both tiers at `--error-limit=0` with **zero diagnostics** (`kasumi:~/lanes/ws63/logs/build-t29-s14.log`). Release 13,946,688 → 14,309,896 bytes, text 1,773,189 → 1,796,461 against 0.2.28 (`build-t28-s14.log`): the runtime's bytes |
| `[std]` | at 0.2.29 trunk's `src/` built against `14f0ab2`, `d7c2968` and `9e5bd6b` gives one release digest, `77f76f84…` (`build-t29-s14.log`, `build-t29-sd7.log`, `build-t29-s9e.log`): between the three trees only ten files differ and lobo reaches one of them (`x/json`) |
| **the ceiling at 0.2.28** | `tests/serve/stream_cap_e2e.lu`'s `LOBO_STREAMS` knob, one harness binary, the server binary swapped (`kasumi:~/lanes/ws63/logs/sweep-*.log`): N clients each download 24 MiB at 64 KB/s for 2.5 s. Built with 0.2.28, bodies started: 15/15, **15/20, 15/40** on 4 cpus (`taskset -c 0-3`); 47/47, **47/48, 47/60** on 12. The ceiling is `4·max(cpus, 2) - 1` parked downloads a process; one more gets its head and no body |
| **the ceiling at 0.2.29** | the same harness, the same source built with 0.2.29: 16/16, 20/20, 40/40, 100/100 on 4 cpus; 48/48, 60/60, 200/200 on 12. Not found up to 200 |
| what parks in lobo | the serving loop is one task over `net_wait` (connections are rows, not tasks). Tasks beside it: one stream proc per large plaintext download (parked in `net_write`), a capped proc per budgeted small body, the signal forwarder (`os_signal_wait`), the ACME daemon under `cert auto`. So the cap bit lobo exactly at downloads parked on slow clients; `stream_room` (`3·max(cpus, 2) - 2`) is sized a quarter under it (ws51) |
| lobo's own limits | `worker_connections` is a `planned` row (parsed, never applied); `worker_rlimit_nofile` is a `named_error`. lobo has no connection limit of its own |
| the pid file | ws62's: `shell.self_pid()` reads `Tgid:` from `/proc/self/status`, else forks `/bin/sh -c 'echo $PPID'`. 0.2.29 has `os_pid() -> int` (capability `env`, which lobo declares) |
| signals in `src/` | literal bits in `shell.lu` (`sig_reload` 1, `sig_terminate` 2, `sig_quit` 4, `sig_mask` 7, `sig_probe` 8, and the comparisons in `signal_name` / `signal_verb`) and in `main.lu` (`sig_meaning_of`, the forwarder's one-digit wire). Three builtins called: `os_signal_listen`, `os_signal_wait`, `os_signal_raise`. `-s <verb>` with no `control` directive refuses by name ("no arbitrary-pid signal send — wolf-lang#126"); `reopen` has no signal twin (nginx's is `SIGUSR1`, which had no meaning before 0.2.29's `USER`) |
| "the worker generation signal" | the contract's words; no such phrase is in lobo's tree. Read here as UPGRADE (`SIGUSR2`, nginx's signal for a new binary generation), the bit lobo's forwarder teardown rides (`sig_probe`). The master tells its hands about a new configuration generation over their control endpoints, not by a signal |
| lobo#81 | open: the proxy runs inline in the serving loop (`proxy.run`, called at two sites in `serve.lu`), so a silent upstream holds the process for `proxy_read_timeout` |
| lobo#82 | open: three named deltas (first-server-only limits, logs and metrics; regex `server_name`; listeners added at reload) |
| trunk's gauntlet | at `af0fa41` on its own pin (0.2.28), `kasumi:~/lanes/ws63/logs/g-trunk28.log`: the baseline every later run is read against |
| kasumi | 16 cpus, load 0.3–1.3, `/home` 32G free, `ulimit -n` 2048, `ulimit -u` 127189 |

## 3. Prediction, committed before the first change

### 1. The pin

- Both tiers build with zero diagnostics at 0.2.29 (an input). The
  gauntlet is GREEN at the pin commit with trunk's per-step verdicts
  and 0 SKIP lines. No test file changes its declared lanes.
- `[std]` moves `14f0ab2` → `9e5bd6b` (wolf-std at 0.2.29, sc60), in
  a commit of its own after the pin: the builds at that commit are
  byte-identical to the pin commit's on both tiers.
- `wolf audit --ci --dir src` holds with the manifest unchanged
  (`[env, exec, fs, net]`): `os_pid` charges `env`, `os_signal_send`
  `exec`.

### 2. The connection ceiling

- A new test, `tests/serve/parked_downloads_e2e.lu`, holds N =
  `4·max(cpus, 2) + 4` and N = `8·max(cpus, 2)` slow downloads against
  one process and asserts every body starts and a probe and `status`
  answer within 1000 ms. **Red against a lobo built with 0.2.28**: 15
  of 20 and 15 of 32 bodies on 4 cpus, 63 of 68 and 63 of 128 on 16.
  **Green built with 0.2.29** on 4 and on 16 cpus.
- With the room opened (a measurement build, not committed), a
  budgeted small body's capped proc runs beside 500 parked downloads
  on 4 cpus at 0.2.29 (it never ran beside `4·max(cpus, 2) - 1` at
  0.2.28).
- What bounds lobo now, each measured: descriptors (two a parked
  download, a socket and the file; one an idle connection) against
  `ulimit -n`; a thread a parked download (the release note says about
  15 KiB; predicted 20–80 kB resident a parked download with its
  buffers); the host's thread limit, past which a body waits and
  nothing aborts. Predicted at `ulimit -n` 2048: about 1,000 parked
  downloads a process, and the process still answers `status` when the
  next accept fails.
- `stream_room` stays as lobo's own margin for the budgeted small
  body; what it is sized against changes in the text (a thread per
  parked download, no pool limit behind it). Whether it should be
  re-sized is reported, not taken, unless the thread-limit measurement
  shows the loop can stall with it as it is.
- Load applied: at most 1,100 loopback connections at 64 KB/s each
  (about 70 MB/s) for under 10 s a probe.

### 3. The pid file

- `shell.self_pid` becomes `os_pid()`; the `/proc` read and the
  `$PPID` shell go. The file's bytes are unchanged (`<pid>\n`).
  `strace -f` of a start shows no `execve` of `/bin/sh` and no open of
  `/proc/self/status` by the master (trunk: the open, on linux).
- The start notice names the pid with no source clause. Test:
  `tests/shell/pid_file_e2e.lu` gains the notice's shape (red at
  trunk); `pid_text.lu` gains `os_pid() > 0` on three lanes (lupin
  serves `os_pid`).

### 4. Signals by name

- Every meaning in `src/` is `std.signal`'s function: `reload()`,
  `terminate()`, `quit()`, `upgrade()` (the probe), and `user()`. A
  grep gate in the gauntlet reds on a literal bit in the signal
  surface. No behaviour moves from the naming alone; the binaries
  change by a few hundred bytes.
- `-s reload | quit | stop | reopen` with **no `control` directive**
  sends the verb's meaning to the pid the pid file names
  (`os_signal_send`), as nginx does, where trunk refuses. With a
  `control` directive the endpoint stays the door (it answers the
  verdict). A pid nobody holds is the stale-pid alert. Red at trunk
  (exit 1, the refusal text), green at head.
- `reopen` gains its signal twin: lobo listens for `user()`
  (`SIGUSR1`), so `kill -USR1` cycles the logs as nginx's does. The
  forwarder's wire stops being the meaning's decimal digit.
- UPGRADE stays the forwarder's teardown probe, by name; an outside
  `SIGUSR2` is still ignored (no binary swap exists to claim it).
- The master's fan-out to its hands stays on their endpoints (the
  reply carries each hand's verdict). A signal as the fallback for a
  hand the fan-out could not reach is taken only if a deterministic
  test for it exists; otherwise it is named, not built.
- macOS: the same paths in CI (`os_signal_send` and `os_pid` are the
  host's own there).

### 5. Parity and memory

- Parity at four hands on a runner VM (nginx ÷ lobo, lower is better,
  bar 1.10): keepalive 0.90–0.95x, close 1.01–1.05x (ws62: 0.923x /
  1.038x); ws63 ÷ trunk inside 0.98–1.02x on both shapes. kasumi the
  same bands within its spread.
- Membudget 24/24 with the master row at 0 KB (bound 64 KB); the
  master's resident size within 25 % of ws62's 4,160 kB; RSS after
  400,000 keepalive requests in one process within 1 MB of ws62's
  4.98 MB.
- Idle syscalls a second across four hands fall (s231: a parked wait
  no longer polls) but not to nginx's 23: `os_signal_wait` still polls
  and every lobo process parks a forwarder in it. Low confidence on
  the size; ws59 measured 1,727.

### lobo#81, lobo#82

- **#81 not in reach here.** 0.2.29 removes the reason the upstream
  exchange could not take a proc of its own (the pool's cap, which on
  4 cpus was 15 parked tasks), so it is unblocked, not done: moving
  `proxy.run` beside the loop is a new row kind in the loop's table
  with the peer accounting carried back, under wolf-lang#678's
  must-join rule. A lane of its own.
- **#82 not in reach here.** None of its three deltas is touched by
  0.2.29 (wolf still has no regular expressions; per-server limits and
  listeners added at reload are lobo's own work).

### The planted break

A branch `ws63-plant` on the head with `-s quit` sending TERMINATE's
meaning (the wrong name): red in CI on both hosts at the `-s`-by-signal
test and nowhere else.
