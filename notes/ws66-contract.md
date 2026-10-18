# ws66 — lobo on 0.2.32 (lobo#92: the park at start retired)

Crawl 54, batch 7, lane ws66 (Opus). Written 2026-10-18 on lobo trunk
`d3f4a38`, after the inputs below were re-derived and measured, and
before any change to `src/`, `tests/`, `tools/`, `docs/` or
`wolf-toolchain.toml`, and before any binary without the workaround
was run. The planning contract is
`sprints/wws/35-the-pin-0232/ws66-lobo-on-0232.md` in
`wolffe-lang/wolf` (planning trunk `88d67ae`); rules are
`sprints/crawl-54.md`, `wave-53.md` down to `wave-45.md`.

One deliverable, five items:

1. lobo pinned from wolf 0.2.29 / lupin 0.1.52 to **wolf 0.2.32 /
   lupin 0.1.54** in a commit of its own; the bare pin's gates against
   0.2.29's; what each of 0.2.30, 0.2.31 and 0.2.32 moves for lobo.
2. **lobo#92**: ws64's one parked read at start retired, since s239
   makes the readiness set before `main`; red at 0.2.29 (lobo#90's
   exhaustion: `ulimit -n 32`, 30 slow downloads) and green at 0.2.32,
   both tiers.
3. A server started at its descriptor limit: it starts with its set or
   exits 71 before serving, which one where, and that the exit is one
   line on standard error.
