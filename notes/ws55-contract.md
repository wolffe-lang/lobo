# ws55 — lobo at 0.2.26

Wave 53, lane ws55 (Opus). Written 2026-10-09 (18:30–19:00Z) on lobo
trunk `92d860f`, before any archive is downloaded or unpacked and
before any edit to `src/`, `tools/` or `wolf.pkg`. The planning
contract is `sprints/wws/24-the-pin-0226/ws55-the-pin-0226.md` in
`wolffe-lang/wolf`; rules are `sprints/wave-53.md` down to
`wave-45.md`. The toolchain template is ws53's (archives by digest,
members by name, every build on kasumi under `setsid`, masks
recorded). The oracle is the pinned nginx 1.30.4 (ws47's copy,
`65595ac2…`), run, never read.

## 1. Forbidden, absolutely

- nginx behaviour only from the pinned oracle (ws47's copy, COPIED to
  `kasumi:~/lanes/ws55/nginx-oracle`, digest checked); never read
  nginx, kernel or libc source.
- Never touch `~/scratch/wolf/*`, port 8088, the `wolf-demo` tunnel,
  `~/.cloudflared` or port 8080. `demo/reel/` is not edited.
- The pin is taken from the RELEASE ARCHIVES by digest, never a clone,
  Homebrew or `~/.local/bin`. (CI builds the pinned revs from source,
  as `ci.yml` has since ws13; that is the CI's acquisition, not this
  lane's pin.)
- No `rm` outside `kasumi:~/lanes/ws55/`, `~/lanes/ws55/` on nomad-1
  (this private clone's parent) and this lane's scratchpad. No deletion
  in any tree this lane did not create.
- No `git add -A`. No edit to another lane's file. Nothing under
  `~/.claude`. No build on nomad-1 (no `wolf build`, no `cargo`). No
  package installs, no sudo.
- No merge, tag or release; close no issue. No `2>/dev/null` on a
  checkout. No commit trailers or PR attribution of any kind.
  Checksums carry a trailing `…`.
- No "seen red" without a run id, sha, path or digest beside it.
  Strict evidence (wolf-lang#571): gauntlets run with
  `WOLF_PAIRING_REQUIRE_SIBLING=1`, lupin present, stdout and stderr
  together, every SKIP line counted; the stream-cap witness under
  `taskset -c 0`, `0-3` and all cores; SigBlk/SigIgn recorded beside
  every run.
- kasumi: `ssh kasumi "bash -c '( setsid nohup … & echo $! > pid )'"`,
  done-files, kill by recorded pid only (pgid 861 is tailscaled's),
  `command ls`, `CARGO_INCREMENTAL=0` for anything cargo (none
  planned), one lobo clone, `target/` pruned as I go (/home at 96 %,
  38 GB free at 18:47Z).
- Waits print at least every five minutes. `gh run view`, never
  `gh run watch` without `--interval 60`. Cancel only my own
  superseded runs (the org has 20 job slots).

## 2. Inputs, verified (re-derived 2026-10-09, 18:40–19:00Z)

| input, as the contract states it | what origin says |
|---|---|
| wolf 0.2.26 = wolf-lang `89dc1394`, release published | **holds**: tag `v0.2.26` (tag object `fdc73f26…`) peels to `89dc139443da38078df6093568da87bc6d0ee6f9`; release **408143286**, published 17:48:26Z, not a draft. Asset digests from the release API: linux x86-64 `05acdc5e…`, linux aarch64 `8b019b64…`, macOS arm64 `8ea7ef3b…`, windows `9cb6958d…` — all four as stated |
| lupin 0.1.49 = wolf-interp `f516a5f` | **holds**: tag `v0.1.49` (tag object `5d14986a…`) peels to `f516a5f4ea4341acd3a30f3e5cdd4327aede1912`; release **408028965**, 15:05:40Z. linux x86-64 `84911a35…`, aarch64 `e1f53d15…`, macOS `ad188d58…`, windows zip `ebff44ab…`, `lupin.exe` `64212006…` — all five as stated |
| what 0.2.26 changes for a downstream | **holds** (CHANGELOG at `89dc1394`, "Read this before you bump the pin"): ten new prelude names (`fs_copy_chunk`, `os_spawn_fds`, `os_pipe`, `os_chdir`, `os_isatty`, `os_error`, `os_error_text`, `bytes_find`, `bytes_count`, `never`); s217's capabilities derived from the host builtins a package's own files reach and the std modules it imports; `wolf audit --ci` refuses a manifest whose directory holds no wolf source and names lobo as that case ("If lobo's manifest did govern `src/`, it would need `capabilities: [env, exec, fs, net]`"); #618 (E1010 for a `str` call result held past its region; s216 measured lobo byte-identical); `copy region` (#56), `-> never` (#50), `!` on integers (#51); fds 0–2 served directly (s200). The pairing is lupin 0.1.49 at spec pin `294d626`, unchanged |
| the codeless manifest | **holds, read in the driver at `89dc1394`**: a build reads `wolf.pkg` only from the ENTRY's directory (`compile_native`: `root = file.parent()`, `pkg_cmd::project_for_build(root, …)`); lobo builds `./src/main.lu`, so `src/` is the root and the repository-root `wolf.pkg` governs nothing, and E1504 never runs on lobo. `wolf audit --ci` on a manifest with no source beside it prints "cannot derive capabilities from the code" and exits 1 (`crates/wolf_driver/tests/cap_reach.rs`, `an_audit_that_cannot_read_the_code_vouches_for_nothing`, which names lobo's shape). A project build reads `wolf.sum` if present and writes none |
| the sandbox table (which builtin is which capability) | `crates/wolf_sema/src/ctfe/intrinsics.rs` `host_stub` at `89dc1394`: `fs_*`/`read_text` → fs; `net_*` → net; `env_*`, `os_cwd`, `os_exe`, `os_cpus`, `os_chdir` → env; `os_spawn*`, `os_wait`, `os_kill`, `os_exit`, `os_pipe`, `os_signal_*` → exec; stdio, clock (`time_*`, `clock_ms`), random (`random_seed`, `os_random`) and `os_isatty` carry nothing (ruling #53) |
| lobo trunk `92d860f` (ws54) | **holds**: `origin/trunk` = `92d860f35ff2…`; `wolf-toolchain.toml` [wolf] `6710f9e0` (0.2.25), [lupin] `531bf058` (0.1.48), [std] `14f0ab2c…`. One lobo issue open (#62); no lobo PR open |
| what lobo's own code reaches (grep at `92d860f`, calls only) | **fs**: `fs_close` 28, `fs_read_text` 12, `fs_read_chunk` 9, `fs_exists` 8, `fs_open_mode` 6, `fs_remove` 6, `fs_read_bytes` 4, `fs_create_dir_all` 4, `fs_write_text` 3, `fs_rename`, `fs_is_dir`, `fs_fstat` 2 each, `fs_write_chunk`, `fs_read_dir`, `fs_open` 1 each. **net**: `net_close` 56, `net_deadline` 18, `net_write` 15, `net_read` 13, `net_write_bytes` 11, `net_port` 8, `net_listen` 8, `net_connect` 7, `net_accept` 6, `net_read_bytes` 4, `net_wait` 3, `net_nodelay`, `net_listen_with`, `net_adopt_listener` 2 each, `net_writev_head`, `net_listen_unix`, `net_connect_unix` 1 each. **env**: `os_cpus` 6, `os_exe` 1, `env_args` 1. **exec**: `os_spawn_with` 3, `os_wait` 2, `os_signal_listen` 2, `os_signal_raise` 2, `os_spawn`, `os_signal_wait`, `os_kill` 1 each. Uncharged: `time_*` (clock), `os_random` (random). std imports: `std.net` (2), `std.x.tls.cert` (5), `std.x.tls.client` (2), `std.x.tls.handshake`, `std.x.tls.record`, `std.x.jose`, `std.x.crypto.curve25519` (3), `std.hex`, `std.base64` |
| a declaration shadowing a new prelude name (W0304) | **none** in `src/` or `tests/` (grep for `fn|let|var|const|type|struct|enum` + each of the ten) |
| lobo's std candidate (B151) | wolf-std trunk is **`0f74ec5`** (sc55, std at 0.2.25); sc57 (std at 0.2.26) is in flight, unmerged. The candidates are `14f0ab2` (held since ws42) and `0f74ec5` |
| sites that name the pin | `wolf-toolchain.toml` (rev, version_line ×2); `src/shell/shell.lu:100,105,461` (`toolchain_version`, `toolchain_pin`, the doc example); the stamp line of all 14 `.wolfi`. Dated prose naming 0.2.25 (README parity rows, `userconf.lu:59`) is measurement and stays |
| sites that name `wolf.pkg` at the root | `tools/lobo-gauntlet:39` (the manifest step), `tools/lobo-stamp:90,108` (the version site), and prose in `src/main.lu:98`, `src/shell/shell.lu:66,78,85`, `tests/shell/version_text.lu:18,23`. `tools/lobo-dist` packs no `wolf.pkg`; no workflow names it |
| CI hosts | `ci.yml`: `gauntlet` (ubuntu-latest) and `gauntlet-macos` (macos-latest, ws54), both building the pinned revs from source; `workflow_dispatch` with `parity=true` runs the bar (`ref_tree` names the tree to compare). `release.yml` on `workflow_dispatch` is the dist rehearsal on linux x86-64 and macOS arm64 |

## 3. Prediction, committed before the archives are unpacked

**P1, the pin and its stamps.** Both archives match the API digests
above. 0.2.26's linux x86-64 members change by name (`wolf`,
`libwolf_rt.a`, `wolf-cimport-worker`, `libwolf_rt_none.a`, `wolf.1`,
`README.md`); `_wolf`, `wolf.bash`, `wolf.fish` and the licences hold
(no new subcommand or flag). `lupin` changes. `wolf --version` reads
`wolf 0.2.26 (wolfgang, pin 89dc139)`; lupin's line reads `lupin
0.1.49 (wolf-interp, reference interpreter at pin 294d626)` — the
conformance pin does not move. The stamp moves in
`wolf-toolchain.toml`, `shell.lu`'s two constants and doc line, and
the 14 `.wolfi` stamp lines; **no `export_hash` or `pkg_hash` moves**.

**P2, B151.** Trunk's `src/` built at 0.2.26 exits 0 with **zero
diagnostics** on both tiers (`--error-limit=0`; no W0304, no #618
E1010 — s216 measured lobo), against std `14f0ab2` and `0f74ec5`
alike, and the two std trees give **byte-identical** binaries on each
tier: the std pin **holds at `14f0ab2`**. Falsified by any diagnostic
or a byte that moves between the std trees.

**P3, binaries.** Both `lobo-debug` and `lobo-release` **change** at
0.2.26 against 0.2.25 even after `objcopy --strip-debug
--remove-section .note.gnu.build-id`: the runtime lobo links moved
(s200 rewrote the fs read/write paths lobo calls — `fs_read_chunk`,
`fs_read_bytes` — and `print`'s lock; s215 adds runtime symbols).
Stripped release `.text` moves by **under 1 %** either way. Two
release builds of one tree are byte-identical; the release digest is
path-free and the debug digest compares within one path only.
Falsified by an unchanged stripped binary, a `.text` move of 1 % or
more, or two release builds that differ.

**P4, the manifest (item 3).**
- (a) At trunk's layout and 0.2.26, `wolf audit --ci` in the repo root
  **exits 1** ("cannot derive capabilities from the code … nothing is
  vouched for"); `wolf audit` without `--ci` exits 0.
- (b) The fix is to make the manifest govern the real build: **`git mv
  wolf.pkg src/wolf.pkg`**, beside the entry `wolf build` is given,
  with `capabilities: [env, exec, fs, net]`. With the move and NO
  capabilities line, both tiers are **refused with E1504** for each of
  the four (std imports add nothing beyond `net`), and `wolf audit
  --ci --dir src` exits 1 with `effective` = those four; with the line,
  both tiers build with zero diagnostics and the audit exits 0 with
  one reason line per capability, each naming a builtin from the
  census in §2. Dropping any one of the four re-reds both.
- (c) The move changes **no binary byte** on either tier (the manifest
  carries no lints, no target, no asm, no dependency; a project build
  writes nothing) and **no `.wolfi` hash**. Falsified by any moved
  byte or hash.
- (d) The gauntlet's manifest step gains `wolf audit --ci --dir src`
  so the declaration is gated, not described; `lobo-stamp` reads the
  version from `src/wolf.pkg`.

**P5, the gauntlet.** GREEN on kasumi at trunk (0.2.25, the control)
and at the head with **the control's counts unchanged**: corpus
313/313 lane-runs (the lupin lane included: 0.1.49 moves is74's
volatile/atomics and the s200/s213/s215/s216 mirrors, none of which
lobo's corpus uses), control 19/19, signal 21/21, prefork 38/38,
membudget 17/17, resolver 9/9, differential, proxy, logdiff, dryrun,
metrics, tls-interop/renewal, acme, dist, census GREEN. The same **2
SKIP lines**, both named (signal's linux-only header, membudget's
wolf-lang#191 gate). No row changes verdict. Falsified by any red or
any moved count.

**P6, membudget.** Retention stays **19–20 KB/req** (plain and
through the capped proc), < 64; round B's string retention within
**±5 %** of the control's. #618 adds a check, not an allocation.

**P7, the stream-cap witness** (`tests/serve/stream_cap_e2e.lu`)
under `taskset -c 0`, `0-3` and all 16 cpus, against `lobo-debug` and
`lobo-release`, at trunk (0.2.25) and at the head (0.2.26): **green
in all 12 runs**, rooms 4 / 10 / 46 (the pool's `4·t - 2` is runtime
code 0.2.26 does not touch). Falsified by any red or a moved room.

**P8, runner parity.** `ci.yml` dispatched with `parity=true`,
`ref_tree` = trunk `92d860f` (0.2.25): head ÷ trunk within
**0.97x–1.03x** on both shapes; nginx ÷ lobo stays **outside the
1.10 bar** (the VM class decides between ~1.17x and ~1.26x). A set
the tool refuses is reported refused.

**P9, CI.** Both gauntlet jobs (linux, macOS) green at the head. A
planted break — `exec` dropped from `src/wolf.pkg`'s capabilities —
is **red** in CI at the manifest step (`wolf audit --ci`) on both
jobs, then reverted.

### §3 against the measurement (written at the close, 2026-10-09)

- **P1: held.** All four linux x86-64 archives digest-ok
  (`kasumi:~/lanes/ws55/dl/digest-check.txt` 1c4970dd…). Members by
  name: `wolf` 8373b0cd… -> 272e0888…, `libwolf_rt.a` 6ac563e7… ->
  679d77e1…, `wolf-cimport-worker` 9c423c74… -> f05db3d1…,
  `libwolf_rt_none.a` 110f062a… -> 11708550…, `wolf.1` and `README.md`
  move; `_wolf`, `wolf.bash`, `wolf.fish` and the licences hold.
  `lupin` 734caee6… -> 6d057eb1…. Version lines as predicted, lupin's
  conformance pin still `294d626` (`toolchain-tc-0226.txt` 62927161…).
  14 `.wolfi` stamp lines moved, no hash: the gauntlet's freshness step
  agrees at `468ffac`.
- **P2: held.** Zero diagnostics, both tiers, both std trees, and the
  two trees byte-identical (`builds-trunk.log` 57a3ccdc…). std holds
  at `14f0ab2`.
- **P3: held.** Stripped (`objcopy --strip-debug --remove-section
  .note.gnu.build-id`) both binaries still differ; stripped release
  `.text` 1,634,846 -> 1,640,810 (+0.36 %); two release builds
  identical. Not predicted, and harmless: the unstripped release grows
  329,232 bytes (+2.6 %), almost all of it debug info; the runtime
  crate's hash changed, so every runtime symbol's mangled name did.
- **P4: (a), (b), (d) held; (c) half falsified.** (a) `wolf audit` at
  the root exits 0 with "cannot derive capabilities from the code", and
  `--ci` exits 1 ("nothing is vouched for"). (b) Moved with no
  capabilities, both tiers refuse with four E1504 (one per capability)
  and the audit's `effective` is `[net, fs, exec, env]`; with the four
  declared both tiers build clean and the audit exits 0; dropping any
  one refuses both tiers naming it (`mf.log` 46ea177b…). std imports
  reach only `net` (`stdreach.log` 46464afd…). (c) The release binary
  is byte-identical with and without the manifest (`3085ddcf…`) and no
  `.wolfi` moves (`wolf interface ./src` diff 0 lines); **the debug
  binary's bytes move** (same size, 255,794 bytes differ stripped):
  the build interns the manifest into the source map before the entry,
  every file index shifts by one, and the debug tier names its per-file
  path symbols `_W.site.<file index>` (`mfd.log` 1cee4cad…; two builds
  each way, each pair identical).
- **P5: held, with one count moved by this lane.** GREEN on kasumi at
  trunk (0.2.25), the pin `468ffac`, the manifest head `17ade8e` and
  the fix head `389de6f`, with the same counts and the same 2 named
  SKIP lines; at `389de6f` the corpus is 314/314, the one new lane-run
  being this lane's witness `tests/acme/tick_clock.lu`.
- **P6: held.** Retention 20 / 20 KB a request at both pins (the
  prediction said 19–20); round B 8052 KB at both.
- **P7: held.** 12 of 12 green, rooms 4 / 10 / 46, identical numbers.
- **P8: held on the gating cells.** 1.001x close, 0.999x keepalive at
  N = 4 (run 37979191081, VALID). N = 1 keepalive read 1.040x
  [0.978, 1.080], the noisy cell, not gated. The bar NOT MET
  (1.153x / 1.254x).
- **P9: the plant held; "both jobs green at the head" was falsified
  until this lane fixed lobo.** The plant (`1c36f9f`) went red at the
  manifest step on both jobs (run 37979239121). But macOS went red at
  the acme rig's coexistence case at 0.2.26 on every head from the pin
  on (runs 37976767680, 37978554212, 37981049172), never on linux
  (kasumi under five cpusets at both pins, `acmets.log` 633e111b…).
  Diagnosed with timestamped traces on a throwaway branch (`ws55-diag`,
  runs 37985235837 and 37993340947 at 0.2.26; `ws55-diag25`, run
  37993343981, the same tree at 0.2.25): lobo's ACME `tick` scheduled
  from the pass's `now_ms`, read before the pass's wait and before the
  step, so the authz poll ran early into the CA's single-threaded
  validation (both sides waiting until lobo's 5 s deadline) and the
  retry after it fired at once into a CA still busy. At 0.2.25 the same
  first-attempt overlap appears but resolves inside the deadline; at
  0.2.26 on macOS it did not (5 of 6 samples red, against 0 of 6 at
  0.2.25). Why the timing moved at 0.2.26 is measured, not explained;
  the defect is lobo's. Fixed at `389de6f` (schedule from the clock
  after the step), witness `tests/acme/tick_clock.lu` RED before
  (`tickw.log`, the second tick retried at once, 10 s) and GREEN after;
  macOS green in CI (run 37995891208) and 3 of 3 diagnostic repeats
  (run 37995901836). The rest (each transaction blocks the loop; the
  rig's race) filed as lobo#65.

Corrections to §2: none of the inputs drifted. To §1: the stray
`/tmp/ws55-acmeca.lu` (one `scp` target, this lane's own file) was
moved into `~/lanes/ws55/k/`, not left behind.

## 4. Evidence index

kasumi paths are under `~/lanes/ws55/`.

| claim | artifact |
|---|---|
| the archives by digest | `dl/digest-check.txt` 1c4970dd… (wolf 0.2.26 `05acdc5e…`, lupin 0.1.49 `84911a35…`, wolf 0.2.25 `9d91f533…`, lupin 0.1.48 `81cfd77a…`); members `toolchain-tc-0226.txt` 62927161…, `toolchain-tc-0225.txt` 984afe4f…, `toolchain-tc-0226-std0f.txt` d412d6e8…; nginx `65595ac2…` (`nginx.sha256` 15e6c86a…) |
| the prediction before unpacking | commit `749e5fc` (pushed 18:50:22Z; `stage.sh` started 18:50:47Z) |
| B151 and the binaries | `builds-trunk.log` 57a3ccdc… at `92d860f` |
| the manifest: refusals, audit, binaries, interface | `mf.log` 46ea177b…, `mf/*.out`; `mfd.log` 1cee4cad…; `stdreach.log` 46464afd… |
| gauntlet GREEN at 0.2.25 (trunk) | `g-before.log` e7a4bbf2… at `92d860f`: exit 0; SigBlk 0x10000 / SigIgn 0x7; 2 SKIP lines, named |
| gauntlet GREEN at 0.2.26 (the pin) | `g-pin.log` adae4323… at `468ffac` |
| gauntlet GREEN with the manifest | `g-head.log` ca698bc6… at `17ade8e` |
| gauntlet GREEN with the ACME fix | `g-head2.log` d480a151… at `389de6f` (corpus 314/314) |
| the stream-cap witness, 3 cpusets × 2 tiers × 2 pins | `cap-before.log` a26f0079…, `cap-pin.log` b269677f… |
| the acme rig on linux under five cpusets, both pins | `acmets.log` 633e111b… |
| the ACME witness red before, green after | `tickw.log` (unfixed: assert at `tick_clock.lu:52`, 10 s; fixed: exit 0, 5 s) |
| runner parity | run **37979191081** (VALID) |
| CI at the pin | run 37976767680 (linux green; macOS red at acme coexistence) |
| planted break red in CI | run **37979239121** at `1c36f9f` (manifest step, both jobs), reverted at `e109715` |
| the macOS red and its traces | runs 37978554212, 37981049172 (red); 37993340947 (0.2.26 traces), 37993343981 (0.2.25 traces), 37995901836 (the fix, 3 of 3 green); branches `ws55-diag`, `ws55-diag25` (throwaway, never merged) |
| CI green with the fix | run **37995891208** at `389de6f` |
| CI at the head | in the PR body (the head is this commit's child) |

## 5. Done-when

- [x] Branch `ws55` on origin; PR #64 open against `trunk`, unmerged.
- [x] The pin as its own commit (`5df7bea`), the stamps after it
  (`8e269fb`, `468ffac`).
- [x] The manifest governs the build (`d853bc1`), the audit gates it
  (`b36adb4`), each capability argued (`17ade8e`).
- [x] Binaries stripped-compared, gauntlet on kasumi at four heads,
  membudget, the stream-cap witness under three cpusets, runner parity.
- [x] Planted break red in CI by run id, reverted.
- [x] Every move against the prediction explained; the macOS red fixed
  here (`389de6f`), the rest filed (lobo#65).
- [ ] CI green at the head sha on linux and macOS; the throwaway
  branches `ws55-diag` and `ws55-diag25` deleted from origin; kasumi
  worktrees removed and `target/` pruned (logs kept); no orphan pids.
  Nothing closed by this lane.
