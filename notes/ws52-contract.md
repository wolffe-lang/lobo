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

## 3. Prediction

Committed next, in its own commit, before the first build.

## 4. Evidence index

Filled in at the close (below and in the PR body).

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
