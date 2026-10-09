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
