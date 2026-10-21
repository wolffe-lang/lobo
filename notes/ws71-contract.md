# ws71 — lobo at 0.2.34 (the pin)

Crawl 54, the 0.2.34 downstream round's lobo step, lane ws71 (Opus).
Written 2026-10-21 on lobo trunk `06b079b` (lobo#108, the `+dev` flip
after v0.1.5), after the inputs below were re-derived and measured on
the 0.2.33 side, and before any change to `src/`, `tests/`, `tools/`,
`docs/`, `wolf-toolchain.toml` or the CHANGELOG, and before anything
was built with 0.2.34. The planning contract is
`sprints/wws/40-lobo-0234/ws71-lobo-at-0234.md` in `wolffe-lang/wolf`
(planning trunk `0d67596`); the rules are `sprints/RULES.md`. wolf-lang's
0.2.34 CHANGELOG names lobo's step as "the pin (ws68 is at 0.2.33)".

One deliverable: lobo on **wolf 0.2.34 / lupin 0.1.55 with the bundled
std `e036bec`**, from ws68's 0.2.33 / 0.1.54 / `cceda63`, in commits of
its own in ws66's shape (the toolchain file, the stamp constants, the
`.wolfi` headers' `toolchain 0.2.34` line as `tools/lobo-interface
--emit` writes it, the `[std]` move and the surfaces whose std hashes
follow; CI acquires each toolchain by the commit `wolf-toolchain.toml`
pins, so its acquire step moves with the file). Then:

1. the gauntlet on both hosts — its smoke (the dist step), the limit
   tests, the memory gate and the parity row against the pinned nginx;
2. every compiled object compared with 0.2.33's, and why any moved;
3. throughput and RSS against ws69's table as ws70 took it on the 0.1.5
   release (whether the pin moved any).

Nothing else: lobo#100 and #106 stay as they are; no release step (0.1.6
is a later ruling).

## 1. Forbidden, absolutely

- **Nothing here deploys or serves anything public.** lobo serves no
  site of ours; lupp.us is nginx on almanta (`sprints/HOSTING.md`).
  Never almanta, the live nginx, any Cloudflare tunnel or
  `~/.cloudflared`, DNS, or host ports 8080 and 8088; never a listing
  of `cloudflared`'s arguments. Every server this lane starts binds
  127.0.0.1 on a kernel-chosen port or one of 18980–18999 (or the
  ports of ws69's and ws70's rigs INSIDE a throwaway container's own
  network namespace), and is stopped through its control endpoint, by
  its handle, or by its recorded pid.
- **Root only inside a container**, as the gauntlet's `user` step does
  (rootless podman on kasumi). Signals, limits and faults only to
  processes the test started.
- No tag, no merge, no release, no tap or AUR change. No issue filed or
  closed (listed in the report). No attribution or co-author trailer in
  any commit or PR text.
- Toolchains only from the published release archives by digest, each
  digest read twice (CI builds the pinned revs from source, as always).
- No `rm` outside `~/lanes/ws71/` (nomad-1 and kasumi); no `git add
  -A`; nothing under `~/.claude`; no package installs; the branch
  asserted before every commit; no build on nomad-1. kasumi: `bash -c`,
  `setsid -f` with a pid file, kill by recorded pid only (never by name,
  pattern or process group); outputs pruned as the lane goes (`/home`
  had 24 G free at the start).
- Strict evidence (wolf-lang#571): `WOLF_PAIRING_REQUIRE_SIBLING=1`,
  stdout and stderr together, every SKIP line counted; `wolf build`
  exit 2 is a compile error; the gauntlet under `taskset -c 0-3`; the
  measuring shell's SigBlk/SigIgn recorded. No "seen red" without a run
  id, sha, path or digest.
- lobo CI is tiered (tl28): the PR opens without the label, `tier pr`
  goes green, `full-matrix` is added at the final head; never cancel
  another lane's run. If the harness refuses an action, stop and report.

## 2. Inputs, verified (re-derived 2026-10-21)

Logs under `kasumi:~/lanes/ws71/` (digests in §4); API reads under
`nomad-1:~/lanes/ws71/ev/`.

| input | what was found |
|---|---|
| lobo trunk | `06b079b6b016…` (ws70b's `+dev` flip, PR #108 merged); origin has nothing later; no lobo PR open |
| wolf 0.2.34 | tag `v0.2.34` (annotated `38ab81cb…`) → wolf-lang `9da7bdcf2aea…`; release 419552903, not a draft, four assets. API digests read twice, identical (`api-wolf-{1,2}.txt`): linux x86-64 `88a9dd3d…` (80,433,878 B), macOS arm64 `29c8331f…` (18,925,363 B), linux aarch64 `ca5cadf9…` (76,212,750 B), windows `77bb8403…` (15,911,654 B) — the contract's four. Staged on kasumi, `sha256sum -c` twice (`dl/digest-check.txt`): `wolf` 2bfaf7b8…, `libwolf_rt.a` cc058247…, `wolf-cimport-worker` 2e37607a…; `wolf 0.2.34 (wolfgang, pin 9da7bdc)`, `paired with lupin 0.1.55`; highest glibc symbol GLIBC_2.34; the archive's `std/STD-REV` is `e036bec3…` (`toolchains.txt`) |
| lupin 0.1.55 | tag `v0.1.55` (annotated `047184fb…`) → wolf-interp `e642f263…`; release 418932753, five assets; linux x86-64 `1152abc0…` (2,966,156 B), macOS arm64 `2eac1ccc…` (2,646,817 B), read twice; staged twice; `lupin` ad52ee96…, `lupin 0.1.55 (wolf-interp, reference interpreter at pin 294d626)`. wolf@v0.2.34 declares 0.1.55: the pairing gap is zero |
| 0.2.33 beside it | wolf `4f955e8d…` and lupin `175df238…` re-staged by digest twice: `wolf` 58e4ade4…, `libwolf_rt.a` 5321ce86…, `wolf-cimport-worker` 57c41e39…, `lupin` a9856dd4…: ws68's, ws69's and ws70's bytes; std `cceda631…` |
| wolf-std | lobo's `[std]` is `cceda63` (ws68). 0.2.34 bundles `e036bec3…`. Under `std/` four files differ (`net/net.lu`, `os/users/users.lu`, `process/process.lu`, `signal/signal.lu`; 427 insertions, 53 deletions). lobo `use`s all four: `std.net` (`acme/flow.lu`, `proxy/proxy.lu`), `std.os.users` (`config/userconf.lu`), `std.process` (`main.lu`), `std.signal` (`shell/shell.lu`). Every public declaration of 0.2.33's std is unchanged in the four; the new ones are `net.Addr`; `process.wait_status_core`, `status_from_core`, `dumped_core`, `CoreChange`, `poll_core`, `exit_signal`; `signal.ignore_one`, `reset_one`. lobo calls none of them |
| the 0.2.34 CHANGELOG | read at `v0.2.34`. For lobo: "the pin (ws68 is at 0.2.33)". What a running program can see change: a mode int without bits 5–7 writes the usual terminal setting (lobo sets no terminal mode: no `os_term_` call, no `std.term`); `wolf test` runs a test file's own `test_*` (lobo runs its tests through `conform-run`, never `wolf test`); a program that names `os_signal_wait_fds` makes the hub and the wake pipe before `main`, one that calls `os_term_restore_at_exit` holds one more descriptor (lobo calls neither); the bundled std moves to `e036bec`. `os_fork` answers `busy` while a task is live (lobo does not fork). The pairing is lupin 0.1.55 (0.2.33's five calls resolve; the signal listen, wait and raise resolve and are refused by name) |
| new prelude names | `os_fork`, `os_term_restore_at_exit`, `os_signal_wait_fds`, `fs_sync`, `fs_sync_dir`, `fs_realpath`, `os_clock_ns` and the mark `busy`: `git grep -w` over `src tests tools` at `06b079b` finds no declaration and no call of any of the seven; `os_signal_wait_fds` once in a doc comment (`src/proxy/proxy.lu:1232`); `busy` as a `bool` parameter of `wait_budget` (`src/main.lu:5538`) and in prose |
| the `.wolfi` surfaces | the four std modules' hashes appear in `acme.wolfi` (`std.net`, and `std.x.tls.client`, which imports `std.net`), `config.wolfi` (`std.os.users`), `proxy.wolfi` (`std.net`, `std.x.tls.client`), `shell.wolfi` (`std.signal`) and `root.wolfi` (`std.process`); no other surface names one of them or a std module that imports one |
| trunk's objects at 0.2.33 | `scripts/build.sh` at `06b079b` (`logs/build-t33.log`): every object the gauntlet's tools compile — both tiers of `src/main.lu` (release with the mid-end on, as the gauntlet and `tools/lobo-dist` build it) and the five rig binaries (`nowms`, `climit`, `pipewait`, `wedge` from `tests/rig/`, `acmeca` staged with `acme`, `config`, `conn` and `tls` as `tools/lobo-acme` stages it) — exits 0 with zero diagnostics at `--error-limit=0`: release `lobo` 14,838,976 B (`.text` 1,616,323), dev 17,090,376 B (`.text` 3,319,731), `nowms` 13,040,360, `climit` 13,372,104, `pipewait` 13,375,960, `wedge` 13,286,504, `acmeca` 15,184,544; release 3e0b0e3e…, dev 53f7ef77…. **Deterministic**: built again from the same path (`t33b`, `logs/build-t33b.log`) all seven are byte-identical, so a digest that moves at the pin is the toolchain's. wolf code is named `_W<module>.<fn>$<hash>` in the symbol table, the runtime and the Rust it links `_R…` (`objdiff.py` splits the two) |
| at rest, trunk at 0.2.33 | one process, 1.2 s after start, every inherited descriptor closed before the exec, on cpus 8–11 (`ev/rest-t33.log`): **20 descriptors and 9 threads**, release and dev, twice each (the set at 3 and 4, the hub's pipes 5–8, no wake pipe); RSS release 4,688–4,696 kB, dev 5,436–5,560 kB — ws68's count |
| lobo 0.1.5 | release 420039477, tag `v0.1.5` → `91b76133…`; the linux archive `b61466c0…` (3,997,075 B, API read twice, `sha256sum -c` twice with its sidecar); binary `0da8d84d…` (ws70's), `lobo version: lobo/0.1.5 (built with wolf 0.2.33, pin 85dab5d)`; BUILD names source `91b7613`, std `cceda631…` |
| the baseline numbers | ws69's table (`notes/ws69-contract.md` §3) and ws70's measurement of the 0.1.5 release on it (`notes/ws70-contract.md` §3, P5): RSS after 400,000 keepalive requests 4,740 and 4,664 kB, growth 0 B a request and a connection; static at four workers and 32 clients, keepalive 638,278 req/s and a connection per request 125,781 (nginx 497,352 / 126,742); proxied px 16,605, ab1 15,758, ab32 17,761 (nginx 16,603 / 17,844); runner-VM parity nginx ÷ 0.1.5 close 1.032x, keepalive 0.933x (run 39656019826). ws70's rig is reused by digest: `rss.sh` 1a6f2ad3…, `tput.sh` 6b6a7c4a…, `tput-in.sh` 309c631f…, `px69.py` 8efb62d3…, `summ.py` 941b8f8a… (this lane's paths) |
| gates and plants | the pin adds no gate and changes none: every gate it is held to is trunk's, already seen red by the lanes that made it. Nothing is planted here (RULES.md §5's rule is for a new gate) |
| the oracle, ab | nginx 1.30.4 `65595ac2…` and ApacheBench 2.3 `05f2f6d5…`, copied from ws70's lane, each checked twice |
| kasumi | 16 cpus (cpu N and N+8 one core's two threads), load 3–18 over the inputs (other lanes), `/home` 24 G free, `ulimit -n` 2048; podman rootless |

The gauntlet at 0.2.33, the row the pin is held to: ws70's run at the
0.1.5 tree (`kasumi:~/lanes/ws70/logs/g-head.log`, `15d0e37`, GREEN,
exit 0, under `taskset -c 0-3`, 0 SKIP lines): corpus 386/386
lane-runs, `differential` 33/33, `proxy-differential` 8/8,
`control-differential` 20/20, `logdiff` 4/4, `confcheck` 40 configs (27
exit-parity, 13 named deltas, 0 red), `dryrun` 41 probes + 2 cross
checks, `lobo-shell` 46 probes / 45 parity / 1 named delta / 0 red,
`lobo-signal` 22/22, `lobo-prefork` 38/38, `lobo-user` 25/25,
`lobo-metrics` GREEN, `lobo-membudget` 25/25, `lobo-resolver` 9/9,
`tls-interop` 8 cases, `tls-renewal` and `acme` 0 red, `lobo-dist`
packed twice identical and smoked. Trunk `06b079b` (the same source but
the channel) is re-run here at 0.2.33 beside the pin, on the same box,
as the row's own baseline (`logs/g-trunk33.log`, started before this
prediction, read after it).

## 3. Prediction, committed before the first change

### The pin

- Commits as ws66's and ws68's: `[wolf]` to `9da7bdcf` and `[lupin]` to
  `e642f26` with `[std]` held at `cceda63` (the bare pin); the stamp
  constants (`0.2.34`, `9da7bdc`); the fourteen `.wolfi` headers
  (`toolchain 0.2.34`, every other line unchanged); `[std]` to
  `e036bec` with `shell.std_rev`; then the surfaces whose std hashes
  move — **exactly `acme`, `config`, `proxy`, `shell` and `root`**
  (falsified by a hash moving on any other surface, or by one of the
  five not moving). The CI files do not change: both jobs acquire by
  the revs the toolchain file pins.
- **Nothing is refused**: both tiers and the five rigs build with zero
  diagnostics at the bare pin and at the std move (no W0304: lobo
  declares none of the seven names; `busy` as a parameter is not a
  function).
- `wolf audit --ci --dir src` holds with the manifest unchanged; the
  bare pin reads trunk's counts (net +197, fs +128, exec +18, env +10);
  the std move moves them by at most a few sites, no capability.
- The gauntlet is GREEN at the bare pin and at the head with trunk's
  verdicts row for row (the row above: corpus 386/386, `lobo-shell` 46
  / 45 / 1 / 0, membudget 25/25, the dist step packed twice identical),
  0 SKIP lines, under `taskset -c 0-3`; every `ok` line the same row but
  for timings, spreads and paths. lupin 0.1.55 changes no declared lane
  (the lane-run count is trunk's). On CI, `tier pr` (linux) and `tier
  full` (linux and macOS) green with the same counts.
- **The limit tests** (`control_exhausted_e2e`, `worker_connections_e2e`,
  `start_at_limit_e2e`, `park_at_limit_e2e`) green on native and checked
  inside the corpus step, and ws66's start ladder unchanged: exit 71 with
  one line at `ulimit -n` 4–8, lobo's `[emerg]` at 9–11, serving from 12
  (0.2.34 makes nothing more before `main` for a program that names
  neither new call).
- At rest at 0.2.34: **20 descriptors and 9 threads**, the same targets,
  both tiers (lobo names neither `os_signal_wait_fds` nor
  `os_term_restore_at_exit`; a doc comment is not a name); RSS within
  ±100 kB of 0.2.33's.

### The objects

- **The bare pin moves every object's digest** (the runtime:
  `libwolf_rt.a` 5321ce86… → cc058247…; RT_SYMBOLS 229 → 237): the
  release `lobo` grows 5–80 kB on the file and 0.5–8 kB of `.text`, dev
  alike, each rig binary by about the same runtime delta. lobo's own
  functions compile to the same code: every symbol outside the runtime
  keeps its size (falsified by any lobo function's size moving at the
  bare pin).
- **The std move** (`cceda63` → `e036bec`) moves the digests of
  `lobo-rel`, `lobo-dev` and `acmeca` (they import modules that import
  the four changed files) by under 4 kB each, and **not** the four
  import-free rigs (`nowms`, `climit`, `pipewait`, `wedge`: identical
  bytes to the bare pin's).
- The build is deterministic: the same tree, toolchain and path build
  the same bytes twice (`t33` and `t33b`), so a moved digest is the
  toolchain's.
- The head's objects differ from trunk-at-the-new-pin's only by the
  stamp strings (`0.2.34`, `9da7bdc`, `e036bec`).

### What moves for lobo, by name

- Nothing a client sees: no fork, no terminal, no `wolf test`, no new
  call; the std's new functions are not called. The binaries by the
  runtime and the std.

### The numbers (kasumi, ws70's rig, alternating rounds)

- RSS of one process after 400,000 keepalive requests within ±200 kB
  of 0.1.5's (4,664–4,740 kB), growth 0 B a request and a connection.
- Static at four workers: the head ÷ 0.1.5 0.95–1.05x on both shapes;
  proxied px, ab1 and ab32 inside 0.1.5's own spread (its px spread was
  36 %), the medians 0.90–1.10x. The pin moves none of the numbers.
- Runner-VM parity (`tier measure`, `ref_tree=v0.1.5`): nginx ÷ ws71
  inside the 1.10 bar on both shapes; ws71 ÷ 0.1.5 0.97–1.03x.

### What would make this wrong

- A runtime change on a path lobo reaches every pass (s247 parks the
  pool's workers and claims the hub's and reactor's threads only at a
  fork; if a new check sits on the park or wake path, keepalive
  requests a second would move).
- A surface hash that moves without an import of the four (the hashes
  are transitive through `std.x.tls.client`'s `use std.net`, which
  only `acme` and `proxy` name).
- lupin 0.1.55 answering a lobo `lupin` lane differently (its new
  refusals by name for the signal family; no lobo test that declares
  `lupin` is known to reach one).

## 3. The prediction against the measurement

Measured on kasumi (16 cpus; other lanes beside this one, load 1–18),
the toolchains of §2; logs under `kasumi:~/lanes/ws71/` (digests in
§4). §3 above is as committed (`9a8ce06`).

### The pin

**Held.**
- Nothing is refused: at the bare pin (0.2.34, std `cceda63`) and at
  the std move (`e036bec`) both tiers and the five rigs exit 0 with
  zero diagnostics at `--error-limit=0` (`logs/build-p34s33.log`,
  `build-p34.log`, `build-h34.log`); no W0304.
- Commits in ws66's and ws68's shape: `[wolf]` and `[lupin]` with
  `[std]` held (`7e38417`), the stamp constants (`0436187`), the
  fourteen headers (`a6992b6`: `tools/lobo-interface --emit` at the
  bare pin wrote exactly the fourteen `toolchain 0.2.34` lines),
  `[std]` with `std_rev` (`2941c8e`), the surfaces (`fe99c55`). The CI
  files do not change: both jobs acquire the revs the toolchain file
  names (the parity run below built 0.2.34 and lupin 0.1.55 from them).
- The audit (`ev/audit.log`): net +201, fs +128, exec +18, env +10 at
  trunk on 0.2.33, at the bare pin and at the std move: no count moves,
  no capability (I quoted ws68's +197 for net in the prediction; trunk
  reads +201 since ws69).
- **The gauntlet** (kasumi, `taskset -c 0-3`, strict env, SigBlk
  `0x10000`, SigIgn `0x4`, 0 SKIP lines in each):
  - trunk `06b079b` at 0.2.33 (`logs/g-trunk33.log`): GREEN, exit 0,
    1,106 s;
  - the bare pin `a6992b6` (`logs/g-bare34.log`): GREEN, exit 0, 1,021 s;
  - the head `fe99c55` (`logs/g-head34.log`): GREEN, exit 0, 959 s
  — each with trunk's rows: corpus 386/386 lane-runs, `differential`
  33/33, `proxy-differential` 8/8, `control-differential` 20/20,
  `logdiff` 4/4, `confcheck` 40 configs (27 / 13 / 0 red), `dryrun` 41
  probes + 2 cross checks, `lobo-shell` 46 probes / 45 parity / 1 named
  delta / 0 red, `lobo-signal` 22/22, `lobo-prefork` 38/38, `lobo-user`
  25/25 (podman, `ubuntu:24.04`), `lobo-metrics`, `lobo-membudget`
  25/25, `lobo-resolver` 9/9, `tls-interop` 8 cases, `tls-renewal` and
  `acme` 0 red, the replay's hunt and fix, `lobo-dist` packed twice
  identical and smoked (200, the stock page byte-compared, `-s stop`).
  Row for row (`scripts/okdiff.sh`, numbers, digests and paths
  normalized): 785 verdict lines each, and the only lines that differ
  are the stamp's (`ev/ok-*.txt`). lupin 0.1.55 moves no declared lane.
- **The memory gate** (`lobo-membudget`, the same 25 rows): the flat
  rows read 0 KB over 4,000 requests, 2,000 connections, 10 idle seconds
  and the file memo at both pins (resident 4,872–4,952 kB at 0.2.33,
  4,912–4,992 kB at the head); the capped rows 52/24 KB and 76/36 KB
  (bound 4,096); `flat, proxied` (lobo#106's row) 4 KB over 2,000 proxied
  requests at both, under `taskset -c 0-3` (#106 is the 16-cpu case, not
  re-taken: the contract leaves it as it is).
- **The limit tests** (`control_exhausted_e2e`, `worker_connections_e2e`,
  `start_at_limit_e2e`, `park_at_limit_e2e`) ok on native and checked in
  every corpus step above, and the start ladder unchanged (`ev/ladder-t33.log`,
  `ladder-h34.log`, ws66's `ladder.sh` by digest): at both pins `ulimit
  -n` 4 exits 71 with the readiness set's one line, 5–8 exit 71 with the
  signal hub's, 9–11 are lobo's own `[emerg]` (exit 1), from 12 it
  serves; at 3 the measuring `setsid` cannot load libc (ws66's row).
- At rest (`ev/rest-t33.log`, `rest-p34s33.log`, `rest-p34.log`): 20
  descriptors and 9 threads at both pins, both tiers, the same targets
  (the set at 3 and 4, the hub's pipes 5–8); RSS release 4,688–4,696 kB
  (0.2.33), 4,676–4,732 kB (0.2.34).

**Not predicted.** The release binary the gauntlet builds is
byte-identical to this lane's build of the same tree from another path
(`3e0b0e3e…` at 0.2.33); the debug binary is not (`a6607bb8…` against
`53f7ef77…`): debug names its paths (ws53's note), release does not.

**Wrong.**
- The surfaces whose hashes move at the std move are `acme`, `dryrun`,
  `proxy`, `serve`, `shell` and `root` (`fe99c55`), not `acme`,
  `config`, `proxy`, `shell` and `root`. `config` keeps its hashes:
  `std.os.users` changed by its documentation only, and a surface
  hash is the signatures', so `ff8a852c…` holds. `dryrun` and `serve`
  move although they import none of the four: each names `proxy`'s
  hash (`proxy <hash>` in its surface), and `proxy`'s moved with
  `std.net`'s. The hashes are transitive through lobo's own modules,
  not only through the std's (my "what would make this wrong" named
  only the std's).

### The objects

Every object the gauntlet's tools compile, at four points
(`ev/objects-table.txt`; `scripts/objdiff.py` splits each binary's
text symbols into lobo's code `_W…`, the Rust runtime and std `_R…`,
and the rest; `scripts/wcode.py` compares lobo's functions instruction
by instruction with addresses taken out). Bytes, `.text` and digest:

| object | trunk at 0.2.33 | bare pin (0.2.34, `cceda63`) | std move (`e036bec`) | the head |
|---|---|---|---|---|
| `lobo` release | 14,838,976 / 1,616,323 / 3e0b0e3ec384 | 15,261,984 / 1,620,163 / 339e00bd3892 | 15,263,616 / 1,621,027 / 49881c0ebccc | 15,263,616 / 1,621,027 / 7f8980352a1e |
| `lobo` dev | 17,090,376 / 3,319,731 / 53f7ef77674d | 17,519,696 / 3,329,150 / 0913feedc1c3 | 17,526,264 / 3,333,182 / 6b0f904fe71d | 17,526,264 / 3,333,182 / e3b2bf579c2b |
| `nowms` | 13,040,360 / 238,467 / 2fbbc177ad34 | 13,456,968 / 238,467 / 66ac22e2d2c7 | the same bytes | the same bytes |
| `climit` | 13,372,104 / 417,219 / 92ce924df139 | 13,793,272 / 418,931 / 7f5295562229 | the same bytes | the same bytes |
| `pipewait` | 13,375,960 / 419,379 / 7942f92cd621 | 13,798,760 / 422,243 / 04de43bfcac7 | the same bytes | the same bytes |
| `wedge` | 13,286,504 / 368,899 / 8862ba44275e | 13,710,424 / 371,587 / e3d210c27b75 | the same bytes | the same bytes |
| `acmeca` | 15,184,544 / 1,752,515 / 0e9eeb4e2ee4 | 15,608,112 / 1,756,163 / e19bf7a84eae | 15,608,120 / 1,756,163 / 320a74a0e296 | the same bytes |
| the dist archive | 4,361,263 B / 01cd338cf4e7 | 4,467,303 B / e1ee7793bba3 (`a6992b6`) | — | 4,468,479 B / ce64f0e9cc02 |

**Held.**
- Deterministic: built twice from one path, every object is the same
  bytes (`t33`, `t33b`).
- **The bare pin moves every digest by the runtime alone**
  (`ev/objdiff-t33-p34s33.log`, `ev/wcode.log`). lobo's own code is
  untouched: the release binary's 707 `_W` functions (208,369
  instructions), dev's 1,522 (467,838), `acmeca`'s 881 and the rigs'
  are identical instruction for instruction, with the same symbol
  hashes. Release `.text` +3,840 bytes, all of it the runtime's: s247's
  fork protocol on the threads lobo runs — the reactor's kernel wait
  (`reactor_main` +396, a state change either side of each
  `epoll_wait` so a fork can claim the thread there), the signal hub's
  reader (`reader_main` +426, `try_hub` +202), the pool (a hold point
  in each worker's loop, `fallback` +494, retired threads counted for
  the fork's join) — and the C-ABI entries whose inlining moved
  (`__wolf_rt_fs_read` +2,266 and `fs_read_chunk` +2,028 absorb the
  four `scratch::with_read_buf` closures they called; the string
  builtins about +240 each, the traps +213 and +237). The files grow
  416–429 kB, nearly all the runtime's debug info (`.debug_info`
  +167,834, `.debug_loc` +96,763, `.debug_str` +82,303, the same in
  every object: the static library's). `nowms` (one 26-instruction
  function) keeps its `.text` to the byte; only its debug info moves.
- The four rigs that import nothing are byte-identical across the std
  move, and the head differs from trunk built at the same pin by the
  stamp's strings alone (release 48 bytes, dev 34: `0.2.34`,
  `9da7bdc`, `e036bec`; `ev/objdiff-p34-h34.log`).

**Wrong.**
- The std move is not "under 4 kB on each of `lobo-rel`, `lobo-dev`
  and `acmeca`" for the reason I gave. Dev grows 6,568 bytes: it
  compiles the seven functions the four files add (`process.poll_core`
  1,128 bytes of them) and the runtime entries they call
  (`exit_signal`, `set_disp_one`, `wait_*_core`), and 19 of its 1,522
  functions differ only in an immediate, the line number a trap
  reports (`std.os.users` gained 35 lines of documentation above
  them: `mov $0x5b,%ecx` → `mov $0x7e,%ecx`). Release grows 1,632
  bytes (`.text` +864) with none of the seven in it: its whole-program
  pass drops them, and 32 of lobo's functions come out inlined
  differently (`serve_main` +46 instructions, `master_main` −83;
  4 functions inlined away, 13 now out of line), 14 more by a trap's
  line number or alignment padding; 657 of 707 are identical. The four
  files remove no line of code (427 insertions, 53 deletions, every
  deletion a comment), and the std's path is not the cause (0.2.34
  built against the same `cceda63` tree by another path gives the bare
  pin's bytes, `logs/build-ctl.log`). `acmeca`'s code is identical
  across the move; 8 bytes of debug info carry `std.net`'s moved line
  numbers (a `DW_AT_decl_line` 240 → 257 needs a second byte).

**Not predicted.**
- An object's debug build names its paths (the `acmeca` staging
  directory moves its `.rodata` and digest); every `acmeca` compared
  here is staged at one path (`scripts/acmeca.sh`, `logs/acmeca.log`).

### The numbers

Kasumi, ws70's rig with this lane's paths (§2; the server under
`taskset -c 0-3`, the clients on cpus 6–7, the proxied rows' upstream
on 4–5, in a rootless `archlinux:base-devel` container's own network
namespace), five alternating rounds, load 1.1–4.9 (`ev/tput-rel5.log`,
`scripts/summ.py`). Four servers each round: the published 0.1.5
(`0da8d84d…`, built on the release runner), trunk `06b079b` built here
at 0.2.33 (`t33`, the same source but the channel), the head built here
at 0.2.34 (`h34`), and the pinned nginx. Requests a second, the median
of five (the spread in brackets):

| shape | nginx | 0.1.5 (ws70) | 0.1.5 | trunk at 0.2.33 | **the head** | head ÷ 0.1.5 | head ÷ trunk |
|---|---|---|---|---|---|---|---|
| static keepalive, 4 workers, 32 clients (`sk32`) | 663,080 | 638,278 | 698,673 (16 %) | 681,717 (14 %) | **680,922** (15 %) | 0.975x | 0.999x |
| static, a connection per request (`sc32`) | 129,328 | 125,781 | 128,873 (7 %) | 128,524 (8 %) | **127,075** (7 %) | 0.986x | 0.989x |
| proxied, one client in turn (`px`) | — | 16,605 | 16,695 (47 %) | 18,383 (16 %) | **19,875** (23 %) | 1.190x | 1.081x |
| proxied, `ab -c 1` (`ab1`) | 16,693 | 15,758 | 15,835 (6 %) | 15,745 (6 %) | **15,716** (4 %) | 0.992x | 0.998x |
| proxied, `ab -c 32` (`ab32`) | 18,096 | 17,761 | 18,063 (4 %) | 17,919 (3 %) | **17,984** (3 %) | 0.996x | 1.004x |

ws69's head (the exchange as 0.1.5 ships it) read px 19,080, ab1 15,616
and ab32 17,917 on its quiet box; this head reads 19,875, 15,716 and
17,984.

RSS of one process (`ev/rss.log`, `rss2.log`, ws70's `rss.sh`: a
2,000-request warm-up, 400,000 keepalive requests, 100,000 connections
of one request):

| binary | after 400,000 keepalive requests | growth a request | a connection |
|---|---|---|---|
| 0.1.5 (published), twice | 4,808 and 4,772 kB | 0 B | 0 B |
| the head, twice beside it | 5,008 and 4,916 kB | 0 B | 0 B |
| trunk at 0.2.33 (built here), three rounds | 5,000, 4,940, 4,884 kB | 0 B | 0 B |
| the head, three rounds beside it | 4,956, 4,920, 4,992 kB | 0 B | 0 B |

`ev/rssprobe.log` (`scripts/rssprobe.sh`: `/proc/<pid>/smaps_rollup`
at start, after the warm-up and after 400,000 requests, twice each):
the anonymous memory is the same in all three binaries — 636–652 kB at
start, 808–852 kB after 400,000 — and nine threads; the difference is
file-backed pages, 3,888–3,912 kB for the runner-built 0.1.5 against
4,028–4,096 kB for both binaries built here, at either pin.

**Held.**
- Static, the head ÷ 0.1.5 inside 0.95–1.05x (0.975x, 0.986x); ab1 and
  ab32 inside 0.90–1.10x (0.992x, 0.996x). Against the same source
  built here at 0.2.33 every row is 0.989–1.004x but px. **The pin
  moves no number**: every difference is inside its row's spread.
- RSS growth 0 B a request and 0 B a connection on both pins; against
  trunk built here the head is the same resident size (medians 4,956
  and 4,940 kB).
- Runner-VM parity, run **39686889778** (`tier measure`, `ws71-parity`
  at `fe99c55`, `ref_tree=v0.1.5`, 4 cpus, load 1.56, VALID SET):
  nginx ÷ ws71 close **1.068x** [1.045, 1.095], keepalive **0.977x**
  [0.973, 0.997], both MET (bar 1.10x); **ws71 ÷ 0.1.5 close 1.003x
  [0.987, 1.006], keepalive 1.001x [0.992, 1.018]**; at one worker
  0.997x and 1.049x (that cell refused: nginx's own keepalive spread,
  1.226). nginx ÷ 0.1.5 on this VM 1.071x and 0.990x (ws70's VM:
  1.032x, 0.933x).

**Wrong.**
- px, the head ÷ 0.1.5, is 1.190x, outside 0.90–1.10x. The row is
  bimodal (ws69's note): 0.1.5's five read 10,844–18,743, trunk-here's
  17,115–20,147, the head's 15,625–20,171; head ÷ trunk-here is 1.081x,
  inside both spreads. Not the pin.
- RSS against ws70's 0.1.5 range (4,664–4,740 kB) is +176 to +268 kB,
  outside the ±200 kB I predicted, and +108 to +236 kB against 0.1.5
  measured beside it. It is the build host, not the pin: the anonymous
  memory is equal, trunk built here at 0.2.33 is as large as the head,
  and the runner-built 0.1.5 maps fewer file-backed pages (ws70's note:
  the runner's binary is not kasumi's).

### Slips, named

- The staging script's first run named trunk by a short sha that is
  not its prefix (`06b079bc`); the checkout refused, nothing else ran
  past it, and it was re-run with the full sha.
- `build.sh` first staged `acmeca` in a directory named for each label;
  a debug build names its paths, so those digests (in the `build-*.log`
  rows) do not compare. Every `acmeca` in the table was rebuilt from one
  path (`logs/acmeca.log`; 0.2.33's two builds there are the same bytes
  as the first).
- The head's gauntlet tree was first checked out one commit short
  (`2941c8e`, before the surfaces); it was moved to `fe99c55` before the
  gauntlet reached it (`logs/g-head34.STATUS` names the head it ran).
- `wolf audit` was run once in trunk's gauntlet tree while that
  gauntlet ran; it writes nothing (`git status --ignored` after it), and
  the census step stayed green.

## 4. Evidence index

kasumi `~/lanes/ws71/` (sha256 prefixes): toolchains and digests: `toolchains.txt` 938a55040fbb…, `dl/digest-check.txt` a54b3119a193…; builds: `logs/build-t33.log` b1080e1f8507…, `logs/build-t33b.log` 0d098d330eb1…, `logs/build-p34s33.log` 058acb7ed843…, `logs/build-p34.log` 91cd14b9b590…, `logs/build-h34.log` 146c162fd195…, `logs/build-ctl.log` 8fbb4756a6e5…, `logs/acmeca.log` d8bf3a728017…; gauntlets: `logs/g-trunk33.log` 5c2a1b6d827a…, `logs/g-bare34.log` 2898dd308047…, `logs/g-head34.log` 1fe298832707…, `ev/ok-trunk33.txt` 4fd92921946a…, `ev/ok-bare34.txt` 201d02847a27…, `ev/ok-head34.txt` 2f21f8ccbbe0…; objects: `ev/objects-table.txt` ab4c1b966ba3…, `ev/objdiff-t33-p34s33.log` 3c96d9a7da65…, `ev/objdiff-p34s33-p34.log` 39cd59370c26…, `ev/objdiff-p34-h34.log` cbe1b86bfbf0…, `ev/objdiff-t33-p34.log` a0b6e88ccc91…, `ev/wcode.log` 9e92fb9f1c32…, `ev/wcode-std-rel.log` f7c31811beea…; the audit, at rest, the ladder: `ev/audit.log` cbacf0a11ef6…, `ev/rest-t33.log` 76701fc8ef87…, `ev/rest-p34s33.log` 46bac39ec3f9…, `ev/rest-p34.log` c30af1fe3657…, `ev/rest-h34.log` 53fd3f89e908…, `ev/ladder-t33.log` 4424c9db2b62…, `ev/ladder-h34.log` 57ddf7da45de…; the numbers: `ev/rss.log` 61b189dd7b68…, `ev/rss2.log` b2a9d4d99ef1…, `ev/rssprobe.log` e00dc6180789…, `ev/tput-rel5.log` 6c486afe3585…. Scripts (`scripts/`): acmeca.sh 9ed539e32009…, bt.sh 0f5df4bfff2e…, build.sh ae474bdcd8a5…, chain-g.sh b6e7e315cc49…, chain-n.sh 58a25de543da…, chain-r.sh 788b1ad3f95b…, digests.sh d78bdf23656b…, g.sh 5e39e59ccc60…, gsum.sh e6d0caeae544…, ladder.sh 9fed8639f76c…, launch.sh af28a25be9aa…, okdiff.sh 9a495ebd10aa…, rest.sh 84baede68eb4…, rssprobe.sh 4fce80be3228…, rss.sh 1defa5cb45e6…, stage.sh 3dea02097c71…, tput-in.sh 22ecb267f8cd…, tput.sh 5fbe88dec6ef…, objdiff.py f42c6d9c5988…, px69.py 8efb62d375e7…, summ.py 941b8f8adfac…, wcode1.py 087b26d2f54c…, wcode-all.py 4785f487f0ee…, wcode.py 894ce54cbf31…; `ladder.sh` is ws66's (`ebced9a9…`), `rss.sh`, `tput.sh`, `tput-in.sh`, `px69.py` and `summ.py` ws70's (§2's digests), each with this lane's paths.

nomad-1 `~/lanes/ws71/ev/`: `api-wolf-{1,2}.txt`, `api-lupin-{1,2}.txt`,
`api-lobo015-{1,2}.txt` (each pair identical), `parity-39686889778.log`
(the parity job's log).

CI: PR run 39686854924 (`tier pr` at `c443e22`, green); the parity
dispatch **39686889778** (`tier measure` on `ws71-parity` at `fe99c55`,
green, VALID SET; never merge evidence); the PR's `tier pr` and labelled
`tier full` at the final head are in the pull request.

## Not verified

macOS beyond CI (no macOS host here: the `gauntlet-macos` job of `tier
full` is the macOS row); the runner VM's static and proxied rows beyond
the parity leg; aarch64 linux and windows; PAX; a lobo built on the
release runner at 0.2.34 (the numbers' 0.1.5 column is runner-built, the
two trunk columns kasumi-built); why the release tier's inliner moves 32
of lobo's functions when an imported module gains functions nobody calls
(measured, not explained; the code it emits is equally correct by every
gate here).

## 5. Done-when

Branch `ws71`, PR #111 open and unmerged, five sections by name, commit
shas as bullets, a test checklist and `Footprint: cross-cutting` (a pin,
ruling #104); `tier pr` green at its head, the `full-matrix` label added
at that head, `wolf/tools/lane-audit.sh lobo ws71 111` run from the org
directory and passing but for `tier full`'s green; then the hand-back
with the full run's id (RULES.md §6). `ws71-parity` stays on origin as
the parity run's evidence. No issue is closed by this PR.
