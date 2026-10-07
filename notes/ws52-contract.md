# ws52 — the cleanup: the #146 `WOLF_MIDEND` flip-back, and lobo#55

Wave 53, lane ws52 (Opus). Written 2026-10-07 on lobo trunk `9167cb5`,
before any measurement and before any edit to `src/` or `tools/`. The
planning contract is `sprints/wws/21-the-cleanup/ws52-the-cleanup.md`
in `wolffe-lang/wolf`; rules are `sprints/wave-53.md` down to
`wave-45.md`. The toolchain template is ws51 (archives by digest,
members by name, every build on kasumi under `setsid`, masks
recorded). The oracle for lobo#55 is the pinned nginx 1.30.4 in
`tests/differential/bin` (`65595ac2…`), run, never read; the oracle
for the flip is lobo's own gauntlet and ws47's parity rig.

## 1. Forbidden, absolutely

- nginx behaviour only from the pinned oracle; never read nginx
  source. Never read kernel or libc source.
- Never touch `~/scratch/wolf/lobo-demo`, `~/scratch/wolf/lang-demo`,
  `~/scratch/wolf/pax-demo`, port 8088, the `wolf-demo` tunnel,
  `~/.cloudflared`, or port 8080. `demo/reel/` in this repo is not
  edited either.
- The pin does not move: wolf 0.2.24 (`294d626`) / lupin 0.1.47
  (`b3228cb`) / std `14f0ab2`, from the release archives by digest.
- No `rm` outside `kasumi:~/lanes/ws52/`, this worktree
  (`~/lanes/ws52/lobo` on nomad-1) and this lane's scratchpad. No
  deletion in any tree this lane did not create; the pinned nginx and
  `ab` are COPIED from ws47's tree, never touched in place.
- No `git add -A`. No edit to another lane's file. Nothing under
  `~/.claude`. No build on nomad-1. No package installs. No `sudo`.
- No merge, tag or release. No `2>/dev/null` on a checkout. No commit
  trailers or PR attribution of any kind. Checksums carry a trailing `…`.
