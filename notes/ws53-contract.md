# ws53 — lobo at 0.2.25

Wave 53, lane ws53 (Opus). Written 2026-10-07 (22:55Z) on lobo trunk
`21c6f8e`, before any archive is downloaded or unpacked and before any
edit to `src/` or `tools/`. The planning contract is
`sprints/wws/22-the-pin-0225/ws53-the-pin-0225.md` in
`wolffe-lang/wolf`; rules are `sprints/wave-53.md` down to
`wave-45.md`. The toolchain template is ws51/ws52 (archives by digest,
members by name, every build on kasumi under `setsid`, masks
recorded). The oracle is the pinned nginx 1.30.4 (`65595ac2…`), run,
never read.

## 1. Forbidden, absolutely

- nginx behaviour only from the pinned oracle; never read nginx, kernel
  or libc source.
- Never touch `~/scratch/wolf/lobo-demo`, `lang-demo`, `pax-demo`, port
  8088, the `wolf-demo` tunnel, `~/.cloudflared`, or port 8080.
  `demo/reel/` is not edited.
- The pin is taken from the RELEASE ARCHIVES by digest, never a clone,
  Homebrew or `~/.local/bin`.
- No `rm` outside `kasumi:~/lanes/ws53/`, `~/lanes/ws53/` on nomad-1
  (this worktree) and this lane's scratchpad. No deletion in any tree
  this lane did not create; the pinned nginx is COPIED from ws52's
  tree, digest checked, never touched in place.
- No `git add -A`. No edit to another lane's file. Nothing under
  `~/.claude`. No build on nomad-1. No package installs.
- No merge, tag or release. No `2>/dev/null` on a checkout. No commit
  trailers or PR attribution of any kind. Checksums carry a trailing `…`.