4. The parity and memory gates re-taken (runner-VM parity; the
   master's RSS gate from ws62).
5. The plant: the workaround removed on the 0.2.29 pin, red in CI.

## 1. Forbidden, absolutely

- **Nothing here deploys or serves anything public.** lobo serves no
  site of ours; lupp.us is nginx on almanta (`sprints/HOSTING.md`).
  Never almanta, any Cloudflare tunnel or `~/.cloudflared`, DNS, or
  host ports 8080 and 8088; never a listing of `cloudflared`'s
  arguments. Every server this lane starts binds 127.0.0.1 on a
  kernel-chosen port or one of 18860–18879, and is stopped through its
  control endpoint, by its handle, or by its recorded pid.
- No release, no tag, no Homebrew tap or AUR change (lobo stays 0.1.4
  published; trunk stays `+dev`). No merge. No issue filed or closed
  (they are listed in the report). No attribution or co-author trailer
  in any commit or PR text.
- Toolchains only from the published release archives by digest, each
  digest read twice: never wolf-lang trunk, a clone's build, Homebrew
  or `~/.local/bin` (CI builds the pinned revs from source, as it
  always has).
- A descriptor limit is lowered only for one server at a time, with
  `ulimit -n` in the subshell that execs it. No host or user limit and
  no sysctl changes.
- No `rm` outside `~/lanes/ws66/` (nomad-1 and kasumi); no scratch in
  `/tmp`; no `git add -A`; nothing under `~/.claude`; no package
  installs; the branch asserted before every commit; no `2>/dev/null`
  on a checkout. No build on nomad-1 (macOS gates run in CI).
- kasumi: remote commands in `bash -c`, `setsid` with a pid file, kill
  by recorded pid only (never a name, a pattern or a process group);
  outputs pruned as the lane goes.
- Strict evidence (wolf-lang#571): `WOLF_PAIRING_REQUIRE_SIBLING=1`,
  stdout and stderr together, every SKIP line counted; a `wolf build`
  that exits 2 is a compile error; process, signal and descriptor rows
  also under `taskset -c 0-3`; SigBlk/SigIgn read before a signal row
  is called red. No "seen red" without a run id, sha, path or digest.
- At most two CI runs of this lane at once; never cancel another
  lane's. If the harness refuses an action, stop and report.

## 2. Inputs, verified (re-derived 2026-10-18)

| input | what was found |
|---|---|
| lobo trunk | `d3f4a38566be…` (the `+dev` flip after 0.1.4, PR #89); origin has no later commit (API read twice, `nomad-1:~/lanes/ws66/ev/tag-commits.txt`) |
| wolf 0.2.32 | tag `v0.2.32` → wolf-lang `72de141f6246…` (annotated tag `d21c4b28…`); release 416327027, not a draft, 4 assets. API digests read twice, identical (`nomad-1:~/lanes/ws66/ev/api-digests-{1,2}.txt`): linux x86-64 `4c37f9c5…` (80,092,071 B), macOS arm64 `061ea7e5…`, linux aarch64 `af27d426…`, windows `40eb42af…`. Staged on kasumi, `sha256sum -c` twice (`kasumi:~/lanes/ws66/dl/digest-check.txt`): `wolf` 81bdf8d4…, `libwolf_rt.a` 74d55d5f…, `wolf-cimport-worker` 0498e8e1…; `wolf 0.2.32 (wolfgang, pin 72de141)`, `paired with lupin 0.1.54`; GLIBC_2.34; the archive's `std/STD-REV` is `d37c911f…` (`kasumi:~/lanes/ws66/toolchains.txt`) |
| lupin 0.1.54 | tag `v0.1.54` → wolf-interp `0e536e8fb451…` (annotated tag `9c98d445…`); release 415937354, 5 assets; linux x86-64 `175df238…` (2,971,403 B), macOS arm64 `9cd14db7…`. `lupin` a9856dd4…, `lupin 0.1.54 (wolf-interp, reference interpreter at pin 294d626)` |
| 0.2.29 / 0.1.52 beside it | re-staged by digest twice (`ae466e85…`, `f5194b74…`): `wolf` 07f12158…, `libwolf_rt.a` fa0a0ae5…, `lupin` 74043b0a…: ws63's and ws64's bytes |
| wolf-std | lobo's `[std]` is `9e5bd6b` (sc60, wolf-std at 0.2.29). 0.2.32's bundled std is `d37c911f12206c4b…` (sc63; API read twice). Between them six files differ (`std/env`, `std/fs`, `std/os/users`, `std/process`, `std/signal`, `std/term`; +791 −30); lobo reaches one, `std/signal`, which gains `wait_fd` and with it `use std.fs` |
| the three CHANGELOGs | read at `v0.2.32` (`nomad-1:~/lanes/ws66/ev/wolf-CHANGELOG-0232.md`). Lines for lobo: 0.2.30 "the toolchain digests; the privilege drop after binding a low port (lobo#52) can be written on `os_set_ids`; `os_euid() == 0` replaces reading `/proc/self/status`" (not taken here; one deliverable); 0.2.31 "**lobo#92**: retire the descriptor workaround … a server at its descriptor limit either starts with its set or exits 71 before serving"; 0.2.32 "the toolchain digests; lobo#92". |
| what moves lobo, by release | **0.2.30**: s755 (seven straight-line constructs that panicked 0.2.29's native and release builds; lobo built at 0.2.29, so none was in a function it compiled), s233's must-join rule (E1010; the CHANGELOG says lobo compiles unchanged and names `budget.run_small` as read path by path), eleven new prelude names. **0.2.31**: s237's shift rule (s237's census: lobo's 95 shift sites all `wrapping`, no new trap), **s239's readiness set before `main` and exit 71** (lobo#92), s243's signal hub before `main` (lobo names `os_signal_listen` and `os_signal_wait`), the net family's `os_error()` (#751; lupin's half in 0.1.54), seven new prelude names. **0.2.32**: s245: the runtime's descriptors never take 0–2, and the set and hub are made where they are *reached* on both tiers (lobo reaches both). |
| new prelude names | 0.2.30's eleven and 0.2.31's seven (0.2.32 adds none): `git grep` over `src tests tools` at `d3f4a38` finds no declaration and no use of any of the eighteen |
| trunk at 0.2.32 | `src/` at `d3f4a38` builds on both tiers at `--error-limit=0` with **zero diagnostics**, with std `9e5bd6b` and with `d37c911` (`kasumi:~/lanes/ws66/logs/build-t32-s9e.log`, `build-t32-sd3.log`). Release 14,335,096 (0.2.29) → 14,695,128 (0.2.32, std 9e5bd6b) → 14,694,056 bytes (std d37c911); dev 16,410,816 → 16,770,928 → 16,783,384 (`build-t29-s9e.log`). The two std trees give different digests on both tiers (`std.signal`'s new `use std.fs`) |
| at rest, trunk | one process, 1.2 s after start, release and dev, at 0.2.29 and 0.2.32: **20 descriptors, 21 threads** every time (`kasumi:~/lanes/ws66/logs/rest-inputs.log`). At 0.2.29 the epoll and eventfd sit at 5 and 11 (made at the warm read in `serve_main`); at 0.2.32 at 3 and 4 (made before `main`). RSS release 4,912 kB (0.2.29) / 4,944–4,960 kB (0.2.32). One of the 20 (fd 8, a socket) is inherited from the measuring shell's session, the same inode in every run: lobo's own count is 19 |
| the workaround | `src/main.lu` 1721–1738 (ws64, `aa13ab2`): a 1 ms `net_read` on the stream pipe's read end (else the self-pipe's) before the serving loop, then the stream pipe's 50 ms deadline, which predates ws64 and stays |
| lobo#92, #90, #86, #87 | #92 open (retire at the pin carrying s239); #90 open (the advisory, fixed in 0.1.4 by the workaround); #86 merged (ws64); #87 open (ws64's limit follow-ups, none touched here) |
| s239's measurement | wolf-lang#760's report: lobo 0.1.4's tree without the workaround at `ulimit -n 32`, 30 slow 24 MiB downloads: the 0.2.29-era runtime ends at the 8th (`reactor.rs:139`); s239's runtime stays up, 6 served, 20 at rest; 12 downloads read to the end 12 of 12 whole (`kasumi:~/lanes/s239/ev/lobo-dl-limit32.log`, `lobo-dlcut-limit32.log`). Its client scripts are reused here by digest: ws64's `lbm.sh` `8cf9f197…` (paths only changed) and `climit.py` `741ce30f…`, s239's `dlcut.py` `9ac1560a…` |
| kasumi | 16 cpus, load 1–2, `/home` 34G free, `ulimit -n` 2048 |

## 3. Prediction, committed before the first change

### 1. The pin

- The pin commit moves `[wolf]` and `[lupin]` only; the stamp
  constants and the fourteen `.wolfi` headers follow in their own
  commits, as at ws63. The gauntlet is GREEN at the pin with trunk's
  per-step verdicts, the same corpus lane-run count as trunk at 0.2.29
  (`kasumi:~/lanes/ws66/logs/g-trunk29.log`), `lobo-shell` 41 probes /
  40 parity / 1 named delta, membudget 24/24, 0 SKIP lines.
- `wolf audit --ci --dir src` holds with the manifest unchanged.
- `[std]` moves `9e5bd6b` → `d37c911` (0.2.32's bundled std) in a
  commit of its own after the pin: both tiers build with zero
  diagnostics, the digests move (an input), and no gauntlet verdict
  moves. `shell.std_rev` follows.
- At rest at the pin: 20 descriptors and 21 threads, as at 0.2.29
  (falsified by any other count).

### 2. lobo#92, the park retired

- The change: the 1 ms warm read and its comment go; the stream
  pipe's 50 ms deadline stays. Release `text` shrinks by under 1 kB.
- At rest without it at 0.2.32: still **20 descriptors and 21
  threads**, the set at 3 and 4 (falsified by any other count: the set
  is the runtime's now, made before `main`).
- **Red at 0.2.29**: lobo without the park at `ulimit -n 32`, 30 slow
  downloads, ends (SIGABRT, 134, `epoll_create1 failed` at
  `reactor.rs:139`) at about the 8th download, on the release and the
  dev tier, plain and under `taskset -c 0-3`. Falsified if it stays up
  on either tier.
- **Green at 0.2.32**: the same tree and load, both tiers, plain and
  under `taskset -c 0-3`: the process stays up, `status` answers inside
  1000 ms, 5–7 downloads served (s239's 6), and it serves again
  afterwards; 12 downloads read to the end 12 of 12 whole.
- A new test, `tests/serve/park_at_limit_e2e.lu` (native, checked),
  holds that shape against the built binary: red with a lobo built at
  0.2.29 without the park, green at 0.2.32. `control_exhausted_e2e`
  (step 2, downloads at 64) stays green at 0.2.32 and is red at 0.2.29
  without the park.

### 3. The start at the limit

- Below the set's two descriptors (and the hub's pipes) the process
  **exits 71 before any line of lobo runs**, with exactly one line on
  standard error, `wolf: the runtime could not make its readiness set
  (…); the program did not start` or the hub's twin, nothing on
  standard output, no pid file, nothing listening. Predicted at
  `ulimit -n` 3–6; at 4 for certain.
- From about 7 up to about 19 lobo itself starts and refuses with its
  own `[emerg]`-style line and exit 1 (a listener, the control endpoint
  or a log it cannot open); from 20 it serves. Falsified if any limit
  gives a status other than 0, 1 or 71, or a 134.
- At 0.2.29 the same low limits do not give 71 (lobo's own refusal, or
  an abort); a test, `tests/shell/start_at_limit_e2e.lu`, holds 71 and
  the one line, red at 0.2.29.

### 4. Parity and memory

- Runner-VM parity (dispatch on a side branch with `ref_tree` trunk):
  nginx ÷ lobo close and keepalive inside the 1.10 bar; this ÷ trunk
  0.97–1.03 on both shapes (the runtime moved three releases;
  lobo's shifts are all `wrapping`, so the shift rule adds no check).
- Memory: membudget 24/24; the master flat over 60 s (0 kB), within
  ±100 kB of trunk's at start.

### The planted break

- Branch `ws66-plant`: trunk's 0.2.29 pin with only the workaround
  removed and the two new tests. CI red on linux at
  `park_at_limit_e2e.lu` (the process gone at the downloads) and at
  `control_exhausted_e2e.lu` step 2, and at `start_at_limit_e2e.lu`
  (not 71). On macOS the same three red; macOS's kqueue at the limit
  is the least certain row.

### What would make this wrong

- The set made before `main` on 0.2.32 not covering lobo (lobo's park
  calls reached only through something the entry shim's walk misses):
  the at-rest fds would drop to 18 without the park, and the 30
  downloads would end the process at 0.2.32 too.
- A hub refusal ordered before the set's, or neither line exactly one.

## 3. The prediction against the measurement

Measured on kasumi (16 cpus, load 1–2.6, other lanes beside it), the
toolchains of §2; logs under `kasumi:~/lanes/ws66/logs/` (digests in §4).

**Held.**
- The pin: zero diagnostics on both tiers; the gauntlet GREEN at the
  pin (`4a2b17b`, `g-pin32.log`) with trunk's verdicts: 364/364 corpus
  lane-runs (trunk at 0.2.29: 364/364, `g-trunk29.log`), `lobo-shell`
  41 / 40 / 1, membudget 24/24, signal 22/22, 0 SKIP lines; the audit
  holds with the manifest unchanged.
- At rest: 20 descriptors, 21 threads at trunk 0.2.29, at the pin and
  at the head without the park, both tiers (`rest-inputs.log`,
  `job-head.log`); the set at 3 and 4 at 0.2.32.
- Red at 0.2.29 without the park: `ulimit -n 32`, 30 downloads, the
  process ends at the 8th (`epoll_create1 failed`, `reactor.rs:139`),
  release, dev and release under `taskset -c 0-3` (`job-head.log`).
  `park_at_limit_e2e` red 3 of 3 on both tiers plain and 2 of 2 under
  `taskset` (`trials-1.log`, `trials-ts.log`).
- Green at 0.2.32 without the park: the process stays up, `status`
  answers, 6 bodies started (s239: 6), 108 `[crit] accept() failed`
  lines and 12 refused opens, served again 0.45–0.47 s after the
  clients close; release, dev and both under `taskset`. Of 12 downloads
  read to the end none is cut (11 whole and one 500 on release, 9 and
  3 on dev; at 0.2.29 without the park 7 cut at 2.2–2.6 MB, 4 reset,
  the process gone; with the park at 0.2.29 11 and 1). The two tests
  green 3 of 3 both tiers and under `taskset`.
- The start at the limit: exit 71, one line, nothing on stdout, no pid
  file, at 4 for certain (the set's line).
- Memory: membudget 24/24 at the head (`g-head2.log`); the master grew
  0 kB over 60 s of supervision.

**Wrong.**
- The 71 range is 4–8, not 3–6, and **the hub's line comes first**
  from 5 to 8 (the set needs two descriptors and comes first; the hub
  then needs four). At 3 nothing of lobo's or wolf's runs: `setsid`
  cannot load libc (the harness's, recorded). lobo's own `[emerg]` is
  9–11, not 7–19, and **it serves from 12**, not 20 (`ladder-trunk.log`,
  `job-head.log`; the same on release and dev, at the pin with the park
  and at the head without it).
- Release text **grew** 2,376 bytes without the park (1,822,199 →
  1,824,575 at 0.2.32; +336 at 0.2.29), where I predicted a shrink
  under 1 kB: removing four calls changed what is inlined.
- The master's resident size at start of the 60 s gate is 4,544 kB at
  the head against 4,344 at trunk 0.2.29 (4,480 at the pin): +200 kB,
  outside the ±100 kB I predicted; it stays flat.
- My first `park_at_limit_e2e` was green at 0.2.29 without the park:
  it pinged the control endpoint to see the server up and opened the
  downloads 20 ms apart, and either lets the first park come before the
  limit. It now waits on the pid file and a bare connect and opens the
  downloads back to back (both written in the file's header).
- The macOS plant: the new test did not go red on the runner at 0.2.29
  without the park; `control_exhausted_e2e` [checked] did, a panic in
  the runtime (§4). I named macOS as the least certain row.

**Not predicted.**
- At 0.2.29 a start at 6–14 descriptors writes the pid file, binds
  the control socket and the listener, and then ends with SIGABRT in
  the runtime (`eventfd failed` at `reactor.rs:142`, `signal self-pipe
  failed` at `signal.rs:351`), leaving both behind; at 15 it started
  and could not be stopped over its endpoint.
- At 0.2.32 a start that fails at the pid file (limit 11) leaves the
  control socket it bound, and the next start refuses: `something
  already exists at "logs/c.sock"`. lobo's own, not the runtime's (for
  the orchestrator to file).