- No "seen red" without a run id, a sha, a path or a digest beside it.
  Strict evidence (wolf-lang#571): gauntlet logs capture stdout and
  stderr together with every SKIP line counted,
  `WOLF_PAIRING_REQUIRE_SIBLING=1` and lupin present, test runs
  `--nocapture`-equivalent; concurrency witnesses also under
  `taskset -c 0-3`; SigBlk/SigIgn recorded beside every signal run.
- kasumi: `ssh kasumi "bash -c '…'"`, `scp` never a pipe, `setsid` and a
  recorded pid, kill by that pid only (never a pattern or a group:
  pgid 861 is tailscaled's), wait on a done-file, `command ls`, prune
  `target/` as I go (/home at 95 %).
- Waits print at least every five minutes. `gh run view`, never
  `gh run watch` without `--interval 60`. Cancel only my own superseded
  runs (the org has 20 job slots).

## 2. Inputs, verified (re-derived 2026-10-07, 19:35–19:50Z)

| input, as the contract states it | what origin and the hosts say |
|---|---|
| lobo trunk `9167cb5` (ws51) | **holds**: `origin/trunk` is `9167cb5`; `wolf-toolchain.toml` pins wolf `294d626` (`wolf 0.2.24 (wolfgang, pin 294d626)`), lupin 0.1.47, std `14f0ab2` |
| the pin's archives | staged on kasumi by digest (`kasumi:~/lanes/ws52/dl/digest-check.txt`): wolf 0.2.24 linux x86-64 `501d6d3f…`, lupin 0.1.47 `0ddc4ff3…`, each asserted non-empty then equal. Members by name (`toolchain-tc-0224.txt`): `wolf` `b8562655…`, `libwolf_rt.a` `644b5670…`, `wolf-cimport-worker` `905f1898…`, `lupin` `4b60bea5…` — ws51's digests; std `STD-REV` `14f0ab2c…` |
| `wolf-toolchain.toml`'s #146 notes at ~81, ~118, ~167, ~203 | **holds, and there are more**: "flip-back is STILL owed" at lines 81, 118, 167, **204**, 239 and 270; the ws37 measurement at 383–396; ws51's correction at 556; and a STALE "the issue is OPEN" in the `[std]` caveat at 689–693 |
| wolf-lang#146 closed | **holds**: closed 2026-09-15 (s162, PR #388). At v0.2.24 the driver calls `WOLF_MIDEND=0` "a MEASUREMENT mode, never a supported build mode" (`crates/wolf_driver/src/main.rs:1206–1213` at `294d626`): it skips the s42 mid-end and the s43 whole-program phase. Unset, `--release` runs both |
| where lobo passes `WOLF_MIDEND=0` | `tools/lobo-gauntlet:71`, `tools/lobo-dist:130` (and its text at 24, 129, 169), `.github/workflows/ci.yml:249, 266, 300, 323`. Prose: `src/shell/shell.lu:475` (the `-V` tier line, a user-visible string; `tests/shell/version_text.lu:49` asserts only `tier: two-tier`), `src/acme/flow.lu:181` (a comment), `docs/BUDGET.md:248–261`, `docs/PARITY.md:32`, `docs/PROFILE.md:13, 112, 125, 1998` (history, dated). `release.yml` builds through `tools/lobo-dist` |
| ws47's parity rig on kasumi | **drift**: ws47's three kasumi sets were all REFUSED at N = 16 (nginx's own spread; PARITY.md's 2026-10-02 row). The rig's two-tree mode (`LOBO_REF`, ws25) measures one tree against another in one set, so the flip is read as the DELTA mid-end-on ÷ mid-end-off against one nginx, at N = 4 under `taskset -c 0-3` beside N = 16. `ab` is not on kasumi; ws47's lane-local `kasumi:~/lanes/ws47/ab/ab` is copied. kasumi load 4.26 / 3.18 / 2.49 at 19:47Z (other lanes), so sets wait for quiet or are refused by the tool |
| lobo#55's report | **holds** as filed (ws49, kasumi, wolf 0.2.22): `root www` under `-p P` from another folder answers 404 where nginx serves `P/www`. The mechanism re-derived at `9167cb5`: `config/parse.lu:758–779` stores `root`/`alias` as written into `rr_root`/`rr_alias`; `http.decide` (`src/http/http.lu:1355, 1359`) joins them with the URI; the serve path stats the result against the cwd. `config.load(prefix, conf)` already receives the prefix and does not use it for these two. `alias` relative is the filer's code reading, unmeasured |
| how lobo resolves `-p` | `src/shell/shell.lu:201` defaults the prefix to `.`; `-p` takes the argument as written (no trailing-slash normalisation). Every other path (`pid`, logs, the control socket, `ssl_*`, the cert store) joins as `{prefix}/{p}` when relative (`shell.pid_path`, `main.resolve_log_path`, `sslcert.against_prefix`), so `-p P/` gives `P//logs` — harmless to the fs, visible in printed paths |
| who sees a resolved root | the dry-run (`-t --request`) prints `decision: would serve: <fs_path>` (`src/dryrun/dryrun.lu:728, 734`) and probes it. `tests/dryrun/probes/distro-default.probe` runs `-p tests/config-corpus/distro-default` with `root html`, so its pinned stanza moves with a fix. The reel (`demo/reel/`) runs without `-p`, so under the default prefix `.` its printed paths must not move |
| the named delta | `tools/lobo-control-differential` row 5 measures `root www` beside the oracle and prints **D5**, non-gating |

## 3. Prediction, committed before the first build

**F1, binaries.** With `WOLF_MIDEND` unset, `target/lobo-release`
CHANGES (a different digest from the `WOLF_MIDEND=0` build of the same
tree) and is **smaller by 5–25 %** (whole-program dedup outweighs
cross-module inlining in a 30-module program). `target/lobo-debug` is
**byte-identical** both ways (the variable reaches only `--release`).
Two mid-end-on release builds of one tree are **byte-identical** to
each other (#503 fixed in 0.2.21). Falsified by an unchanged release
digest, a release binary larger than the `=0` one or more than 25 %
smaller, a moved debug digest, or two on-builds that differ.

**F2, tests.** The gauntlet is green both ways at one tree with the
**same counts**: corpus lane-runs, differential 22/22, proxy 8/8,
control 9/9 (10/10 or more after #55's rows), signal 21/21, membudget
17/17, `lobo-stamp: ok`. No row changes verdict. Falsified by any red,
or any count that moves with the flag alone.

**F3, bench.** On kasumi, the two-tree parity set (this tree mid-end
on, `LOBO_REF` = the same tree `=0`, one nginx) reads the delta
**lobo(on) ÷ lobo(off) between 1.00x and 1.10x** on both shapes at
N = 4 (`taskset -c 0-3`): the request path is syscall-bound (ws47:
lobo + libc 24.5 % of samples at one hand), so the mid-end can move at
most the user-space quarter. `lobo-membudget`'s figures move by no
more than ±5 %. Falsified by a delta under 0.98x (the mid-end made it
slower) or above 1.10x, or a membudget figure outside ±5 %. If the box
will not quiet, the set is refused by the tool and reported refused.

**F4, #55 against the oracle.** Both servers started from a folder
that is not the prefix:

| row | config | nginx 1.30.4 | lobo at `9167cb5` | lobo after |
|---|---|---|---|---|
| a | `root www;`, `-p P/` | serves `P/www` | 404 (red) | serves `P/www` |
| b | `root www;`, `-p P` (no slash) | serves `P/www` | 404 (red) | serves `P/www` |
| c | `location /al/ { alias alt/; }`, `-p P/` | serves `P/alt` | 404 (red) | serves `P/alt` |
| d | `root /abs/www;` (absolute), both `-p` forms | serves `/abs/www` | serves (green) | unchanged |

Falsified by the oracle answering otherwise on any row (then lobo
follows the oracle and this table was wrong), or by row d moving.
Beside it: with no `-p` (the prefix `.`), every printed path stays as
written, so the reel's `would serve: html/files/big.bin` and every
probe without `-p` do not move; `distro-default.probe` (relative
`-p`, `root html`) moves to `tests/config-corpus/distro-default/html/`
and no other probe stanza moves.

### §3 against the measurement (written at the close)

- **F1: falsified on size, held on the rest.** The release binary
  changed (`3330959c…` -> `e8d2ff85…`) but is only **0.22 % smaller**
  (12,472,648 -> 12,444,936 bytes), and its text section **grew
  0.93 %** (1,610,434 -> 1,625,358): cross-module inlining outweighs the
  dedup here, not the other way round. The debug binary is the same
  bytes both ways (`9054863d…`) and two on-builds are byte-identical.
- **F2: held**, with one stale number of mine: trunk's control
  differential was already 10/10 (ws49's row 5), not 9/9. Both ways at
  one tree: corpus 311/311 with the same verdict on every lane-run,
  differential 22/22, proxy 8/8, control 10/10, logdiff 4/4, signal
  21/21, membudget 17/17, resolver 9/9.
- **F3: held on the bar's host.** The runner's two-tree set (run
  37683057126, VALID): on ÷ off 1.004x close, 1.025x keepalive at
  N = 4. kasumi refused both sets (load and nginx's spread); indicative
  0.997x / 1.006x and 0.990x / 1.020x. membudget: every growth figure
  within ±2.3 % (the capped round B 8104 -> 8288 KB), retention 19 / 20
  KB a request both ways.
- **F4: held on every row.** The oracle served `P/www`, `P/alt/` and
  the absolute root under both `-p P/` and `-p P`; trunk's lobo
  answered 404 on 6a-6d and served 6e-6f; the fix serves all six. With
  no `-p` nothing printed moved; `distro-default.probe` moved as
  predicted and no other probe did. **Not predicted:**
  `tests/shell/reload_swap.lu` encoded the bug (`root ws04_reload/A`
  under `-p ws04_reload`, a path relative to the cwd) and went red with
  the fix; its roots are now written under the prefix.

## 4. Evidence index

kasumi paths are under `~/lanes/ws52/`.

| claim | artifact |
|---|---|
| the pin by digest | `dl/digest-check.txt` 24e90317… (wolf `501d6d3f…`, lupin `0ddc4ff3…`), `toolchain-tc-0224.txt` f978b939…; nginx `65595ac2…` (`nginx.sha256` bdddc316…, copied from ws47's tree) |
| binaries both ways, one tree | `builds-base.log` 7d5ea79d… at `07ad3d6` |
| gauntlet GREEN with `WOLF_MIDEND=0` | `g-base.log` e2c8b82b… at `07ad3d6`: exit 0, 297 s; mask SigBlk 0x10000, SigIgn 0x7; 2 SKIP lines, both named (signal's linux-only header, membudget's wolf-lang#191 gate) |
| gauntlet GREEN with the mid-end on | `g-flip.log` b593e1c3… at `e03574a`: exit 0, 351 s, release `e8d2ff85…`; same mask, same 2 SKIP lines |
| the oracle on #55 | `oprobe.log` a95856c1… (nginx 1.30.4 under `-p P/` and `-p P`, conf relative and absolute) |
| #55 red at trunk's code | `g-red.log` d4158f98… at `605e185` (root_prefix `trap(assert)` native and checked, 311/313); `cd-red.log` 8b947a26… (row 6: 6a-6d FAILED, 6e-6f ok, 4 of 16) |
| #55 green, the head | `g-fix.log` eae20c10… at `cc5db03`: GREEN, 377 s, 313/313, control 16/16, dryrun green; mask SigBlk 0x10000 |
| planted break red in CI | run **37682188234** at `59d1891` (root_prefix and reload_swap, both lanes, 309/313) |
| the revert green in CI | run **37683057126**'s sibling PR run **37683050295** at `9acf0d6` |
| the bench | run **37683057126** (VALID, runner); `p-n4.log` 20481546…, `p-n4b.log` e278787c… (kasumi, refused) |
| CI green at the fixes | run **37680730118** at `cc5db03` |

## 5. Done-when

- [ ] Branch `ws52` on origin; PR open against `trunk`, **unmerged**,
  five sections by name, commit shas as bullets, a test checklist.
- [ ] The flip-back as its own commit: `WOLF_MIDEND=0` gone from the
  gauntlet, `lobo-dist` and ci.yml; binaries compared; the gauntlet
  green both ways on kasumi by log path with the mask; the bench
  (membudget, parity delta) before and after.
- [ ] lobo#55 fixed: differential rows against the oracle for a
  relative root, a relative alias, an absolute root unchanged, and
  `-p` with and without a trailing slash; red at trunk by log path,
  green after; a planted break red in CI by run id, reverted.
- [ ] CHANGELOG entries; docs follow the flip.
- [ ] CI green at the head sha (`gh run view`).
- [ ] Worktrees gone; kasumi `target/` dirs pruned (logs kept); no
  orphan pids. Nothing closed by this lane; what to close is listed.