- No "seen red" without a run id, a sha, a path or a digest beside it.
  Strict evidence (wolf-lang#571): gauntlet logs capture stdout and
  stderr together with every SKIP line counted,
  `WOLF_PAIRING_REQUIRE_SIBLING=1` and lupin present; the stream-cap
  witness under `taskset -c 0`, `0-3` and all cores; SigBlk/SigIgn
  recorded beside every run.
- kasumi: `ssh kasumi "bash -c '…'"`, `scp`, `setsid` and a recorded
  pid, kill by that pid only (pgid 861 is tailscaled's), wait on a
  done-file, `command ls`, prune `target/` as I go (/home at 95 %).
- Waits print at least every five minutes. `gh run view`, never
  `gh run watch` without `--interval 60`. Cancel only my own
  superseded runs (the org has 20 job slots).

## 2. Inputs, verified (re-derived 2026-10-07, 22:40–22:55Z)

| input, as the contract states it | what origin says |
|---|---|
| wolf 0.2.25 = wolf-lang `6710f9e0`, release 406122367 | **holds**: tag `v0.2.25` (tag object `90f1c11e…`) peels to `6710f9e0cbc3a7264349093751ce7a46a407e473`; release 406122367, published 20:18:34Z. Asset digests from the release API: linux x86-64 `9d91f533…`, linux aarch64 `6b0bb90d…`, macOS arm64 `202c8d6c…`, windows `9debee73…` — all four as stated |
| lupin 0.1.48 = wolf-interp `531bf058`, release 405340127 | **holds**: tag `v0.1.48` (tag object `469352f5…`) peels to `531bf0581dea6bba4b1247edb2abada5214c18ab`; release 405340127. linux x86-64 `81cfd77a…`, aarch64 `a5c30957…`, macOS `27d86060…`, windows zip `9e4ea090…`, `lupin.exe` `6a6eb6e9…` — all five as stated |
| 0.2.25's "read this before you bump" | **holds** (CHANGELOG at `6710f9e0`): no new prelude names; #598/#601 (every call clobbers foreign memory: module `var`s, `extern "c" let`, raw-pointer memory; a lent `List` stays frozen), #600 (rangeopt bounds `x >> s` by the unsigned maximum). s214's downstream table (wolf-lang PR #607 §4, at lobo `b4975f7c`): **lobo native 1/1, release 2/2 objects changed**, by added loads only; "lobo: WIR explanation only" — no behaviour run on lobo. lupin 0.1.48 re-pinned on v0.2.24, 16 pins dropped |
| lobo trunk `21c6f8ec`, pinned 0.2.24 / 0.1.47, std `14f0ab2` | **holds**: `origin/trunk` = `21c6f8eca599…`; `wolf-toolchain.toml` [wolf] `294d626`, [lupin] `b3228cb` (0.1.47), [std] `14f0ab2c…`. ws52's gauntlet at this sha (`kasumi:~/lanes/ws52/g-head.log`): GREEN, release `fe2ee1cf…`, debug `8d2e197b…` |
| the std candidate (B151) | wolf-std trunk is **`2f389a7`** (sc54, std at 0.2.23); sc55 (std at 0.2.25) is in flight and unmerged. The candidates are `14f0ab2` (held) and `2f389a7` |
| what in lobo the 0.2.25 fixes can reach | lobo's `src/` has **no** module `var`, no `extern "c"` item, no raw pointer, no `packed`/`align`/layout query and no shift (grep at `21c6f8e`); the reloads s214 counted come from calls in the vendored std and the runtime boundary, not from a lobo store that was being forwarded |
| sites that name the pin | `wolf-toolchain.toml` (rev, version_line); `src/shell/shell.lu:100,105,461` (`toolchain_version`, `toolchain_pin`, the doc example); the stamp line of all 14 `.wolfi` (13 modules + `root.wolfi`). History prose naming 0.2.24 (README Limits, main.lu, serve.lu, budget.lu, stream_cap_e2e.lu, gauntlet comment) is dated measurement and stays |
| CI hosts | `ci.yml` runs one job, `gauntlet`, on ubuntu-latest (it clones the pinned revs with `WOLF_CI_TOKEN`; dispatch with `parity=true` runs the bar instead). `release.yml` on `workflow_dispatch` is a rehearsal: `create`/`publish` skip, `dist` and `smoke` run on linux x86-64 AND macOS arm64 |

## 3. Prediction, committed before the archives are unpacked

**P1, the pin and its stamps.** Both archives match the API digests
above. 0.2.25's linux x86-64 members change by name (`wolf`,
`libwolf_rt.a`, `wolf-cimport-worker` at least; the runtime moves
because #601's clobber is in the builder, and the runtime is built by
it); `lupin` changes. `wolf --version` reads `wolf 0.2.25 (wolfgang,
pin 6710f9e)`; lupin's version line names its conformance pin
`294d626` (v0.2.24), so [lupin]'s `version_line` changes in two
places, not one. The stamp moves in `wolf-toolchain.toml`,
`shell.lu`'s two constants and doc line, and the 14 `.wolfi` stamp
lines; **no `export_hash` or `pkg_hash` moves** (no surface changes).

**P2, B151.** Trunk's `src/` built at 0.2.25 exits 0 with **zero
diagnostics** on both tiers (`--error-limit=0`), against std
`14f0ab2` and `2f389a7` alike, and the two std trees give
**byte-identical** binaries on each tier (as at 0.2.22–0.2.24): the
std pin **holds at `14f0ab2`**.

**P3, binaries.** Both `lobo-debug` and `lobo-release` **change
digest** at 0.2.25 (s214: native 1/1, release 2/2 on lobo), each
**larger by under 1 %** (only added reloads after calls and the pure
ops on them; no store, call or branch removed). Two release builds of
one tree are byte-identical. Falsified by an unchanged digest, a
binary that shrinks, a growth of 1 % or more, or two builds that
differ.

**P4, the gauntlet.** GREEN on kasumi at the pin commit and at the
head with **ws52's counts unchanged**: corpus 313/313 lane-runs (the
70 lupin lane-runs included: 0.1.48's moves are is73's constructs and
#205, none of which lobo's corpus uses), differential 22/22, proxy
8/8, control 16/16, logdiff 4/4, dryrun GREEN, signal 21/21, prefork
38/38, replay byte-identical by seed, metrics GREEN, membudget 17/17,
resolver 9/9, tls-interop/renewal/acme GREEN, census clean, `lobo-stamp`
ok. The same **2 SKIP lines**, both named (signal's linux-only header,
membudget's wolf-lang#191 gate). No row changes verdict. Falsified by
any red or any moved count.

**P5, membudget.** Retention stays **19 KB/req** (plain) and **20
KB/req** (through the capped proc), both < 64; every growth figure and
round B's string retention (7964 KB at ws52's head) within **±5 %**.
A reload is a load of a pointer already live, so no allocation moves.

**P6, the stream-cap witness** (`tests/serve/stream_cap_e2e.lu`, both
phases, built at the head) under `taskset -c 0`, `0-3` and all 16
kasumi cpus, against both `lobo-debug` and `lobo-release`, at the
0.2.24 pin and at 0.2.25: **green in all 12 runs**, rooms 4 / 10 / 46.
The pool (s210's `4·t - 2`) is runtime code 0.2.25 does not touch.
Falsified by any red.

**P7, runner parity.** `ci.yml` dispatched with `parity=true`,
`ref_tree` = trunk `21c6f8e` (0.2.24): this ÷ ref within **0.97x–1.03x**
on both shapes (reloads of a hot cache line cost below the runner's
noise); nginx ÷ lobo stays **outside the 1.10 bar** (~1.15x close,
~1.25x keepalive, ws52's numbers ± noise). If the VM's spread refuses
the set, it is reported refused.

**P8, CI.** `ci.yml`'s gauntlet green at the head (linux x86-64);
a `release.yml` rehearsal green on both dist hosts (linux x86-64 and
macOS arm64: build, pack twice identical, smoke). A planted break
(the stamp constant left at 0.2.24 while the pin moves) is **red** in
CI at `lobo-stamp`, then reverted.
