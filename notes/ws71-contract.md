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
